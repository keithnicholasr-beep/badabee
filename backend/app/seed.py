"""Explicit opt-in synthetic demo seed; never run automatically on application startup."""
import os
import random
from datetime import timedelta
from sqlalchemy import select
from .db import SessionLocal
from .models import *
from .security import passwords
from .config import settings
from .notifications import publish_alert, deliver_in_app


def seed(db, password):
    if db.scalar(select(User.id).limit(1)):
        raise RuntimeError('Seed requires an empty database; refusing to change existing records')
    rng = random.Random(2026)
    hashed = passwords.hash(password)

    def add(model, **kwargs):
        row = model(**kwargs)
        db.add(row)
        db.flush()
        return row

    def user(email, name, role, district=None, state=None):
        return add(User, email=email, name=name, password_hash=hashed, role=role,
                   district_id=district.id if district else None, state_id=state.id if state else None)

    user('national@demo.invalid', 'Demo National Coordinator', Role.NATIONAL_ADMIN)
    global_scheme = add(GovernmentScheme, name='Demo National Recovery Grant', authority='Synthetic National Support Authority',
        description='Synthetic rule example, not a real government entitlement.', benefits='Demo recovery assistance',
        application_process='Demo: submit documents to the support desk.', source_url='https://example.invalid/demo-scheme', is_demo=True)
    add(SchemeEligibility, scheme_id=global_scheme.id, field='annual_income', operator='lte', value=300000)
    add(SchemeDocument, scheme_id=global_scheme.id, name='Income declaration (demo)')
    sequence = 0
    for state_index, (state_name, district_names) in enumerate([
        ('Tamil Nadu', ['Chennai', 'Coimbatore', 'Madurai']),
        ('Karnataka', ['Bengaluru Urban', 'Mysuru', 'Dharwad']),
        ('Kerala', ['Ernakulam', 'Kozhikode', 'Thiruvananthapuram'])]):
        state = add(State, name=state_name)
        user(f'state{state_index + 1}@demo.invalid', f'Demo State Coordinator {state_index + 1}', Role.STATE_ADMIN, state=state)
        scheme = add(GovernmentScheme, name=f'Demo {state_name} Rehabilitation Support', authority='Synthetic State Support Authority',
            description='Synthetic demonstration only; eligibility is not legal advice.', benefits='Demo vocational and shelter support',
            application_process='Demo: apply through district support desk.', source_url='https://example.invalid/state-demo', state_id=state.id, is_demo=True)
        add(SchemeEligibility, scheme_id=scheme.id, field='age', operator='gte', value=18)
        add(SchemeDocument, scheme_id=scheme.id, name='Identity document (demo)')
        for district_index, district_name in enumerate(district_names):
            district = add(District, name=district_name, state_id=state.id)
            key = state_index * 3 + district_index + 1
            user(f'district{key}@demo.invalid', f'Demo District Coordinator {key}', Role.DISTRICT_ADMIN, district, state)
            officer_user = user(f'legal{key}@demo.invalid', f'Demo Legal Officer {key}', Role.LEGAL_OFFICER, district, state)
            officer = add(LegalOfficer, user_id=officer_user.id, designation='Demo legal support officer')
            counsellor_user = user(f'counsellor{key}@demo.invalid', f'Demo Counsellor {key}', Role.COUNSELLOR, district, state)
            counsellor = add(Counsellor, user_id=counsellor_user.id, specialization='Trauma-informed support')
            prosecutor = add(Prosecutor, name=f'Demo Prosecutor {key}', district_id=district.id)
            language = ['Tamil', 'Kannada', 'Malayalam'][state_index]
            for n in range(3):
                ngo = add(NGO, name=f'Demo {district_name} Support Centre {n + 1}', district_id=district.id,
                          latitude=10.0 + key * .25, longitude=76.0 + n * .2, phone='DEMO — no live number', availability='Weekdays 09:00–18:00')
                for service in (['counselling', 'shelter'], ['legal aid', 'women support', 'SC/ST support'], ['medical support', 'rehabilitation'])[n]:
                    add(NGOService, ngo_id=ngo.id, service=service)
                for spoken in ('English', language):
                    add(NGOLanguage, ngo_id=ngo.id, language=spoken)
            for index in range(12):
                sequence += 1
                victim_user = user(f'victim{sequence}@demo.invalid', f'Demo Participant {sequence:03}', Role.VICTIM, district, state)
                victim = add(Victim, user_id=victim_user.id, district_id=district.id, language=language,
                             age=rng.randint(18, 65), annual_income=rng.choice([100000, 180000, 250000, 450000, None]), support_category='GENERAL')
                add(CounsellorAssignment, counsellor_id=counsellor.id, victim_id=victim.id)
                age = rng.randint(35, 350)
                created = now() - timedelta(days=age)
                case = add(Case, case_id=f'DEMO-2026-{sequence:04}', victim_id=victim.id, district_id=district.id,
                           case_type=rng.choice(['Domestic violence', 'Workplace harassment', 'Atrocity complaint', 'Assault']),
                           fir_number=f'DEMO/FIR/{sequence:04}', fir_date=created.date(), police_station=f'Demo {district_name} Station',
                           court=f'Demo {district_name} District Court', legal_officer_id=officer.id, prosecutor_id=prosecutor.id,
                           investigation_status=rng.choice(['PENDING', 'IN_PROGRESS', 'COMPLETED']),
                           compensation_status=rng.choice(['PENDING', 'PENDING', 'APPROVED', 'PAID', 'NOT_APPLIED']),
                           rehabilitation_status=rng.choice(['PENDING', 'IN_PROGRESS', 'COMPLETED', 'NOT_STARTED']),
                           protection_status=rng.choice(['NONE', 'NONE', 'REQUESTED', 'ACTIVE']), created_at=created)
                add(CaseSection, case_id=case.id, act='Synthetic Demonstration Act', section=f'DEMO-{index + 1}')
                stages = ['INCIDENT', 'FIR', 'INVESTIGATION', 'CHARGESHEET', 'TRIAL', 'JUDGMENT', 'REHABILITATION']
                count = rng.randint(2, len(stages))
                for step, stage in enumerate(stages[:count]):
                    add(CaseEvent, case_id=case.id, event_type=stage, stage=stage, description=f'Synthetic {stage.lower()} milestone recorded.',
                        occurred_at=created + timedelta(days=step * 3), actor_id=officer_user.id)
                if count >= 4:
                    case.chargesheet_date = (created + timedelta(days=9)).date()
                    case.chargesheet_reference = f'DEMO-CS-{sequence}'
                    case.investigation_status = 'COMPLETED'
                if count >= 6:
                    case.status = 'CLOSED'
                else:
                    add(Hearing, case_id=case.id, scheduled_at=now() + timedelta(days=rng.randint(0, 20)), purpose='Demo case progress review')
                add(Hearing, case_id=case.id, scheduled_at=created + timedelta(days=12), purpose='Demo initial hearing', status='COMPLETED', outcome='Demo: next review scheduled')
                add(CaseDocument, case_id=case.id, name='Demo FIR reference.pdf', document_type='FIR', storage_key=f'demo/{case.id}/fir.pdf', uploaded_by=officer_user.id)
                for week in range(3):
                    followup = add(Followup, victim_id=victim.id, counsellor_id=counsellor.id,
                        due_at=now() + timedelta(days=week * 7 - 8), status=rng.choice(['PENDING', 'MISSED', 'COMPLETED']))
                    add(CounsellingNote, followup_id=followup.id, author_id=counsellor_user.id,
                        note='SYNTHETIC PRIVATE NOTE. Must never appear in legal or admin responses.')
                add(DistressAssessment, victim_id=victim.id, instrument='SYNTHETIC-DEMO', score=rng.randint(10, 90), assessed_at=now())
                for month in range(6):
                    score = rng.randint(15, 98)
                    level = 'CRITICAL' if score >= 90 else 'HIGH' if score >= 70 else 'MODERATE' if score >= 40 else 'LOW'
                    prediction = add(DistressPrediction, victim_id=victim.id, external_id=f'demo-{sequence}-{month}', score=score,
                        level=level, trend=rng.choice(['RISING', 'STABLE', 'FALLING']), confidence=.81,
                        factors=['Synthetic demonstration signal'], recommended_action='Demo: counsellor review',
                        model_version='synthetic-fixture', observed_at=now() - timedelta(days=(5 - month) * 30))
                    if month == 5:
                        publish_alert(db, prediction)
    while deliver_in_app(db):
        db.flush()
    db.flush()
    return sequence


if __name__ == '__main__':
    password = os.environ.get('DEMO_PASSWORD', '')
    if not settings().demo_seed_enabled or len(password) < 12:
        raise SystemExit('Set DEMO_SEED_ENABLED=true and DEMO_PASSWORD (12+ characters) explicitly')
    with SessionLocal.begin() as db:
        count = seed(db, password)
    print(f'Created {count} synthetic victims/cases across 9 districts and 3 states')
