from .responses import CaseOut, CasePage, DocumentOut, EventOut, HearingOut, SectionOut
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func
from .models import *
from .security import DB, Actor, roles, case_scope, get_case, get_victim, audit
from .schemas import CaseCreate, CaseUpdate, EventInput, HearingInput, HearingUpdate, DocumentInput, SectionInput
from .presenters import case_view, fields

router = APIRouter(tags=['Cases'])


def check_prosecutor(db, prosecutor_id, district_id):
    if prosecutor_id:
        prosecutor = db.get(Prosecutor, prosecutor_id)
        if not prosecutor or prosecutor.district_id != district_id:
            raise HTTPException(422, 'Prosecutor must belong to the case district')


@router.get('/cases', response_model=CasePage)
def list_cases(db: DB, user: Actor, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
               status: str | None = None, district_id: str | None = None):
    stmt = select(Case).where(case_scope(user))
    if status:
        stmt = stmt.where(Case.status == status)
    if district_id:
        stmt = stmt.where(Case.district_id == district_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    audit(db, user, 'LIST', 'cases')
    return {'items': [case_view(db, c) for c in db.scalars(stmt.order_by(Case.created_at.desc(), Case.id).offset(offset).limit(limit))], 'total': total}


@router.get('/legal/overview')
def legal_overview(db: DB, user: Actor):
    roles(user, Role.LEGAL_OFFICER)
    rows = list(db.scalars(select(Case).where(case_scope(user))))
    ids = [c.id for c in rows]
    today = now()
    week = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    hearings = db.scalar(select(func.count()).select_from(Hearing).where(Hearing.case_id.in_(ids), Hearing.scheduled_at >= week, Hearing.scheduled_at < week + timedelta(days=7), Hearing.status != 'CANCELLED'))
    # An explicit MVP operational definition: open and no timeline progress in 30 days.
    delayed = 0
    for c in rows:
        last = db.scalar(select(func.max(CaseEvent.occurred_at)).where(CaseEvent.case_id == c.id)) or c.created_at
        if c.status == 'OPEN' and last.replace(tzinfo=timezone.utc) < today - timedelta(days=30):
            delayed += 1
    return {'total_cases': len(rows), 'hearings_this_week': hearings,
            'pending_investigation': sum(c.investigation_status != 'COMPLETED' for c in rows),
            'delayed_cases': delayed, 'protection_requests': sum(c.protection_status == 'REQUESTED' for c in rows),
            'compensation_pending': sum(c.compensation_status == 'PENDING' for c in rows)}


@router.post('/cases', response_model=CaseOut, status_code=201)
def create_case(payload: CaseCreate, db: DB, user: Actor):
    roles(user, Role.LEGAL_OFFICER)
    # New cases may only be opened for an already permitted victim. Initial intake is provisioned separately.
    victim = get_victim(db, user, payload.victim_id)
    officer = db.scalar(select(LegalOfficer).where(LegalOfficer.user_id == user.id))
    check_prosecutor(db, payload.prosecutor_id, victim.district_id)
    row = Case(**payload.model_dump(exclude={'sections'}), district_id=victim.district_id, legal_officer_id=officer.id)
    db.add(row)
    db.flush()
    for section in payload.sections:
        db.add(CaseSection(case_id=row.id, **section.model_dump()))
    db.add(CaseEvent(case_id=row.id, event_type='CASE_CREATED', stage='REGISTERED',
                     description='Case registered', occurred_at=now(), actor_id=user.id))
    audit(db, user, 'CREATE', 'case', row.id)
    db.flush()
    return case_view(db, row)


@router.get('/cases/{case_id}', response_model=CaseOut)
def detail(case_id: str, db: DB, user: Actor):
    row = get_case(db, user, case_id)
    audit(db, user, 'READ', 'case', row.id)
    return case_view(db, row)


@router.patch('/cases/{case_id}', response_model=CaseOut)
def update_case(case_id: str, payload: CaseUpdate, db: DB, user: Actor):
    row = get_case(db, user, case_id, edit=True)
    values = payload.model_dump(exclude_unset=True)
    check_prosecutor(db, values.get('prosecutor_id'), row.district_id)
    for key, value in values.items():
        setattr(row, key, value)
    audit(db, user, 'UPDATE', 'case', row.id)
    db.flush()
    return case_view(db, row)


@router.get('/cases/{case_id}/timeline', response_model=list[EventOut])
def timeline(case_id: str, db: DB, user: Actor):
    get_case(db, user, case_id)
    audit(db, user, 'READ', 'timeline', case_id)
    return [fields(x, 'id', 'event_type', 'stage', 'description', 'occurred_at') for x in db.scalars(select(CaseEvent).where(CaseEvent.case_id == case_id).order_by(CaseEvent.occurred_at, CaseEvent.created_at, CaseEvent.id))]


@router.post('/cases/{case_id}/timeline', response_model=EventOut, status_code=201)
def add_event(case_id: str, payload: EventInput, db: DB, user: Actor):
    get_case(db, user, case_id, edit=True)
    row = CaseEvent(case_id=case_id, actor_id=user.id, **payload.model_dump())
    db.add(row)
    db.flush()
    audit(db, user, 'CREATE', 'case_event', row.id)
    return fields(row, 'id', 'event_type', 'stage', 'description', 'occurred_at')


@router.post('/cases/{case_id}/sections', response_model=SectionOut, status_code=201)
def add_section(case_id: str, payload: SectionInput, db: DB, user: Actor):
    get_case(db, user, case_id, edit=True)
    row = CaseSection(case_id=case_id, **payload.model_dump())
    db.add(row)
    db.flush()
    audit(db, user, 'CREATE', 'case_section', row.id)
    return fields(row, 'id', 'act', 'section')


@router.get('/hearings', response_model=list[HearingOut])
def hearings(db: DB, user: Actor, case_id: str | None = None, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200)):
    stmt = select(Hearing).where(Hearing.case_id.in_(select(Case.id).where(case_scope(user))))
    if case_id:
        get_case(db, user, case_id)
        stmt = stmt.where(Hearing.case_id == case_id)
    audit(db, user, 'LIST', 'hearings')
    return [fields(x, 'id', 'case_id', 'scheduled_at', 'purpose', 'outcome', 'status') for x in db.scalars(stmt.order_by(Hearing.scheduled_at, Hearing.id).offset(offset).limit(limit))]


@router.post('/cases/{case_id}/hearings', response_model=HearingOut, status_code=201)
def add_hearing(case_id: str, payload: HearingInput, db: DB, user: Actor):
    get_case(db, user, case_id, edit=True)
    row = Hearing(case_id=case_id, **payload.model_dump())
    db.add(row)
    db.flush()
    audit(db, user, 'CREATE', 'hearing', row.id)
    return fields(row, 'id', 'case_id', 'scheduled_at', 'purpose', 'status')


@router.patch('/hearings/{hearing_id}', response_model=HearingOut)
def update_hearing(hearing_id: str, payload: HearingUpdate, db: DB, user: Actor):
    row = db.scalar(select(Hearing).where(Hearing.id == hearing_id, Hearing.case_id.in_(select(Case.id).where(case_scope(user, edit=True)))))
    if not row:
        raise HTTPException(404, 'Hearing not found')
    row.status, row.outcome = payload.status, payload.outcome
    audit(db, user, 'UPDATE', 'hearing', row.id)
    return fields(row, 'id', 'case_id', 'scheduled_at', 'purpose', 'outcome', 'status')


@router.get('/cases/{case_id}/documents', response_model=list[DocumentOut])
def documents(case_id: str, db: DB, user: Actor):
    get_case(db, user, case_id)
    audit(db, user, 'READ', 'case_documents', case_id)
    return [fields(x, 'id', 'name', 'document_type', 'created_at') for x in db.scalars(select(CaseDocument).where(CaseDocument.case_id == case_id))]


@router.post('/cases/{case_id}/documents', response_model=DocumentOut, status_code=201)
def add_document(case_id: str, payload: DocumentInput, db: DB, user: Actor):
    get_case(db, user, case_id, edit=True)
    row = CaseDocument(case_id=case_id, uploaded_by=user.id, **payload.model_dump())
    db.add(row)
    db.flush()
    audit(db, user, 'CREATE', 'case_document', row.id)
    return fields(row, 'id', 'name', 'document_type', 'created_at')


@router.get('/prosecutors')
def prosecutors(db: DB, user: Actor):
    roles(user, Role.LEGAL_OFFICER)
    districts = select(Case.district_id).where(case_scope(user))
    return [fields(p, 'id', 'name', 'district_id') for p in db.scalars(select(Prosecutor).where(Prosecutor.district_id.in_(districts)))]
