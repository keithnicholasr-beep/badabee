import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, DateTime, Date, Boolean, Integer, Float, JSON, UniqueConstraint, CheckConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base, UTCDateTime


def now():
    return datetime.now(timezone.utc)


class Role(str, enum.Enum):
    VICTIM = 'VICTIM'
    COUNSELLOR = 'COUNSELLOR'
    LEGAL_OFFICER = 'LEGAL_OFFICER'
    DISTRICT_ADMIN = 'DISTRICT_ADMIN'
    STATE_ADMIN = 'STATE_ADMIN'
    NATIONAL_ADMIN = 'NATIONAL_ADMIN'


class Record:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now, onupdate=now)


class State(Record, Base):
    __tablename__ = 'states'
    name: Mapped[str] = mapped_column(String(100), unique=True)


class District(Record, Base):
    __tablename__ = 'districts'
    state_id: Mapped[str] = mapped_column(ForeignKey('states.id'), index=True)
    name: Mapped[str] = mapped_column(String(100))
    __table_args__ = (UniqueConstraint('state_id', 'name'),)


class User(Record, Base):
    __tablename__ = 'users'
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False))
    district_id: Mapped[str | None] = mapped_column(ForeignKey('districts.id'), index=True)
    state_id: Mapped[str | None] = mapped_column(ForeignKey('states.id'), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (CheckConstraint("role != 'DISTRICT_ADMIN' OR district_id IS NOT NULL"), CheckConstraint("role != 'STATE_ADMIN' OR state_id IS NOT NULL"))


class Victim(Record, Base):
    __tablename__ = 'victims'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), unique=True)
    district_id: Mapped[str] = mapped_column(ForeignKey('districts.id'), index=True)
    language: Mapped[str] = mapped_column(String(60), default='English')
    age: Mapped[int | None] = mapped_column(Integer)
    annual_income: Mapped[int | None] = mapped_column(Integer)
    support_category: Mapped[str | None] = mapped_column(String(80))
    __table_args__ = (CheckConstraint('age IS NULL OR (age >= 0 AND age <= 130)'), CheckConstraint('annual_income IS NULL OR annual_income >= 0'))


class Counsellor(Record, Base):
    __tablename__ = 'counsellors'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), unique=True)
    specialization: Mapped[str] = mapped_column(String(120))


class LegalOfficer(Record, Base):
    __tablename__ = 'legal_officers'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), unique=True)
    designation: Mapped[str] = mapped_column(String(120))


class Prosecutor(Record, Base):
    __tablename__ = 'prosecutors'
    name: Mapped[str] = mapped_column(String(120))
    district_id: Mapped[str] = mapped_column(ForeignKey('districts.id'))


class Case(Record, Base):
    __tablename__ = 'cases'
    case_id: Mapped[str] = mapped_column(String(60), unique=True)
    victim_id: Mapped[str] = mapped_column(ForeignKey('victims.id'), index=True)
    district_id: Mapped[str] = mapped_column(ForeignKey('districts.id'), index=True)
    case_type: Mapped[str] = mapped_column(String(100))
    fir_number: Mapped[str | None] = mapped_column(String(80))
    fir_date: Mapped[datetime | None] = mapped_column(Date)
    police_station: Mapped[str | None] = mapped_column(String(160))
    investigation_status: Mapped[str] = mapped_column(String(40), default='PENDING')
    chargesheet_date: Mapped[datetime | None] = mapped_column(Date)
    chargesheet_reference: Mapped[str | None] = mapped_column(String(160))
    court: Mapped[str | None] = mapped_column(String(160))
    prosecutor_id: Mapped[str | None] = mapped_column(ForeignKey('prosecutors.id'))
    legal_officer_id: Mapped[str | None] = mapped_column(ForeignKey('legal_officers.id'), index=True)
    status: Mapped[str] = mapped_column(String(40), default='OPEN')
    compensation_status: Mapped[str] = mapped_column(String(40), default='NOT_APPLIED')
    rehabilitation_status: Mapped[str] = mapped_column(String(40), default='NOT_STARTED')
    protection_status: Mapped[str] = mapped_column(String(40), default='NONE')


class CasePermission(Record, Base):
    __tablename__ = 'case_permissions'
    case_id: Mapped[str] = mapped_column(ForeignKey('cases.id'), index=True)
    legal_officer_id: Mapped[str] = mapped_column(ForeignKey('legal_officers.id'))
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (UniqueConstraint('case_id', 'legal_officer_id'),)


class CaseSection(Record, Base):
    __tablename__ = 'case_sections'
    case_id: Mapped[str] = mapped_column(ForeignKey('cases.id'), index=True)
    act: Mapped[str] = mapped_column(String(200))
    section: Mapped[str] = mapped_column(String(80))
    __table_args__ = (UniqueConstraint('case_id', 'act', 'section'),)


class CaseEvent(Record, Base):
    __tablename__ = 'case_events'
    case_id: Mapped[str] = mapped_column(ForeignKey('cases.id'), index=True)
    event_type: Mapped[str] = mapped_column(String(80))
    stage: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'))


class Hearing(Record, Base):
    __tablename__ = 'hearings'
    case_id: Mapped[str] = mapped_column(ForeignKey('cases.id'), index=True)
    scheduled_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    purpose: Mapped[str] = mapped_column(String(200))
    outcome: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default='SCHEDULED')


class CaseDocument(Record, Base):
    __tablename__ = 'case_documents'
    case_id: Mapped[str] = mapped_column(ForeignKey('cases.id'), index=True)
    name: Mapped[str] = mapped_column(String(200))
    document_type: Mapped[str] = mapped_column(String(80))
    storage_key: Mapped[str] = mapped_column(String(300))
    uploaded_by: Mapped[str] = mapped_column(ForeignKey('users.id'))


class CounsellorAssignment(Record, Base):
    __tablename__ = 'counsellor_assignments'
    counsellor_id: Mapped[str] = mapped_column(ForeignKey('counsellors.id'), index=True)
    victim_id: Mapped[str] = mapped_column(ForeignKey('victims.id'), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint('counsellor_id', 'victim_id'),)


class Followup(Record, Base):
    __tablename__ = 'followups'
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    victim_id: Mapped[str] = mapped_column(ForeignKey('victims.id'), index=True)
    counsellor_id: Mapped[str] = mapped_column(ForeignKey('counsellors.id'))
    due_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    status: Mapped[str] = mapped_column(String(40), default='PENDING')


class CounsellingNote(Record, Base):
    __tablename__ = 'counselling_notes'
    followup_id: Mapped[str] = mapped_column(ForeignKey('followups.id'), unique=True)
    author_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    note: Mapped[str] = mapped_column(Text)


class DistressAssessment(Record, Base):
    __tablename__ = 'distress_assessments'
    victim_id: Mapped[str] = mapped_column(ForeignKey('victims.id'), index=True)
    instrument: Mapped[str] = mapped_column(String(100))
    score: Mapped[float] = mapped_column(Float)
    assessed_at: Mapped[datetime] = mapped_column(UTCDateTime())


class DistressPrediction(Record, Base):
    __tablename__ = 'distress_predictions'
    victim_id: Mapped[str] = mapped_column(ForeignKey('victims.id'), index=True)
    external_id: Mapped[str] = mapped_column(String(120), unique=True)
    score: Mapped[float] = mapped_column(Float)
    level: Mapped[str] = mapped_column(String(20))
    trend: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[float] = mapped_column(Float)
    factors: Mapped[list] = mapped_column(JSON)
    recommended_action: Mapped[str] = mapped_column(Text)
    model_version: Mapped[str] = mapped_column(String(120))
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    __table_args__ = (CheckConstraint('score >= 0 AND score <= 100'), CheckConstraint('confidence >= 0 AND confidence <= 1'))


class Alert(Record, Base):
    __tablename__ = 'alerts'
    victim_id: Mapped[str] = mapped_column(ForeignKey('victims.id'), index=True)
    prediction_id: Mapped[str | None] = mapped_column(ForeignKey('distress_predictions.id'), unique=True)
    severity: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(Text)
    acknowledged_by: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    acknowledged_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class ChatMessage(Record, Base):
    __tablename__ = 'chat_messages'
    victim_id: Mapped[str] = mapped_column(ForeignKey('victims.id'), index=True)
    sender_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    recipient_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    body: Mapped[str] = mapped_column(Text)


class NGO(Record, Base):
    __tablename__ = 'ngos'
    name: Mapped[str] = mapped_column(String(160))
    district_id: Mapped[str] = mapped_column(ForeignKey('districts.id'), index=True)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    phone: Mapped[str] = mapped_column(String(40))
    availability: Mapped[str] = mapped_column(String(120))
    __table_args__ = (CheckConstraint('latitude IS NULL OR (latitude >= -90 AND latitude <= 90)'), CheckConstraint('longitude IS NULL OR (longitude >= -180 AND longitude <= 180)'))


class NGOService(Record, Base):
    __tablename__ = 'ngo_services'
    ngo_id: Mapped[str] = mapped_column(ForeignKey('ngos.id'), index=True)
    service: Mapped[str] = mapped_column(String(80))
    __table_args__ = (UniqueConstraint('ngo_id', 'service'),)


class NGOLanguage(Record, Base):
    __tablename__ = 'ngo_languages'
    ngo_id: Mapped[str] = mapped_column(ForeignKey('ngos.id'), index=True)
    language: Mapped[str] = mapped_column(String(60))
    __table_args__ = (UniqueConstraint('ngo_id', 'language'),)


class GovernmentScheme(Record, Base):
    __tablename__ = 'government_schemes'
    name: Mapped[str] = mapped_column(String(200))
    authority: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    benefits: Mapped[str] = mapped_column(Text)
    application_process: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(String(500))
    state_id: Mapped[str | None] = mapped_column(ForeignKey('states.id'), index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class SchemeEligibility(Record, Base):
    __tablename__ = 'scheme_eligibility'
    scheme_id: Mapped[str] = mapped_column(ForeignKey('government_schemes.id'), index=True)
    field: Mapped[str] = mapped_column(String(80))
    operator: Mapped[str] = mapped_column(String(20))
    value: Mapped[dict | list | str | int] = mapped_column(JSON)


class SchemeDocument(Record, Base):
    __tablename__ = 'scheme_documents'
    scheme_id: Mapped[str] = mapped_column(ForeignKey('government_schemes.id'), index=True)
    name: Mapped[str] = mapped_column(String(200))


class Notification(Record, Base):
    __tablename__ = 'notifications'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    alert_id: Mapped[str | None] = mapped_column(ForeignKey('alerts.id'))
    title: Mapped[str] = mapped_column(String(160))
    read_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    __table_args__ = (UniqueConstraint('user_id', 'alert_id'),)


class NotificationOutbox(Record, Base):
    __tablename__ = 'notification_outbox'
    notification_id: Mapped[str] = mapped_column(ForeignKey('notifications.id'), unique=True)
    channel: Mapped[str] = mapped_column(String(40), default='IN_APP')
    status: Mapped[str] = mapped_column(String(40), default='PENDING')
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    delivered_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class AuditLog(Record, Base):
    __tablename__ = 'audit_logs'
    actor_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), index=True)
    action: Mapped[str] = mapped_column(String(100))
    resource_type: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str | None] = mapped_column(String(120))
    outcome: Mapped[str] = mapped_column(String(40), default='SUCCESS')



class UserSettings(Record, Base):
    __tablename__ = 'user_settings'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), unique=True)
    photo: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(60), default='English')
    theme: Mapped[str] = mapped_column(String(20), default='system')
    text_size: Mapped[str] = mapped_column(String(20), default='standard')
    high_contrast: Mapped[bool] = mapped_column(Boolean, default=False)
    reduced_motion: Mapped[bool] = mapped_column(Boolean, default=False)

class WellbeingCheckin(Record, Base):
    __tablename__ = 'wellbeing_checkins'
    victim_id: Mapped[str] = mapped_column(ForeignKey('victims.id'), index=True)
    request_id: Mapped[str] = mapped_column(String(80))
    mood: Mapped[int] = mapped_column(Integer)
    stress: Mapped[int] = mapped_column(Integer)
    sleep: Mapped[int] = mapped_column(Integer)
    feels_unsafe: Mapped[bool] = mapped_column(Boolean)
    text: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(10))
    prediction_id: Mapped[str] = mapped_column(ForeignKey('distress_predictions.id'))
    __table_args__ = (UniqueConstraint('victim_id', 'request_id'), CheckConstraint('mood BETWEEN 1 AND 5 AND stress BETWEEN 1 AND 5 AND sleep BETWEEN 1 AND 5'))


class SupportAction(Record, Base):
    __tablename__ = 'support_actions'
    victim_id: Mapped[str] = mapped_column(ForeignKey('victims.id'), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    kind: Mapped[str] = mapped_column(String(30))
    note: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default='OPEN')
    ngo_id: Mapped[str | None] = mapped_column(ForeignKey('ngos.id'))
    resolved_by: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class SupportChatTurn(Record, Base):
    __tablename__ = 'support_chat_turns'
    victim_id: Mapped[str] = mapped_column(ForeignKey('victims.id'), index=True)
    request_id: Mapped[str] = mapped_column(String(80))
    message: Mapped[str] = mapped_column(Text)
    reply: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(10))
    intent: Mapped[str] = mapped_column(String(40))
    __table_args__ = (UniqueConstraint('victim_id', 'request_id'),)
