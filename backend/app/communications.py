"""Assignment-scoped victim and interdepartmental one-to-one conversations."""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, or_, and_, func
from .models import (User, Role, Victim, District, Counsellor, CounsellorAssignment,
                     LegalOfficer, Case, CasePermission, LawEnforcementOfficer, Complaint,
                     ChatMessage, UserSettings, Notification, NotificationOutbox, now)
from .security import DB, Actor, roles, victim_scope, audit

router = APIRouter(prefix='/communications', tags=['Support team communication'])
STAFF_ROLES = (Role.COUNSELLOR, Role.LEGAL_OFFICER, Role.LAW_ENFORCEMENT)
ALLOWED_ROLES = (Role.VICTIM, *STAFF_ROLES)


class ContactOut(BaseModel):
    id: str
    name: str
    role: Role
    email: str
    phone: str | None


class ClientOut(BaseModel):
    id: str
    user_id: str
    name: str
    district: str
    language: str
    photo: str | None
    contacts: list[ContactOut]


class ClientPage(BaseModel):
    items: list[ClientOut]
    total: int


class MessageInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    body: str = Field(min_length=1, max_length=4000)


class MessageOut(BaseModel):
    id: str
    body: str
    sender_name: str
    mine: bool
    created_at: datetime


class ConversationOut(BaseModel):
    victim_id: str
    victim_name: str
    recipient_name: str
    recipient_role: Role
    messages: list[MessageOut]


def client_scope(user):
    if user.role == Role.LAW_ENFORCEMENT:
        return Victim.id.in_(select(Complaint.victim_id).where(
            Complaint.district_id == user.district_id,
            Complaint.officer_id.in_(select(LawEnforcementOfficer.id).where(LawEnforcementOfficer.user_id == user.id))))
    return victim_scope(user)


def get_client(db, user, victim_id):
    roles(user, *ALLOWED_ROLES)
    row = db.scalar(select(Victim).join(User, User.id == Victim.user_id).where(
        Victim.id == victim_id, client_scope(user), User.active.is_(True), User.role == Role.VICTIM))
    if row is None:
        raise HTTPException(404, 'Client not found')
    return row


def team(db, victim_id):
    """Resolve current assignments afresh. No stored membership or clinical data."""
    counsellors = select(Counsellor.user_id).join(CounsellorAssignment,
        CounsellorAssignment.counsellor_id == Counsellor.id).where(
        CounsellorAssignment.victim_id == victim_id, CounsellorAssignment.active.is_(True))
    legal_ids = select(Case.legal_officer_id).where(Case.victim_id == victim_id).union(
        select(CasePermission.legal_officer_id).join(Case, CasePermission.case_id == Case.id).where(Case.victim_id == victim_id))
    lawyers = select(LegalOfficer.user_id).where(LegalOfficer.id.in_(legal_ids))
    # Re-check the officer's current district even if a stale complaint assignment remains.
    police = select(LawEnforcementOfficer.user_id).join(User, User.id == LawEnforcementOfficer.user_id).join(
        Complaint, Complaint.officer_id == LawEnforcementOfficer.id).where(
        Complaint.victim_id == victim_id, Complaint.district_id == User.district_id)
    return list(db.scalars(select(User).where(User.active.is_(True), or_(
        and_(User.role == Role.COUNSELLOR, User.id.in_(counsellors)),
        and_(User.role == Role.LEGAL_OFFICER, User.id.in_(lawyers)),
        and_(User.role == Role.LAW_ENFORCEMENT, User.id.in_(police))
    )).order_by(User.role, User.name, User.id)))


def client_view(db, victim, user):
    owner = db.get(User, victim.user_id)
    settings = db.scalar(select(UserSettings).where(UserSettings.user_id == owner.id))
    return dict(id=victim.id, user_id=owner.id, name=owner.name,
                district=db.get(District, victim.district_id).name, language=victim.language,
                photo=settings.photo if settings else None,
                contacts=[dict(id=member.id, name=member.name, role=member.role,
                               email=member.email, phone=member.phone)
                          for member in team(db, victim.id) if member.id != user.id and member.role != user.role])


def conversation_participants(db, user, victim_id, recipient_id):
    victim = get_client(db, user, victim_id)
    members = {member.id: member for member in team(db, victim.id)}
    owner = db.get(User, victim.user_id)
    members[owner.id] = owner
    recipient = members.get(recipient_id)
    # Only the two current participants can read this pair's thread. Staff peers
    # from the same department are not exposed as cross-department conversations.
    if user.id not in members or recipient is None or recipient.id == user.id or recipient.role == user.role:
        raise HTTPException(404, 'Conversation not available for these assignments')
    return victim, recipient


def pair_filter(victim_id, sender_id, recipient_id):
    return and_(ChatMessage.victim_id == victim_id, or_(
        and_(ChatMessage.sender_id == sender_id, ChatMessage.recipient_id == recipient_id),
        and_(ChatMessage.sender_id == recipient_id, ChatMessage.recipient_id == sender_id)))


def message_view(row, user, recipient):
    return dict(id=row.id, body=row.body, sender_name=user.name if row.sender_id == user.id else recipient.name,
                mine=row.sender_id == user.id, created_at=row.created_at)


@router.get('/clients', response_model=ClientPage)
def clients(db: DB, user: Actor, search: str = Query('', max_length=120),
            offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50)):
    roles(user, *ALLOWED_ROLES)
    stmt = select(Victim).join(User, User.id == Victim.user_id).where(
        client_scope(user), User.active.is_(True), User.role == Role.VICTIM)
    if search.strip():
        stmt = stmt.where(User.name.icontains(search.strip(), autoescape=True))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(User.name, Victim.id).offset(offset).limit(limit))
    audit(db, user, 'LIST', 'support_team_clients')
    return dict(items=[client_view(db, row, user) for row in rows], total=total)


@router.get('/clients/{victim_id}', response_model=ClientOut)
def client(victim_id: str, db: DB, user: Actor):
    victim = get_client(db, user, victim_id)
    audit(db, user, 'READ', 'support_team_client', victim_id)
    return client_view(db, victim, user)


@router.get('/clients/{victim_id}/messages/{recipient_id}', response_model=ConversationOut)
def messages(victim_id: str, recipient_id: str, db: DB, user: Actor,
             offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
    victim, recipient = conversation_participants(db, user, victim_id, recipient_id)
    rows = db.scalars(select(ChatMessage).where(pair_filter(victim_id, user.id, recipient_id)).order_by(
        ChatMessage.created_at.desc(), ChatMessage.id.desc()).offset(offset).limit(limit))
    audit(db, user, 'READ', 'support_conversation', victim_id)
    return dict(victim_id=victim.id, victim_name=db.get(User, victim.user_id).name,
                recipient_name=recipient.name, recipient_role=recipient.role,
                messages=[message_view(row, user, recipient) for row in rows])


@router.post('/clients/{victim_id}/messages/{recipient_id}', response_model=MessageOut, status_code=201)
def send(victim_id: str, recipient_id: str, payload: MessageInput, db: DB, user: Actor):
    victim, recipient = conversation_participants(db, user, victim_id, recipient_id)
    row = ChatMessage(victim_id=victim.id, sender_id=user.id, recipient_id=recipient.id, body=payload.body)
    db.add(row)
    db.flush()
    audit(db, user, 'SEND', 'support_message', row.id)
    notification = Notification(user_id=recipient.id, title='You have a new support team message')
    db.add(notification)
    db.flush()
    db.add(NotificationOutbox(notification_id=notification.id, channel='IN_APP', status='DELIVERED', delivered_at=now(), attempts=1))
    return message_view(row, user, recipient)
