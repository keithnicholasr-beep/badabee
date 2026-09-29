"""Complaint and FIR coordination; never grants access to clinical or legal records."""
from datetime import date, datetime
from typing import Literal
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select, func, false
from .models import (User, Role, Victim, District, LawEnforcementOfficer,
                     Complaint, FIRRegistration, ComplaintMessage, Notification, NotificationOutbox, now)
from .security import DB, Actor, roles, audit, district_scope

router = APIRouter(prefix='/complaints', tags=['Complaints and FIRs'])


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class ComplaintInput(Input):
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=10000)
    location: str = Field(min_length=2, max_length=250)
    incident_date: date | None = None

    @field_validator('incident_date')
    @classmethod
    def past_date(cls, value):
        if value and value > date.today():
            raise ValueError('Incident date cannot be in the future')
        return value


class MessageInput(Input):
    body: str = Field(min_length=1, max_length=4000)


class FIRInput(Input):
    number: str = Field(min_length=1, max_length=80)
    police_station: str = Field(min_length=2, max_length=160)
    registered_on: date

    @field_validator('registered_on')
    @classmethod
    def past_date(cls, value):
        if value > date.today():
            raise ValueError('Registration date cannot be in the future')
        return value


class AssignmentInput(Input):
    officer_id: str = Field(min_length=1, max_length=36)


class StatusInput(Input):
    status: Literal['IN_REVIEW', 'CLOSED']


class FIROut(BaseModel):
    id: str
    number: str
    police_station: str
    registered_on: date


class ComplaintOut(BaseModel):
    id: str
    subject: str
    description: str
    location: str
    incident_date: date | None
    status: str
    created_at: datetime
    updated_at: datetime
    district_id: str
    district: str
    victim_name: str
    officer_id: str | None
    officer_name: str | None
    police_station: str | None
    fir: FIROut | None


class MessageOut(BaseModel):
    id: str
    body: str
    sender_name: str
    mine: bool
    created_at: datetime


def scope(user):
    if user.role == Role.VICTIM:
        return Complaint.victim_id.in_(select(Victim.id).where(Victim.user_id == user.id))
    if user.role == Role.LAW_ENFORCEMENT:
        return (Complaint.district_id == user.district_id) & Complaint.officer_id.in_(
            select(LawEnforcementOfficer.id).where(LawEnforcementOfficer.user_id == user.id))
    return false()


def get_complaint(db, user, complaint_id, lock=False):
    statement = select(Complaint).where(Complaint.id == complaint_id, scope(user))
    if lock:
        statement = statement.with_for_update()
    row = db.scalar(statement)
    if row is None:
        raise HTTPException(404, 'Complaint not found')
    return row


def view(db, row):
    victim = db.get(Victim, row.victim_id)
    officer = db.get(LawEnforcementOfficer, row.officer_id) if row.officer_id else None
    fir = db.scalar(select(FIRRegistration).where(FIRRegistration.complaint_id == row.id))
    return dict(id=row.id, subject=row.subject, description=row.description, location=row.location,
                incident_date=row.incident_date, status=row.status, created_at=row.created_at,
                updated_at=row.updated_at, district_id=row.district_id,
                district=db.get(District, row.district_id).name,
                victim_name=db.get(User, victim.user_id).name,
                officer_id=row.officer_id, officer_name=db.get(User, officer.user_id).name if officer else None,
                police_station=officer.police_station if officer else None,
                fir=dict(id=fir.id, number=fir.number, police_station=fir.police_station,
                         registered_on=fir.registered_on) if fir else None)


def choose_officer(db, district_id):
    # Deterministic least-open-complaint matching, replaceable without changing API contracts.
    load = select(func.count(Complaint.id)).where(
        Complaint.officer_id == LawEnforcementOfficer.id, Complaint.status != 'CLOSED'
    ).correlate(LawEnforcementOfficer).scalar_subquery()
    return db.scalar(select(LawEnforcementOfficer).join(User).where(
        User.active.is_(True), User.role == Role.LAW_ENFORCEMENT, User.district_id == district_id
    ).order_by(load, LawEnforcementOfficer.created_at, LawEnforcementOfficer.id).limit(1))


def notify(db, user_id, title):
    # Durable in-app infrastructure; does not send email or SMS.
    notification = Notification(user_id=user_id, title=title)
    db.add(notification)
    db.flush()
    db.add(NotificationOutbox(notification_id=notification.id, channel='IN_APP', status='DELIVERED', delivered_at=now(), attempts=1))


@router.post('', response_model=ComplaintOut, status_code=201)
def create(payload: ComplaintInput, db: DB, user: Actor):
    roles(user, Role.VICTIM)
    victim = db.scalar(select(Victim).where(Victim.user_id == user.id))
    if victim is None:
        raise HTTPException(409, 'A linked victim profile is required')
    officer = choose_officer(db, victim.district_id)
    row = Complaint(victim_id=victim.id, district_id=victim.district_id,
                    officer_id=officer.id if officer else None, **payload.model_dump())
    db.add(row)
    db.flush()
    audit(db, user, 'CREATE', 'complaint', row.id)
    if officer:
        notify(db, officer.user_id, 'A victim complaint has been assigned to you')
    return view(db, row)


@router.get('', response_model=list[ComplaintOut])
def listing(db: DB, user: Actor, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
    roles(user, Role.VICTIM, Role.LAW_ENFORCEMENT)
    audit(db, user, 'READ', 'complaints')
    return [view(db, row) for row in db.scalars(select(Complaint).where(scope(user)).order_by(
        Complaint.created_at.desc(), Complaint.id).offset(offset).limit(limit))]


@router.get('/assignment-queue')
def assignment_queue(db: DB, user: Actor, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
    roles(user, Role.DISTRICT_ADMIN, Role.STATE_ADMIN)
    rows = db.scalars(select(Complaint).where(district_scope(user, Complaint.district_id),
        Complaint.status != 'CLOSED').order_by(Complaint.created_at, Complaint.id).offset(offset).limit(limit))
    audit(db, user, 'READ', 'complaint_assignments')
    # Administrators get assignment metadata, not complaint narratives or private messages.
    return [dict(id=r.id, district_id=r.district_id, district=db.get(District, r.district_id).name,
                 officer_id=r.officer_id, status=r.status, created_at=r.created_at) for r in rows]


@router.get('/officers')
def officers(db: DB, user: Actor):
    roles(user, Role.DISTRICT_ADMIN, Role.STATE_ADMIN)
    return [dict(id=o.id, name=u.name, district_id=u.district_id, police_station=o.police_station)
            for o, u in db.execute(select(LawEnforcementOfficer, User).join(User).where(
                User.active.is_(True), User.role == Role.LAW_ENFORCEMENT, district_scope(user, User.district_id)))]


@router.post('/{complaint_id}/assign')
def assign(complaint_id: str, payload: AssignmentInput, db: DB, user: Actor):
    roles(user, Role.DISTRICT_ADMIN, Role.STATE_ADMIN)
    row = db.scalar(select(Complaint).where(Complaint.id == complaint_id,
        district_scope(user, Complaint.district_id)).with_for_update())
    if not row:
        raise HTTPException(404, 'Complaint not found')
    if row.status == 'CLOSED':
        raise HTTPException(409, 'Closed complaints cannot be reassigned')
    officer = db.scalar(select(LawEnforcementOfficer).join(User).where(
        LawEnforcementOfficer.id == payload.officer_id, User.active.is_(True),
        User.role == Role.LAW_ENFORCEMENT, User.district_id == row.district_id))
    if not officer:
        raise HTTPException(422, 'Choose an active officer in the complaint district')
    if row.officer_id != officer.id:
        row.officer_id = officer.id
        audit(db, user, 'ASSIGN', 'complaint', row.id)
        notify(db, officer.user_id, 'A victim complaint has been assigned to you')
        notify(db, db.get(Victim, row.victim_id).user_id, 'Your complaint officer assignment was updated')
    return {'status': 'assigned'}


@router.get('/{complaint_id}', response_model=ComplaintOut)
def detail(complaint_id: str, db: DB, user: Actor):
    row = get_complaint(db, user, complaint_id)
    audit(db, user, 'READ', 'complaint', row.id)
    return view(db, row)


@router.post('/{complaint_id}/fir', response_model=ComplaintOut, status_code=201)
def register_fir(complaint_id: str, payload: FIRInput, db: DB, user: Actor):
    roles(user, Role.LAW_ENFORCEMENT)
    row = get_complaint(db, user, complaint_id, lock=True)
    if row.status == 'CLOSED' or db.scalar(select(FIRRegistration.id).where(FIRRegistration.complaint_id == row.id)):
        raise HTTPException(409, 'Complaint is closed or already has an FIR')
    if row.incident_date and payload.registered_on < row.incident_date:
        raise HTTPException(422, 'Registration cannot precede the incident')
    db.add(FIRRegistration(complaint_id=row.id, registered_by=row.officer_id,
        district_id=row.district_id, number=payload.number.upper(), police_station=payload.police_station.upper(),
        registered_on=payload.registered_on, registration_year=payload.registered_on.year))
    row.status = 'FIR_REGISTERED'
    db.flush()
    audit(db, user, 'REGISTER_FIR', 'complaint', row.id)
    notify(db, db.get(Victim, row.victim_id).user_id, 'An FIR record is available in your complaint')
    return view(db, row)


@router.patch('/{complaint_id}/status', response_model=ComplaintOut)
def status(complaint_id: str, payload: StatusInput, db: DB, user: Actor):
    roles(user, Role.LAW_ENFORCEMENT)
    row = get_complaint(db, user, complaint_id, lock=True)
    allowed = {'SUBMITTED': {'IN_REVIEW', 'CLOSED'}, 'IN_REVIEW': {'CLOSED'}, 'FIR_REGISTERED': {'CLOSED'}, 'CLOSED': set()}
    if payload.status not in allowed[row.status]:
        raise HTTPException(409, 'This status transition is not permitted')
    row.status = payload.status
    db.flush()
    audit(db, user, 'UPDATE_STATUS', 'complaint', row.id)
    return view(db, row)


def message_view(db, row, user):
    return dict(id=row.id, body=row.body, sender_name=db.get(User, row.sender_id).name,
                mine=row.sender_id == user.id, created_at=row.created_at)


@router.get('/{complaint_id}/messages', response_model=list[MessageOut])
def messages(complaint_id: str, db: DB, user: Actor, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200)):
    get_complaint(db, user, complaint_id)
    audit(db, user, 'READ', 'complaint_messages', complaint_id)
    return [message_view(db, m, user) for m in db.scalars(select(ComplaintMessage).where(
        ComplaintMessage.complaint_id == complaint_id).order_by(ComplaintMessage.created_at.desc(), ComplaintMessage.id.desc()).offset(offset).limit(limit))]


@router.post('/{complaint_id}/messages', response_model=MessageOut, status_code=201)
def send(complaint_id: str, payload: MessageInput, db: DB, user: Actor):
    row = get_complaint(db, user, complaint_id, lock=True)
    officer = db.get(LawEnforcementOfficer, row.officer_id) if row.officer_id else None
    officer_user = db.get(User, officer.user_id) if officer else None
    if not officer_user or not officer_user.active or officer_user.role != Role.LAW_ENFORCEMENT or officer_user.district_id != row.district_id:
        raise HTTPException(409, 'An active officer must be assigned before messaging')
    if row.status == 'CLOSED':
        raise HTTPException(409, 'This complaint is closed; its conversation is read-only')
    message = ComplaintMessage(complaint_id=row.id, sender_id=user.id, body=payload.body)
    db.add(message)
    db.flush()
    audit(db, user, 'SEND', 'complaint_message', message.id)
    recipient = officer.user_id if user.role == Role.VICTIM else db.get(Victim, row.victim_id).user_id
    notify(db, recipient, 'You have a new complaint message')
    return message_view(db, message, user)
