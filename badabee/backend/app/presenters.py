from sqlalchemy import select
from .models import *


def fields(row, *names):
    return {name: getattr(row, name) for name in names}


def location(db, district_id):
    district = db.get(District, district_id)
    return {'district_id': district.id, 'district': district.name,
            'state_id': district.state_id, 'state': db.get(State, district.state_id).name}


def victim_view(db, victim):
    return {'id': victim.id, 'name': db.get(User, victim.user_id).name,
            'language': victim.language, **location(db, victim.district_id)}


def case_view(db, case):
    event = db.scalar(select(CaseEvent).where(CaseEvent.case_id == case.id).order_by(CaseEvent.occurred_at.desc(), CaseEvent.created_at.desc(), CaseEvent.id.desc()))
    hearing = db.scalar(select(Hearing).where(Hearing.case_id == case.id, Hearing.scheduled_at >= now(), Hearing.status == 'SCHEDULED').order_by(Hearing.scheduled_at))
    officer = db.get(LegalOfficer, case.legal_officer_id) if case.legal_officer_id else None
    prosecutor = db.get(Prosecutor, case.prosecutor_id) if case.prosecutor_id else None
    victim = db.get(Victim, case.victim_id)
    return {**fields(case, 'id', 'case_id', 'victim_id', 'case_type', 'fir_number', 'fir_date', 'police_station',
                      'investigation_status', 'chargesheet_date', 'chargesheet_reference', 'court',
                      'prosecutor_id', 'legal_officer_id', 'status', 'compensation_status',
                      'rehabilitation_status', 'protection_status', 'created_at', 'updated_at'),
            **location(db, case.district_id), 'victim': db.get(User, victim.user_id).name,
            'stage': event.stage if event else 'REGISTERED',
            'sections': [fields(x, 'id', 'act', 'section') for x in db.scalars(select(CaseSection).where(CaseSection.case_id == case.id))],
            'prosecutor': prosecutor.name if prosecutor else None,
            'legal_officer': db.get(User, officer.user_id).name if officer else None,
            'next_hearing': hearing.scheduled_at if hearing else None}


def prediction_view(row):
    return fields(row, 'id', 'victim_id', 'score', 'level', 'trend', 'confidence', 'factors',
                  'recommended_action', 'model_version', 'observed_at', 'created_at')
