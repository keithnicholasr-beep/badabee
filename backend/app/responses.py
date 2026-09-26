"""Explicit public DTOs: document shared contracts and whitelist response fields."""
from datetime import date, datetime
from pydantic import BaseModel
from .models import Role


class LocationOut(BaseModel):
    district_id: str
    district: str
    state_id: str
    state: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: Role
    district_id: str | None
    state_id: str | None


class TokenOut(BaseModel):
    access_token: str
    token_type: str


class VictimOut(LocationOut):
    id: str
    name: str
    language: str


class SectionOut(BaseModel):
    id: str
    act: str
    section: str


class CaseOut(LocationOut):
    id: str
    case_id: str
    victim_id: str
    victim: str
    case_type: str
    sections: list[SectionOut]
    stage: str
    fir_number: str | None
    fir_date: date | None
    police_station: str | None
    investigation_status: str
    chargesheet_date: date | None
    chargesheet_reference: str | None
    court: str | None
    prosecutor_id: str | None
    prosecutor: str | None
    legal_officer_id: str | None
    legal_officer: str | None
    next_hearing: datetime | None
    status: str
    compensation_status: str
    rehabilitation_status: str
    protection_status: str
    created_at: datetime
    updated_at: datetime


class CasePage(BaseModel):
    items: list[CaseOut]
    total: int


class EventOut(BaseModel):
    id: str
    event_type: str
    stage: str
    description: str
    occurred_at: datetime


class HearingOut(BaseModel):
    id: str
    case_id: str
    scheduled_at: datetime
    purpose: str
    outcome: str | None = None
    status: str


class DocumentOut(BaseModel):
    id: str
    name: str
    document_type: str
    created_at: datetime


class FollowupOut(BaseModel):
    id: str
    victim_id: str
    counsellor_id: str
    due_at: datetime
    status: str


class PredictionOut(BaseModel):
    id: str
    victim_id: str
    score: float
    level: str
    trend: str
    confidence: float
    factors: list[str]
    recommended_action: str
    model_version: str
    observed_at: datetime
    created_at: datetime


class AlertOut(BaseModel):
    id: str
    victim_id: str
    severity: str
    message: str
    acknowledged_at: datetime | None
    created_at: datetime


class AcknowledgementOut(BaseModel):
    id: str
    acknowledged_at: datetime


class NGOOut(LocationOut):
    id: str
    name: str
    latitude: float | None
    longitude: float | None
    phone: str
    availability: str
    services: list[str]
    languages: list[str]


class NGOMatchOut(NGOOut):
    match_score: int
    match_reasons: list[str]


class EligibilityRuleOut(BaseModel):
    field: str
    operator: str
    value: dict | list | str | int


class SchemeOut(BaseModel):
    id: str
    name: str
    authority: str
    description: str
    benefits: str
    application_process: str
    source_url: str
    state_id: str | None
    applicability: str
    is_demo: bool
    eligibility_criteria: list[EligibilityRuleOut]
    required_documents: list[str]


class RuleExplanation(BaseModel):
    field: str
    result: str


class EligibleSchemeOut(SchemeOut):
    eligibility: str
    explanation: list[RuleExplanation]


class JurisdictionOut(BaseModel):
    level: str
    district_id: str | None
    state_id: str | None


class TrendOut(BaseModel):
    month: str
    average_score: float
    observations: int


class AnalyticsOut(BaseModel):
    jurisdiction: JurisdictionOut
    cases_monitored: int
    high_risk_cases: int
    critical_alerts: int
    followups_pending: int
    case_categories: dict[str, int]
    case_stages: dict[str, int]
    average_case_age_days: float
    compensation_status: dict[str, int]
    rehabilitation_status: dict[str, int]
    distress_trends: list[TrendOut]
