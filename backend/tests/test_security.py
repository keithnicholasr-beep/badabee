from datetime import timedelta
import uuid
import jwt
import pytest
from sqlalchemy import select, func
from app.models import *
from app.config import settings
from app.security import token_for


def case_for(db, email):
    return db.scalar(select(Case).join(Victim, Case.victim_id == Victim.id).join(User, Victim.user_id == User.id).where(User.email == email))


def test_auth_and_expiry(client, db):
    assert client.get('/auth/me').status_code == 401
    assert client.post('/auth/login', json={'email': 'missing@demo.invalid', 'password': 'bad'}).status_code == 401
    response = client.post('/auth/login', json={'email': 'legal1@demo.invalid', 'password': 'Synthetic-test-password-2026'})
    assert response.status_code == 200
    token = response.json()['access_token']
    me = client.get('/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert me.json()['role'] == 'LEGAL_OFFICER'
    assert 'password_hash' not in me.text
    user = db.scalar(select(User).where(User.email == 'legal1@demo.invalid'))
    claims = {'sub': user.id, 'iat': now() - timedelta(hours=2), 'exp': now() - timedelta(hours=1),
              'iss': settings().jwt_issuer, 'aud': settings().jwt_audience}
    expired = jwt.encode(claims, settings().jwt_secret, algorithm='HS256')
    assert client.get('/auth/me', headers={'Authorization': f'Bearer {expired}'}).status_code == 401
    assert client.get('/auth/me', headers={'Authorization': f'Bearer {token[:-4]}xxxx'}).status_code == 401


@pytest.mark.parametrize('email,expected', [('victim1@demo.invalid', 1), ('counsellor1@demo.invalid', 12),
    ('legal1@demo.invalid', 12), ('district1@demo.invalid', 12), ('state1@demo.invalid', 36), ('national@demo.invalid', 0)])
def test_scoped_case_lists(client, auth, email, expected):
    result = client.get('/cases', headers=auth(email)).json()
    assert result['total'] == expected


@pytest.mark.parametrize('email', ['victim1@demo.invalid', 'counsellor1@demo.invalid', 'legal1@demo.invalid', 'district1@demo.invalid', 'state1@demo.invalid', 'national@demo.invalid'])
def test_foreign_ids_never_grant_access(client, db, auth, email):
    foreign = case_for(db, 'victim49@demo.invalid')
    for path in [f'/cases/{foreign.id}', f'/cases/{foreign.id}/timeline', f'/cases/{foreign.id}/documents',
                 f'/victims/{foreign.victim_id}', f'/victims/{foreign.victim_id}/case',
                 f'/victims/{foreign.victim_id}/eligible-schemes', f'/victims/{foreign.victim_id}/followups',
                 f'/ngos/match?victim_id={foreign.victim_id}', f'/hearings?case_id={foreign.id}']:
        assert client.get(path, headers=auth(email)).status_code == 404, path


def test_legal_privacy_and_permissions(client, db, auth):
    case = case_for(db, 'victim1@demo.invalid')
    followup = db.scalar(select(Followup).where(Followup.victim_id == case.victim_id))
    headers = auth('legal1@demo.invalid')
    assert client.get(f'/victims/{case.victim_id}/distress', headers=headers).status_code == 404
    assert client.get(f'/victims/{case.victim_id}/followups', headers=headers).status_code == 404
    assert client.get(f'/followups/{followup.id}/note', headers=headers).status_code == 403
    for path in ['/cases', f'/cases/{case.id}', f'/victims/{case.victim_id}', '/followups', '/alerts']:
        result = client.get(path, headers=headers)
        assert 'SYNTHETIC PRIVATE NOTE' not in result.text
        assert 'annual_income' not in result.text
    assert client.get(f'/followups/{followup.id}/note', headers=auth('counsellor1@demo.invalid')).status_code == 200
    assert client.get(f'/followups/{followup.id}/note', headers=auth('district1@demo.invalid')).status_code == 403


def test_explicit_read_permission_and_revoke(client, db, auth):
    case = case_for(db, 'victim49@demo.invalid')
    officer = db.scalar(select(LegalOfficer).join(User).where(User.email == 'legal1@demo.invalid'))
    permission = CasePermission(case_id=case.id, legal_officer_id=officer.id, can_edit=False)
    db.add(permission); db.commit()
    headers = auth('legal1@demo.invalid')
    assert client.get(f'/cases/{case.id}', headers=headers).status_code == 200
    assert client.patch(f'/cases/{case.id}', headers=headers, json={'status': 'CLOSED'}).status_code == 404
    permission.can_edit = True; db.commit()
    assert client.patch(f'/cases/{case.id}', headers=headers, json={'status': case.status}).status_code == 200
    db.delete(permission); db.commit()
    assert client.get(f'/cases/{case.id}', headers=headers).status_code == 404


def test_analytics_jurisdictions(client, db, auth):
    assert client.get('/analytics/district', headers=auth('district1@demo.invalid')).json()['cases_monitored'] == 12
    assert client.get('/analytics/state', headers=auth('state1@demo.invalid')).json()['cases_monitored'] == 36
    national = client.get('/analytics/national', headers=auth('national@demo.invalid'))
    assert national.json()['cases_monitored'] == 108
    assert 'victim_id' not in national.text and 'Demo Participant' not in national.text
    foreign = case_for(db, 'victim49@demo.invalid')
    assert client.get(f'/analytics/district?district_id={foreign.district_id}', headers=auth('district1@demo.invalid')).status_code == 403
    assert client.get(f'/analytics/state?district_id={foreign.district_id}', headers=auth('state1@demo.invalid')).status_code == 403
    assert client.get('/analytics/national', headers=auth('state1@demo.invalid')).status_code == 403
    assert client.get('/analytics/state', headers=auth('district1@demo.invalid')).status_code == 403
    filtered = client.get(f'/analytics/national?district_id={foreign.district_id}', headers=auth('national@demo.invalid'))
    assert filtered.json()['cases_monitored'] == 12


def test_distress_ingest_idempotence_validation_and_outbox(client, db, auth):
    case = case_for(db, 'victim1@demo.invalid')
    payload = {'victim_id': case.victim_id, 'score': 82, 'level': 'HIGH', 'trend': 'RISING', 'confidence': .81,
               'factors': ['two missed follow-ups'], 'recommended_action': 'Priority counsellor review'}
    assert client.post('/integrations/distress', json=payload).status_code == 401
    headers = {'X-Ingest-Key': settings().distress_ingest_key, 'Idempotency-Key': str(uuid.uuid4())}
    first = client.post('/integrations/distress', json=payload, headers=headers)
    assert first.status_code == 201, first.text
    second = client.post('/integrations/distress', json=payload, headers=headers)
    assert first.json()['id'] == second.json()['id']
    assert db.scalar(select(func.count()).select_from(Alert).where(Alert.prediction_id == first.json()['id'])) == 1
    assert client.post('/integrations/distress', json={**payload, 'score': 99}, headers=headers).status_code == 409
    assert client.post('/integrations/distress', json={**payload, 'score': 101}, headers={**headers, 'Idempotency-Key': str(uuid.uuid4())}).status_code == 422
    from app.notifications import deliver_in_app
    assert deliver_in_app(db) >= 1
    db.commit()
    assert deliver_in_app(db) == 0
    notice = client.get('/notifications', headers=auth('counsellor1@demo.invalid')).json()
    assert notice
    assert client.post(f'/notifications/{notice[0]["id"]}/read', headers=auth('counsellor2@demo.invalid')).status_code == 404
    assert client.post(f'/notifications/{notice[0]["id"]}/read', headers=auth('counsellor1@demo.invalid')).status_code == 200


def test_alert_acknowledgement_scope(client, db, auth):
    case = case_for(db, 'victim1@demo.invalid')
    alert = Alert(victim_id=case.victim_id, severity='CRITICAL', message='Synthetic review')
    db.add(alert); db.commit()
    assert client.post(f'/alerts/{alert.id}/acknowledge', headers=auth('district2@demo.invalid')).status_code == 404
    assert client.post(f'/alerts/{alert.id}/acknowledge', headers=auth('national@demo.invalid')).status_code == 403
    assert client.post(f'/alerts/{alert.id}/acknowledge', headers=auth('legal1@demo.invalid')).status_code == 403
    one = client.post(f'/alerts/{alert.id}/acknowledge', headers=auth('district1@demo.invalid'))
    two = client.post(f'/alerts/{alert.id}/acknowledge', headers=auth('district1@demo.invalid'))
    assert one.status_code == 200 and one.json() == two.json()


def test_login_rate_limit(client):
    for _ in range(10):
        assert client.post('/auth/login', json={'email': 'nobody@demo.invalid', 'password': 'bad'}).status_code == 401
    assert client.post('/auth/login', json={'email': 'nobody@demo.invalid', 'password': 'bad'}).status_code == 429


def test_deactivated_user_and_assignment_revocation(client, db, auth):
    user = db.scalar(select(User).where(User.email == 'counsellor1@demo.invalid'))
    headers = auth(user.email)
    user.active = False; db.commit()
    assert client.get('/auth/me', headers=headers).status_code == 401
    user.active = True; db.commit()
    case = case_for(db, 'victim1@demo.invalid')
    assignment = db.scalar(select(CounsellorAssignment).where(CounsellorAssignment.victim_id == case.victim_id))
    assignment.active = False; db.commit()
    assert client.get(f'/victims/{case.victim_id}', headers=headers).status_code == 404
    assignment.active = True; db.commit()


def test_audit_records_have_no_private_payload(client, db, auth):
    client.get('/cases', headers=auth('legal1@demo.invalid'))
    rows = list(db.scalars(select(AuditLog)))
    assert any(x.action == 'LIST' and x.resource_type == 'cases' for x in rows)
    assert any(x.action == 'ACCESS_DENIED' for x in rows)
    assert not hasattr(rows[0], 'payload')


def test_registration_persists_and_cannot_self_assign_staff_role(client, db):
    import uuid
    from sqlalchemy import select
    from app.models import User, Victim, Role
    locations = client.get('/auth/registration-options').json()
    payload = {'name': 'Synthetic Signup', 'email': f'{uuid.uuid4()}@example.test',
               'password': 'Synthetic-signup-password-2026', 'district_id': locations[0]['district_id'], 'language': 'Tamil'}
    assert client.post('/auth/register', json={**payload, 'role': 'NATIONAL_ADMIN'}).status_code == 422
    response = client.post('/auth/register', json=payload)
    assert response.status_code == 201
    assert response.json()['role'] == 'VICTIM'
    db.expire_all()
    user = db.scalar(select(User).where(User.email == payload['email']))
    assert user and user.role == Role.VICTIM
    assert db.scalar(select(Victim.id).where(Victim.user_id == user.id))
    login = client.post('/auth/login', json={'email': payload['email'], 'password': payload['password']})
    assert login.status_code == 200
    me = client.get('/auth/me', headers={'Authorization': 'Bearer '+login.json()['access_token']})
    assert me.json()['victim_id'] is not None
    assert client.post('/auth/register', json=payload).status_code == 409


def test_local_staff_creator_links_both_roles(client, db, monkeypatch):
    import uuid
    import create_staff
    from sqlalchemy import select
    from app.models import User, LegalOfficer, Counsellor, Role
    for choice, role, model in [('1', Role.LEGAL_OFFICER, LegalOfficer), ('2', Role.COUNSELLOR, Counsellor)]:
        email = f'{uuid.uuid4()}@example.test'
        answers = iter([choice, 'Synthetic Staff', email])
        monkeypatch.setattr('builtins.input', lambda prompt: next(answers))
        monkeypatch.setattr(create_staff, 'getpass', lambda prompt: 'Synthetic-staff-password-2026')
        create_staff.main()
        user = db.scalar(select(User).where(User.email == email))
        assert user.role == role
        assert db.scalar(select(model.id).where(model.user_id == user.id))
        assert client.post('/auth/login', json={'email': email, 'password': 'Synthetic-staff-password-2026'}).status_code == 200
