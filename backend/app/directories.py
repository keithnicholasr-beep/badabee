from .responses import EligibleSchemeOut, LocationOut, NGOMatchOut, NGOOut, SchemeOut
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import select, or_
from .models import *
from .security import DB, Actor, get_victim, audit, district_scope
from .presenters import fields, location

def directory_access(user: Actor):
    if user.role == Role.LAW_ENFORCEMENT:
        raise HTTPException(403, 'Law enforcement access is limited to complaints and FIRs')


router = APIRouter(tags=['Directories'], dependencies=[Depends(directory_access)])


def ngo_view(db, row):
    return {**fields(row, 'id', 'name', 'latitude', 'longitude', 'phone', 'availability'),
            **location(db, row.district_id),
            'services': list(db.scalars(select(NGOService.service).where(NGOService.ngo_id == row.id))),
            'languages': list(db.scalars(select(NGOLanguage.language).where(NGOLanguage.ngo_id == row.id)))}


def match_score(ngo, victim, required_service, language, state_id):
    """Replaceable, deterministic ranking. No ML dependency or clinical inference."""
    if required_service and required_service not in ngo['services']:
        return None
    if ngo['availability'] == 'UNAVAILABLE':
        return None
    reasons, score = [], 0
    if ngo['district_id'] == victim.district_id:
        score += 60
        reasons.append('Same district')
    elif ngo['state_id'] == state_id:
        score += 25
        reasons.append('Same state')
    if language in ngo['languages']:
        score += 25
        reasons.append('Preferred language available')
    if required_service:
        score += 15
        reasons.append('Requested service available')
    return score, reasons


@router.get('/ngos', response_model=list[NGOOut])
def ngos(db: DB, user: Actor, district_id: str | None = None, state_id: str | None = None,
         service: str | None = None, language: str | None = None,
         offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200)):
    stmt = select(NGO)
    if district_id:
        stmt = stmt.where(NGO.district_id == district_id)
    if state_id:
        stmt = stmt.where(NGO.district_id.in_(select(District.id).where(District.state_id == state_id)))
    if service:
        stmt = stmt.where(NGO.id.in_(select(NGOService.ngo_id).where(NGOService.service == service)))
    if language:
        stmt = stmt.where(NGO.id.in_(select(NGOLanguage.ngo_id).where(NGOLanguage.language == language)))
    return [ngo_view(db, x) for x in db.scalars(stmt.order_by(NGO.name, NGO.id).offset(offset).limit(limit))]


@router.get('/ngos/match', response_model=list[NGOMatchOut])
def match(victim_id: str, db: DB, user: Actor, required_service: str | None = None, language: str | None = None):
    victim = get_victim(db, user, victim_id)
    state_id = db.get(District, victim.district_id).state_id
    result = []
    for ngo in db.scalars(select(NGO)):
        data = ngo_view(db, ngo)
        ranking = match_score(data, victim, required_service, language or victim.language, state_id)
        if ranking is not None:
            score, reasons = ranking
            result.append({**data, 'match_score': score, 'match_reasons': reasons})
    audit(db, user, 'MATCH', 'ngo', victim_id)
    return sorted(result, key=lambda x: (-x['match_score'], x['name']))[:20]


@router.get('/ngos/{ngo_id}', response_model=NGOOut)
def ngo(ngo_id: str, db: DB, user: Actor):
    row = db.get(NGO, ngo_id)
    if row is None:
        raise HTTPException(404, 'NGO not found')
    return ngo_view(db, row)


def scheme_view(db, row):
    return {**fields(row, 'id', 'name', 'authority', 'description', 'benefits', 'application_process', 'source_url', 'state_id', 'is_demo'),
            'applicability': db.get(State, row.state_id).name if row.state_id else 'National',
            'eligibility_criteria': [fields(x, 'field', 'operator', 'value') for x in db.scalars(select(SchemeEligibility).where(SchemeEligibility.scheme_id == row.id))],
            'required_documents': list(db.scalars(select(SchemeDocument.name).where(SchemeDocument.scheme_id == row.id)))}


def evaluate_rule(victim, rule):
    if rule['field'] not in ('age', 'annual_income', 'support_category'):
        return None
    value = getattr(victim, rule['field'])
    if value is None:
        return None
    expected, operator = rule['value'], rule['operator']
    try:
        if operator == 'eq':
            return value == expected
        if operator == 'lte':
            return value <= expected
        if operator == 'gte':
            return value >= expected
        if operator == 'in' and isinstance(expected, list):
            return value in expected
    except TypeError:
        return None
    return None


@router.get('/schemes', response_model=list[SchemeOut])
def schemes(db: DB, user: Actor, state_id: str | None = None):
    stmt = select(GovernmentScheme)
    if state_id:
        stmt = stmt.where(or_(GovernmentScheme.state_id.is_(None), GovernmentScheme.state_id == state_id))
    return [scheme_view(db, x) for x in db.scalars(stmt.order_by(GovernmentScheme.name))]


@router.get('/victims/{victim_id}/eligible-schemes', response_model=list[EligibleSchemeOut])
def eligible(victim_id: str, db: DB, user: Actor):
    victim = get_victim(db, user, victim_id)
    state_id = db.get(District, victim.district_id).state_id
    result = []
    for row in db.scalars(select(GovernmentScheme).where(or_(GovernmentScheme.state_id.is_(None), GovernmentScheme.state_id == state_id))):
        data = scheme_view(db, row)
        rules = data['eligibility_criteria']
        checks = [evaluate_rule(victim, rule) for rule in rules]
        status = 'NOT_ELIGIBLE' if False in checks else 'NEEDS_REVIEW' if None in checks or not checks else 'POTENTIALLY_ELIGIBLE'
        # Do not disclose income/category values in a legal-facing eligibility response.
        result.append({**data, 'eligibility': status, 'explanation':
                       [{'field': rule['field'], 'result': 'UNKNOWN' if check is None else 'MATCH' if check else 'NO_MATCH'} for rule, check in zip(rules, checks)]})
    audit(db, user, 'EVALUATE', 'scheme_eligibility', victim_id)
    return result


@router.get('/jurisdictions', response_model=list[LocationOut])
def jurisdictions(db: DB, user: Actor):
    stmt = select(District)
    if user.role in (Role.DISTRICT_ADMIN, Role.STATE_ADMIN):
        stmt = stmt.where(district_scope(user, District.id))
    return [location(db, x.id) for x in db.scalars(stmt.order_by(District.name))]
