"""Victim and counsellor workflows; all queries enforce existing record scopes."""
from datetime import timedelta
from uuid import uuid4
from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import Field
from sqlalchemy import select
from .models import (User, Victim, Counsellor, CounsellorAssignment, Followup, CounsellingNote,
    DistressPrediction, WellbeingCheckin, SupportAction, SupportChatTurn, Alert, NGO,
    Role, Case, now)
from .schemas import Input
from .security import DB, Actor, roles, get_victim, victim_scope, case_scope, audit
from .presenters import victim_view, case_view, prediction_view, fields
from .notifications import publish_alert, deliver_in_app, notify_counsellors
from .directories import eligible
from .ai.distress import Features, predict_distress
from .ai.chat import provider as chat_provider

router = APIRouter(prefix='/portal', tags=['Support portals'])


class CheckinInput(Input):
    request_id: str = Field(min_length=8, max_length=80)
    mood: int = Field(ge=1, le=5)
    stress: int = Field(ge=1, le=5)
    sleep: int = Field(ge=1, le=5)
    feels_unsafe: bool = False
    text: str = Field(default='', max_length=4000)
    language: Literal['en', 'hi', 'kn'] = 'en'


class ActionInput(Input):
    kind: Literal['EMERGENCY', 'SUPPORT', 'ESCALATION', 'REFERRAL', 'INTERVENTION', 'REVIEW', 'ALERT']
    note: str = Field(min_length=1, max_length=4000)
    ngo_id: str | None = None


class NoteInput(Input):
    note: str = Field(min_length=1, max_length=10000)


class ChatInput(Input):
    request_id: str = Field(min_length=8, max_length=80)
    message: str = Field(min_length=1, max_length=2000)
    language: Literal['en', 'hi', 'kn'] = 'en'
    intent: Literal['hearing', 'counsellor', 'schemes', 'stage', 'safety'] | None = None


def support_role(user):
    roles(user, Role.VICTIM, Role.COUNSELLOR)


def own_victim(db, user):
    roles(user, Role.VICTIM)
    row = db.scalar(select(Victim).where(Victim.user_id == user.id))
    if row is None: raise HTTPException(404, 'Victim profile not configured')
    return row


def counsellors(db, victim_id):
    rows = db.scalars(select(Counsellor).join(CounsellorAssignment, CounsellorAssignment.counsellor_id == Counsellor.id)
        .where(CounsellorAssignment.victim_id == victim_id, CounsellorAssignment.active.is_(True)))
    return [{'id': x.id, 'name': db.get(User, x.user_id).name, 'specialization': x.specialization} for x in rows]


def latest_prediction(db, victim_id):
    return db.scalar(select(DistressPrediction).where(DistressPrediction.victim_id == victim_id)
        .order_by(DistressPrediction.observed_at.desc(), DistressPrediction.created_at.desc()))


def wellbeing(prediction):
    return 'EXTRA_SUPPORT' if prediction and prediction.level in ('HIGH', 'CRITICAL') else 'CHECK_IN' if not prediction else 'RECORDED'


def action_view(db, row):
    return {**fields(row, 'id', 'victim_id', 'kind', 'note', 'status', 'ngo_id', 'created_at', 'resolved_at'),
            'author': db.get(User, row.actor_id).name,
            'ngo': db.get(NGO, row.ngo_id).name if row.ngo_id else None}


@router.get('/me')
def me(db: DB, user: Actor):
    support_role(user)
    profile_class = Victim if user.role == Role.VICTIM else Counsellor
    row = db.scalar(select(profile_class).where(profile_class.user_id == user.id))
    if row is None: raise HTTPException(404, 'Support profile not configured')
    return {'user_id': user.id, 'profile_id': row.id, 'role': user.role, 'name': user.name}


@router.get('/victims/{victim_id}')
def detail(victim_id: str, db: DB, user: Actor):
    support_role(user)
    victim = get_victim(db, user, victim_id, clinical=True)
    cases = [case_view(db, x) for x in db.scalars(select(Case).where(Case.victim_id == victim_id, case_scope(user)))]
    followups = list(db.scalars(select(Followup).where(Followup.victim_id == victim_id).order_by(Followup.due_at.desc()).limit(200)))
    predictions = list(db.scalars(select(DistressPrediction).where(DistressPrediction.victim_id == victim_id).order_by(DistressPrediction.observed_at.desc()).limit(200)))
    last_checkin = db.scalar(select(WellbeingCheckin).where(WellbeingCheckin.victim_id == victim_id).order_by(WellbeingCheckin.created_at.desc()))
    actions_query = select(SupportAction).where(SupportAction.victim_id == victim_id)
    if user.role == Role.VICTIM:
        actions_query = actions_query.where(SupportAction.actor_id == user.id)
    actions = [action_view(db, a) for a in db.scalars(actions_query.order_by(SupportAction.created_at.desc()).limit(100))]
    notes = []
    if user.role == Role.COUNSELLOR:
        notes = [fields(n, 'id', 'followup_id', 'note', 'created_at') for n in db.scalars(select(CounsellingNote)
            .join(Followup, CounsellingNote.followup_id == Followup.id)
            .where(Followup.victim_id == victim_id, CounsellingNote.author_id == user.id).order_by(CounsellingNote.created_at.desc()).limit(100))]
    audit(db, user, 'READ', 'support_profile', victim_id)
    return {'profile': victim_view(db, victim), 'cases': cases, 'counsellors': counsellors(db, victim_id),
        'followups': [fields(f, 'id', 'victim_id', 'counsellor_id', 'due_at', 'status', 'completed_at') for f in followups],
        'predictions': [prediction_view(p) for p in predictions] if user.role == Role.COUNSELLOR else [],
        'wellbeing': wellbeing(predictions[0] if predictions else None), 'notes': notes, 'actions': actions,
        'last_checkin': last_checkin.created_at if last_checkin else None,
        'next_checkin': last_checkin.created_at + timedelta(days=7) if last_checkin else now()}


@router.get('/caseload')
def caseload(db: DB, user: Actor):
    roles(user, Role.COUNSELLOR)
    rows = []
    for victim in db.scalars(select(Victim).where(victim_scope(user))):
        prediction = latest_prediction(db, victim.id)
        follows = list(db.scalars(select(Followup).where(Followup.victim_id == victim.id)))
        pending = [f for f in follows if f.status == 'PENDING']
        cases = [case_view(db, x) for x in db.scalars(select(Case).where(Case.victim_id == victim.id, case_scope(user)))]
        actions = list(db.scalars(select(SupportAction).where(SupportAction.victim_id == victim.id, SupportAction.status == 'OPEN')))
        rows.append({**victim_view(db, victim), 'risk': prediction_view(prediction) if prediction else None,
            'last_contact': max((f.completed_at for f in follows if f.completed_at), default=None),
            'next_followup': min((f.due_at for f in pending), default=None),
            'due_today': sum(f.due_at.date() == now().date() for f in pending),
            'missed': sum(f.status == 'MISSED' or (f.status == 'PENDING' and f.due_at < now()) for f in follows),
            'escalated': any(a.kind in ('ESCALATION', 'EMERGENCY') for a in actions),
            'stage': ', '.join(dict.fromkeys(c['stage'] for c in cases)) or 'No case recorded'})
    audit(db, user, 'LIST', 'caseload')
    return rows


@router.post('/checkins', status_code=201)
def checkin(payload: CheckinInput, db: DB, user: Actor):
    victim = own_victim(db, user)
    old = db.scalar(select(WellbeingCheckin).where(WellbeingCheckin.victim_id == victim.id, WellbeingCheckin.request_id == payload.request_id))
    if old:
        if any(getattr(old, k) != v for k, v in payload.model_dump().items()):
            raise HTTPException(409, 'Request ID already used for a different check-in')
        return {'id': old.id, 'wellbeing': wellbeing(db.get(DistressPrediction, old.prediction_id)), 'created_at': old.created_at}
    follows = db.scalars(select(Followup).where(Followup.victim_id == victim.id, Followup.due_at >= now() - timedelta(days=30)))
    missed = sum(f.status == 'MISSED' or (f.status == 'PENDING' and f.due_at < now()) for f in follows)
    cases = [case_view(db, c) for c in db.scalars(select(Case).where(Case.victim_id == victim.id))]
    previous = latest_prediction(db, victim.id)
    features = Features(payload.mood, payload.stress, payload.sleep, payload.feels_unsafe, payload.text,
        missed, any(c['next_hearing'] and c['next_hearing'] <= now() + timedelta(days=7) for c in cases), previous.score if previous else None)
    prediction = DistressPrediction(victim_id=victim.id, external_id=f'checkin:{uuid4()}',
        observed_at=now(), **predict_distress(features))
    db.add(prediction)
    db.flush()
    row = WellbeingCheckin(victim_id=victim.id, prediction_id=prediction.id, **payload.model_dump())
    db.add(row)
    publish_alert(db, prediction)
    db.flush()
    deliver_in_app(db)
    audit(db, user, 'CREATE', 'wellbeing_checkin', row.id)
    return {'id': row.id, 'wellbeing': wellbeing(prediction), 'created_at': row.created_at}


@router.post('/victims/{victim_id}/actions', status_code=201)
def create_action(victim_id: str, payload: ActionInput, db: DB, user: Actor):
    support_role(user)
    get_victim(db, user, victim_id, clinical=True)
    if user.role == Role.VICTIM and payload.kind not in ('EMERGENCY', 'SUPPORT'):
        raise HTTPException(403, 'Only counsellors can perform this action')
    if payload.kind == 'REFERRAL' and not payload.ngo_id:
        raise HTTPException(422, 'Choose an NGO for the referral')
    if payload.ngo_id and (payload.kind != 'REFERRAL' or not db.get(NGO, payload.ngo_id)):
        raise HTTPException(422, 'Invalid referral organization')
    # A repeated emergency button press returns the active ticket, not duplicate alerts.
    if payload.kind in ('EMERGENCY', 'SUPPORT'):
        existing = db.scalar(select(SupportAction).where(SupportAction.victim_id == victim_id,
            SupportAction.actor_id == user.id, SupportAction.kind == payload.kind, SupportAction.status == 'OPEN'))
        if existing: return action_view(db, existing)
    row = SupportAction(victim_id=victim_id, actor_id=user.id, **payload.model_dump(),
        status='COMPLETED' if payload.kind == 'REVIEW' else 'OPEN')
    db.add(row)
    if payload.kind in ('EMERGENCY', 'ESCALATION', 'ALERT', 'SUPPORT'):
        alert = Alert(victim_id=victim_id, severity='CRITICAL' if payload.kind == 'EMERGENCY' else 'HIGH',
            message='Human support request: ' + payload.kind.lower())
        db.add(alert)
        db.flush()
        notify_counsellors(db, alert)
        db.flush()
        deliver_in_app(db)
    db.flush()
    audit(db, user, 'CREATE', 'support_action', row.id)
    return action_view(db, row)


@router.post('/actions/{action_id}/resolve')
def resolve(action_id: str, db: DB, user: Actor):
    roles(user, Role.COUNSELLOR)
    row = db.scalar(select(SupportAction).where(SupportAction.id == action_id,
        SupportAction.victim_id.in_(select(Victim.id).where(victim_scope(user)))))
    if row is None: raise HTTPException(404, 'Action not found')
    row.status, row.resolved_by, row.resolved_at = 'COMPLETED', user.id, row.resolved_at or now()
    audit(db, user, 'RESOLVE', 'support_action', row.id)
    return action_view(db, row)


@router.post('/followups/{followup_id}/note')
def save_note(followup_id: str, payload: NoteInput, db: DB, user: Actor):
    roles(user, Role.COUNSELLOR)
    profile = db.scalar(select(Counsellor).where(Counsellor.user_id == user.id))
    followup = db.scalar(select(Followup).where(Followup.id == followup_id, Followup.counsellor_id == profile.id))
    if followup is None: raise HTTPException(404, 'Follow-up not found')
    get_victim(db, user, followup.victim_id, clinical=True)
    note = db.scalar(select(CounsellingNote).where(CounsellingNote.followup_id == followup_id, CounsellingNote.author_id == user.id))
    if note: note.note = payload.note
    else:
        note = CounsellingNote(followup_id=followup_id, author_id=user.id, note=payload.note)
        db.add(note)
    db.flush()
    audit(db, user, 'WRITE', 'counselling_note', note.id)
    return fields(note, 'id', 'note', 'created_at')


@router.get('/chat')
def chat_history(db: DB, user: Actor):
    victim = own_victim(db, user)
    rows = list(db.scalars(select(SupportChatTurn).where(SupportChatTurn.victim_id == victim.id).order_by(SupportChatTurn.created_at.desc()).limit(50)))
    audit(db, user, 'READ', 'support_chat', victim.id)
    return [fields(x, 'id', 'message', 'reply', 'language', 'intent', 'created_at') for x in reversed(rows)]


@router.post('/chat', status_code=201)
def chat(payload: ChatInput, db: DB, user: Actor):
    victim = own_victim(db, user)
    old = db.scalar(select(SupportChatTurn).where(SupportChatTurn.victim_id == victim.id, SupportChatTurn.request_id == payload.request_id))
    if old:
        if old.message != payload.message or old.language != payload.language:
            raise HTTPException(409, 'Request ID already used')
        return fields(old, 'id', 'message', 'reply', 'language', 'intent', 'created_at')
    cases = [case_view(db, c) for c in db.scalars(select(Case).where(Case.victim_id == victim.id))]
    hearing = min((c['next_hearing'] for c in cases if c['next_hearing']), default=None)
    context = {'hearing': hearing.strftime('%d %b %Y, %H:%M') if hearing else None,
        'counsellors': [c['name'] for c in counsellors(db, victim.id)],
        'stages': [c['case_id'] + ': ' + c['stage'] for c in cases], 'schemes': eligible(victim.id, db, user)}
    intent, reply = chat_provider.respond(payload.message, payload.language, context, payload.intent)
    row = SupportChatTurn(victim_id=victim.id, request_id=payload.request_id,
        message=payload.message, language=payload.language, reply=reply, intent=intent)
    db.add(row)
    db.flush()
    audit(db, user, 'CREATE', 'support_chat', row.id)
    return fields(row, 'id', 'message', 'reply', 'language', 'intent', 'created_at')
