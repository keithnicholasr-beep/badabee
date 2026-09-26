from .responses import AcknowledgementOut, AlertOut, CaseOut, FollowupOut, PredictionOut, VictimOut
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, Header, Query
from sqlalchemy import select
from .models import *
from .security import DB, Actor, get_victim, victim_scope, case_scope, roles, audit, ingest_auth
from .schemas import FollowupInput, FollowupUpdate, PredictionInput
from .presenters import victim_view, case_view, fields, prediction_view
from .notifications import publish_alert

router = APIRouter(tags=['Support contracts'])


@router.get('/victims/{victim_id}', response_model=VictimOut)
def victim(victim_id: str, db: DB, user: Actor):
    row = get_victim(db, user, victim_id)
    audit(db, user, 'READ', 'victim', row.id)
    return victim_view(db, row)


@router.get('/victims/{victim_id}/case', response_model=list[CaseOut])
def victim_cases(victim_id: str, db: DB, user: Actor):
    get_victim(db, user, victim_id)
    audit(db, user, 'READ', 'victim_cases', victim_id)
    return [case_view(db, x) for x in db.scalars(select(Case).where(Case.victim_id == victim_id, case_scope(user)))]


@router.get('/victims/{victim_id}/followups', response_model=list[FollowupOut])
def victim_followups(victim_id: str, db: DB, user: Actor):
    get_victim(db, user, victim_id, clinical=True)
    audit(db, user, 'READ', 'followups', victim_id)
    return [fields(x, 'id', 'victim_id', 'counsellor_id', 'due_at', 'status') for x in db.scalars(select(Followup).where(Followup.victim_id == victim_id).order_by(Followup.due_at.desc()).limit(200))]


@router.get('/victims/{victim_id}/distress', response_model=list[PredictionOut])
def victim_distress(victim_id: str, db: DB, user: Actor):
    get_victim(db, user, victim_id, clinical=True)
    # Private explanatory factors are restricted to the victim and assigned counsellor.
    roles(user, Role.VICTIM, Role.COUNSELLOR)
    audit(db, user, 'READ', 'distress', victim_id)
    return [prediction_view(x) for x in db.scalars(select(DistressPrediction).where(DistressPrediction.victim_id == victim_id).order_by(DistressPrediction.observed_at.desc()).limit(200))]


@router.get('/counsellors/{counsellor_id}/victims', response_model=list[VictimOut])
def assigned(counsellor_id: str, db: DB, user: Actor):
    roles(user, Role.COUNSELLOR)
    profile = db.scalar(select(Counsellor).where(Counsellor.id == counsellor_id, Counsellor.user_id == user.id))
    if profile is None:
        raise HTTPException(404, 'Counsellor not found')
    audit(db, user, 'LIST', 'assigned_victims', counsellor_id)
    return [victim_view(db, x) for x in db.scalars(select(Victim).where(victim_scope(user)))]


@router.post('/followups', response_model=FollowupOut, status_code=201)
def create_followup(payload: FollowupInput, db: DB, user: Actor):
    roles(user, Role.COUNSELLOR)
    get_victim(db, user, payload.victim_id, clinical=True)
    profile = db.scalar(select(Counsellor).where(Counsellor.user_id == user.id))
    row = Followup(victim_id=payload.victim_id, counsellor_id=profile.id, due_at=payload.due_at)
    db.add(row)
    db.flush()
    if payload.note:
        db.add(CounsellingNote(followup_id=row.id, author_id=user.id, note=payload.note))
    audit(db, user, 'CREATE', 'followup', row.id)
    return fields(row, 'id', 'victim_id', 'counsellor_id', 'due_at', 'status')


@router.patch('/followups/{followup_id}', response_model=FollowupOut)
def update_followup(followup_id: str, payload: FollowupUpdate, db: DB, user: Actor):
    roles(user, Role.COUNSELLOR)
    profile = select(Counsellor.id).where(Counsellor.user_id == user.id)
    row = db.scalar(select(Followup).where(Followup.id == followup_id, Followup.counsellor_id.in_(profile),
                    Followup.victim_id.in_(select(Victim.id).where(victim_scope(user, clinical=True)))))
    if row is None:
        raise HTTPException(404, 'Followup not found')
    row.status = payload.status
    audit(db, user, 'UPDATE', 'followup', row.id)
    return fields(row, 'id', 'victim_id', 'counsellor_id', 'due_at', 'status')


@router.get('/followups', response_model=list[FollowupOut])
def followups(db: DB, user: Actor, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200)):
    ids = select(Victim.id).where(victim_scope(user, clinical=True))
    audit(db, user, 'LIST', 'followups')
    return [fields(x, 'id', 'victim_id', 'counsellor_id', 'due_at', 'status') for x in db.scalars(select(Followup).where(Followup.victim_id.in_(ids)).order_by(Followup.due_at, Followup.id).offset(offset).limit(limit))]


@router.get('/followups/{followup_id}/note')
def note(followup_id: str, db: DB, user: Actor):
    roles(user, Role.COUNSELLOR)
    followup = db.scalar(select(Followup).where(Followup.id == followup_id, Followup.victim_id.in_(select(Victim.id).where(victim_scope(user, clinical=True)))))
    if followup is None:
        raise HTTPException(404, 'Followup not found')
    row = db.scalar(select(CounsellingNote).where(CounsellingNote.followup_id == followup_id, CounsellingNote.author_id == user.id))
    if row is None:
        raise HTTPException(404, 'Note not found')
    audit(db, user, 'READ', 'counselling_note', row.id)
    return fields(row, 'id', 'note', 'created_at')


@router.get('/alerts', response_model=list[AlertOut])
def alerts(db: DB, user: Actor, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200)):
    ids = select(Victim.id).where(victim_scope(user, clinical=True))
    audit(db, user, 'LIST', 'alerts')
    return [fields(x, 'id', 'victim_id', 'severity', 'message', 'acknowledged_at', 'created_at') for x in db.scalars(select(Alert).where(Alert.victim_id.in_(ids)).order_by(Alert.created_at.desc(), Alert.id).offset(offset).limit(limit))]


@router.post('/alerts/{alert_id}/acknowledge', response_model=AcknowledgementOut)
def acknowledge(alert_id: str, db: DB, user: Actor):
    roles(user, Role.COUNSELLOR, Role.DISTRICT_ADMIN, Role.STATE_ADMIN)
    row = db.scalar(select(Alert).where(Alert.id == alert_id, Alert.victim_id.in_(select(Victim.id).where(victim_scope(user, clinical=True)))).with_for_update())
    if row is None:
        raise HTTPException(404, 'Alert not found')
    if row.acknowledged_at is None:
        row.acknowledged_by, row.acknowledged_at = user.id, now()
        audit(db, user, 'ACKNOWLEDGE', 'alert', row.id)
    return fields(row, 'id', 'acknowledged_at')


@router.post('/integrations/distress', response_model=PredictionOut, dependencies=[Depends(ingest_auth)], status_code=201)
def ingest(payload: PredictionInput, db: DB, idempotency_key: Annotated[str, Header(min_length=1, max_length=120)]):
    existing = db.scalar(select(DistressPrediction).where(DistressPrediction.external_id == idempotency_key))
    if existing:
        supplied = payload.model_dump(exclude={'observed_at'})
        if any(getattr(existing, key) != value for key, value in supplied.items()) or (
            payload.observed_at and existing.observed_at.replace(tzinfo=timezone.utc) != payload.observed_at):
            raise HTTPException(409, 'Idempotency key already used for a different payload')
        return prediction_view(existing)
    if not db.get(Victim, payload.victim_id):
        raise HTTPException(404, 'Victim not found')
    row = DistressPrediction(**payload.model_dump(exclude={'observed_at'}), observed_at=payload.observed_at or now(), external_id=idempotency_key)
    db.add(row)
    db.flush()
    publish_alert(db, row)
    audit(db, None, 'INGEST_DISTRESS', 'distress_prediction', row.id)
    return prediction_view(row)


@router.get('/notifications')
def notifications(db: DB, user: Actor):
    # Re-check assignments when reading previously generated notifications.
    permitted = select(Alert.id).where(Alert.victim_id.in_(select(Victim.id).where(victim_scope(user, clinical=True))))
    stmt = select(Notification).where(Notification.user_id == user.id, Notification.alert_id.in_(permitted),
             Notification.id.in_(select(NotificationOutbox.notification_id).where(NotificationOutbox.status == 'DELIVERED')))
    return [fields(x, 'id', 'title', 'alert_id', 'read_at', 'created_at') for x in db.scalars(stmt.order_by(Notification.created_at.desc()).limit(100))]


@router.post('/notifications/{notification_id}/read')
def read_notification(notification_id: str, db: DB, user: Actor):
    row = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id))
    if row is None:
        raise HTTPException(404, 'Notification not found')
    if row.alert_id:
        alert = db.get(Alert, row.alert_id)
        get_victim(db, user, alert.victim_id, clinical=True)
    row.read_at = row.read_at or now()
    audit(db, user, 'READ', 'notification', row.id)
    return fields(row, 'id', 'read_at')
