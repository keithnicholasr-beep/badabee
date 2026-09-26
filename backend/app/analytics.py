from .responses import AnalyticsOut
from collections import Counter, defaultdict
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from .models import *
from .security import DB, Actor, roles, audit

router = APIRouter(prefix='/analytics', tags=['Aggregated analytics'])


def aggregate(db, user, level, district_id=None, state_id=None):
    roles(user, Role.DISTRICT_ADMIN, Role.STATE_ADMIN, Role.NATIONAL_ADMIN)
    if level == 'national' and user.role != Role.NATIONAL_ADMIN:
        raise HTTPException(403, 'National analytics require national access')
    if level == 'state' and user.role == Role.DISTRICT_ADMIN:
        raise HTTPException(403, 'State analytics require state access')
    if user.role == Role.DISTRICT_ADMIN:
        if district_id and district_id != user.district_id:
            raise HTTPException(403, 'Outside your jurisdiction')
        district_id = user.district_id
    if user.role == Role.STATE_ADMIN:
        if state_id and state_id != user.state_id:
            raise HTTPException(403, 'Outside your jurisdiction')
        state_id = user.state_id
    if level == 'district' and not district_id:
        raise HTTPException(422, 'district_id is required')
    if level == 'state' and not state_id:
        raise HTTPException(422, 'state_id is required')
    if state_id and not db.get(State, state_id):
        raise HTTPException(404, 'State not found')
    if district_id:
        district = db.get(District, district_id)
        if not district or (state_id and district.state_id != state_id):
            raise HTTPException(403, 'Outside the selected jurisdiction')
    districts = select(District.id)
    if state_id:
        districts = districts.where(District.state_id == state_id)
    if district_id:
        districts = districts.where(District.id == district_id)
    cases = list(db.scalars(select(Case).where(Case.district_id.in_(districts))))
    victims = select(Victim.id).where(Victim.district_id.in_(districts))
    predictions = list(db.scalars(select(DistressPrediction).where(DistressPrediction.victim_id.in_(victims)).order_by(DistressPrediction.observed_at.desc(), DistressPrediction.created_at.desc(), DistressPrediction.id.desc())))
    latest, months = {}, defaultdict(list)
    for p in predictions:
        latest.setdefault(p.victim_id, p)
        months[p.observed_at.strftime('%Y-%m')].append(p.score)
    events = db.scalars(select(CaseEvent).where(CaseEvent.case_id.in_([c.id for c in cases])).order_by(CaseEvent.occurred_at.desc(), CaseEvent.created_at.desc(), CaseEvent.id.desc()))
    stages = {}
    for event in events:
        stages.setdefault(event.case_id, event.stage)
    critical = list(db.scalars(select(Alert).where(Alert.victim_id.in_(victims), Alert.severity == 'CRITICAL', Alert.acknowledged_at.is_(None))))
    pending = list(db.scalars(select(Followup).where(Followup.victim_id.in_(victims), Followup.status == 'PENDING')))
    ages = [(now() - c.created_at.replace(tzinfo=timezone.utc)).days for c in cases]
    audit(db, user, 'AGGREGATE', 'analytics', level)
    return {'jurisdiction': {'level': level, 'district_id': district_id, 'state_id': state_id},
            'cases_monitored': len(cases),
            'high_risk_cases': sum(c.victim_id in latest and latest[c.victim_id].level in ('HIGH', 'CRITICAL') for c in cases),
            'critical_alerts': len(critical), 'followups_pending': len(pending),
            'case_categories': dict(Counter(c.case_type for c in cases)),
            'case_stages': dict(Counter(stages.get(c.id, 'REGISTERED') for c in cases)),
            'average_case_age_days': round(sum(ages) / len(ages), 1) if ages else 0,
            'compensation_status': dict(Counter(c.compensation_status for c in cases)),
            'rehabilitation_status': dict(Counter(c.rehabilitation_status for c in cases)),
            'distress_trends': [{'month': month, 'average_score': round(sum(values) / len(values), 1), 'observations': len(values)} for month, values in sorted(months.items())]}


@router.get('/district', response_model=AnalyticsOut)
def district(db: DB, user: Actor, district_id: str | None = None):
    return aggregate(db, user, 'district', district_id=district_id)


@router.get('/state', response_model=AnalyticsOut)
def state(db: DB, user: Actor, state_id: str | None = None, district_id: str | None = None):
    return aggregate(db, user, 'state', district_id=district_id, state_id=state_id)


@router.get('/national', response_model=AnalyticsOut)
def national(db: DB, user: Actor, state_id: str | None = None, district_id: str | None = None):
    return aggregate(db, user, 'national', district_id=district_id, state_id=state_id)
