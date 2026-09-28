from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, field_validator


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Login(Input):
    # Preserve passwords exactly as entered, including spaces.
    model_config = ConfigDict(
        extra='forbid',
        str_strip_whitespace=False,
    )

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)

    @field_validator('email', mode='before')
    @classmethod
    def normalize_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class Register(Login):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(
        min_length=3,
        max_length=254,
        pattern=r'^[^@\s]+@[^@\s]+\.[^@\s]+$',
    )
    password: str = Field(min_length=12, max_length=256)
    district_id: str = Field(min_length=1, max_length=36)
    language: str = Field(default='English', min_length=1, max_length=60)

    @field_validator('name', 'language', mode='before')
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class SectionInput(Input):
    act: str = Field(min_length=1, max_length=200)
    section: str = Field(min_length=1, max_length=80)


class CaseCreate(Input):
    victim_id: str
    case_id: str = Field(min_length=1, max_length=60)
    case_type: str = Field(min_length=1, max_length=100)
    fir_number: str | None = Field(default=None, max_length=80)
    fir_date: date | None = None
    police_station: str | None = Field(default=None, max_length=160)
    court: str | None = Field(default=None, max_length=160)
    prosecutor_id: str | None = None
    sections: list[SectionInput] = Field(default_factory=list, max_length=30)


class CaseUpdate(Input):
    investigation_status: Literal['PENDING', 'IN_PROGRESS', 'COMPLETED'] | None = None
    chargesheet_date: date | None = None
    chargesheet_reference: str | None = Field(default=None, max_length=160)
    court: str | None = Field(default=None, max_length=160)
    prosecutor_id: str | None = None
    status: Literal['OPEN', 'CLOSED', 'ON_HOLD'] | None = None
    compensation_status: Literal['NOT_APPLIED', 'PENDING', 'APPROVED', 'PAID', 'REJECTED'] | None = None
    rehabilitation_status: Literal['NOT_STARTED', 'PENDING', 'IN_PROGRESS', 'COMPLETED'] | None = None
    protection_status: Literal['NONE', 'REQUESTED', 'ACTIVE', 'RESOLVED'] | None = None

    @field_validator('investigation_status', 'status', 'compensation_status', 'rehabilitation_status', 'protection_status')
    @classmethod
    def non_null_status(cls, value):
        if value is None:
            raise ValueError('Status cannot be null')
        return value


class EventInput(Input):
    event_type: str = Field(min_length=1, max_length=80)
    stage: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=4000)
    occurred_at: AwareDatetime

    @field_validator('occurred_at')
    @classmethod
    def not_future(cls, value):
        from .models import now
        if value > now():
            raise ValueError('Timeline events must have occurred already')
        return value


class HearingInput(Input):
    scheduled_at: AwareDatetime
    purpose: str = Field(min_length=1, max_length=200)


class HearingUpdate(Input):
    status: Literal['SCHEDULED', 'COMPLETED', 'CANCELLED']
    outcome: str | None = Field(default=None, max_length=4000)


class DocumentInput(Input):
    name: str = Field(min_length=1, max_length=200)
    document_type: str = Field(min_length=1, max_length=80)
    storage_key: str = Field(min_length=1, max_length=300)


class FollowupInput(Input):
    victim_id: str
    due_at: AwareDatetime
    note: str | None = Field(default=None, max_length=10000)


class FollowupUpdate(Input):
    status: Literal['PENDING', 'COMPLETED', 'MISSED', 'CANCELLED']


class PredictionInput(Input):
    victim_id: str
    score: float = Field(ge=0, le=100)
    level: Literal['LOW', 'MODERATE', 'HIGH', 'CRITICAL']
    trend: Literal['RISING', 'STABLE', 'FALLING']
    confidence: float = Field(ge=0, le=1)
    factors: list[str] = Field(max_length=30)
    recommended_action: str = Field(min_length=1, max_length=2000)
    model_version: str = Field(default='unspecified', max_length=120)
    observed_at: AwareDatetime | None = None

    @field_validator('factors')
    @classmethod
    def factors_length(cls, value):
        if any(len(item) > 500 for item in value):
            raise ValueError('Each factor must be 500 characters or fewer')
        return value

    @field_validator('observed_at')
    @classmethod
    def observation_not_future(cls, value):
        from .models import now
        if value and value > now():
            raise ValueError('Observation cannot be in the future')
        return value
