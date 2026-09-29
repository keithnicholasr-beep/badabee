import uuid
from datetime import date
import pytest
from sqlalchemy import select
from app.models import User, Role, District, State, Victim, LawEnforcementOfficer, Complaint, Notification, AuditLog
from app.security import token_for, passwords


def headers(user):
    return {'Authorization': f'Bearer {token_for(user)}'}


@pytest.fixture
def group(db):
    state = State(name=f'Synthetic law test {uuid.uuid4()}'); db.add(state); db.flush()
    districts = [District(name=f'Synthetic district {i}', state_id=state.id) for i in range(2)]
    db.add_all(districts); db.flush()
    hashed = passwords.hash('Synthetic-law-test-password')
    def user(role, district):
        u = User(name=f'Synthetic {role.value}', email=f'{uuid.uuid4()}@example.test', role=role,
                 district_id=district.id, state_id=state.id, password_hash=hashed)
        db.add(u); db.flush(); return u
    victims = [user(Role.VICTIM, districts[0]) for _ in range(2)]
    for v in victims:
        db.add(Victim(user_id=v.id, district_id=v.district_id))
    officers = [user(Role.LAW_ENFORCEMENT, districts[0]), user(Role.LAW_ENFORCEMENT, districts[0]), user(Role.LAW_ENFORCEMENT, districts[1])]
    profiles = []
    for o in officers:
        p = LawEnforcementOfficer(user_id=o.id, police_station='Synthetic station'); db.add(p); db.flush(); profiles.append(p)
    admins = [user(Role.DISTRICT_ADMIN, d) for d in districts]
    db.commit()
    return dict(victims=victims, officers=officers, profiles=profiles, admins=admins, districts=districts)


def create(client, group):
    response = client.post('/complaints', headers=headers(group['victims'][0]), json={
        'subject': 'Synthetic incident', 'description': 'Synthetic complaint description', 'location': 'Synthetic location', 'incident_date': str(date.today())})
    assert response.status_code == 201, response.text
    return response.json()


def assigned(group, row):
    return next(u for u, p in zip(group['officers'], group['profiles']) if p.id == row['officer_id'])


def test_complaint_fir_and_messages_persist_with_ownership(client, db, group, auth):
    row = create(client, group); path = f"/complaints/{row['id']}"
    victim, other = group['victims']; officer = assigned(group, row)
    assert row['officer_id'] is not None
    assert client.post(path+'/messages', headers=headers(victim), json={'body': 'Please review this complaint.'}).status_code == 201
    assert client.post(path+'/messages', headers=headers(officer), json={'body': 'I have received your complaint.'}).status_code == 201
    assert len(client.get(path+'/messages', headers=headers(victim)).json()) == 2
    assert client.get(path, headers=headers(other)).status_code == 404
    for who in [other, *[u for u in group['officers'] if u.id != officer.id], *group['admins']]:
        assert client.get(path+'/messages', headers=headers(who)).status_code == 404
        assert client.post(path+'/messages', headers=headers(who), json={'body': 'Unauthorized'}).status_code == 404
    for email in ['legal1@demo.invalid', 'counsellor1@demo.invalid', 'national@demo.invalid']:
        assert client.get(path, headers=auth(email)).status_code == 404
        assert client.get('/complaints', headers=auth(email)).status_code == 403
    fir = {'number': 'TEST-1', 'police_station': 'Synthetic station', 'registered_on': str(date.today())}
    assert client.post(path+'/fir', headers=headers(victim), json=fir).status_code == 403
    result = client.post(path+'/fir', headers=headers(officer), json=fir)
    assert result.status_code == 201, result.text
    saved = client.get(path, headers=headers(victim)).json()
    assert saved['fir']['number'] == 'TEST-1' and saved['status'] == 'FIR_REGISTERED'
    assert client.post(path+'/fir', headers=headers(officer), json=fir).status_code == 409
    assert client.patch(path+'/status', headers=headers(officer), json={'status':'IN_REVIEW'}).status_code == 409
    assert client.patch(path+'/status', headers=headers(officer), json={'status':'CLOSED'}).status_code == 200
    assert client.post(path+'/messages', headers=headers(victim), json={'body': 'After closure'}).status_code == 409
    assert db.scalar(select(Notification).where(Notification.user_id == victim.id)) is not None
    assert db.scalar(select(AuditLog).where(AuditLog.resource_id == row['id'], AuditLog.action == 'REGISTER_FIR')) is not None
    vid = db.scalar(select(Victim.id).where(Victim.user_id == victim.id))
    for endpoint in [f'/victims/{vid}', f'/victims/{vid}/distress', f'/victims/{vid}/followups']:
        assert client.get(endpoint, headers=headers(officer)).status_code in (403, 404)


def test_assignment_queue_jurisdiction_and_revocation(client, db, group):
    row = create(client, group); path = f"/complaints/{row['id']}"
    old = assigned(group, row)
    target = next(p for p in group['profiles'][:2] if p.id != row['officer_id'])
    other_district = group['profiles'][2]
    a = headers(group['admins'][0]); outside = headers(group['admins'][1])
    assert client.post(path+'/assign', headers=outside, json={'officer_id':target.id}).status_code == 404
    assert client.post(path+'/assign', headers=a, json={'officer_id':other_district.id}).status_code == 422
    assert client.post(path+'/assign', headers=headers(old), json={'officer_id':target.id}).status_code == 403
    queue = client.get('/complaints/assignment-queue', headers=a).json()
    assert row['id'] in [q['id'] for q in queue]
    assert all('description' not in q and 'victim_name' not in q for q in queue)
    assert client.post(path+'/assign', headers=a, json={'officer_id':target.id}).status_code == 200
    assert client.get(path, headers=headers(old)).status_code == 404
    assert client.post(path+'/fir', headers=headers(old), json={'number':'X', 'police_station':'Test station','registered_on':str(date.today())}).status_code == 404
    new = db.get(User, target.user_id)
    assert client.get(path, headers=headers(new)).status_code == 200


def test_unassigned_complaint_and_input_validation(client, db, group):
    for user in group['officers']:
        user.active = False
    db.commit()
    row = create(client, group); path = f"/complaints/{row['id']}"
    assert row['officer_id'] is None
    h = headers(group['victims'][0])
    assert client.post(path+'/messages', headers=h, json={'body':'Hello'}).status_code == 409
    assert client.post('/complaints', headers=h, json={'subject':'Test', 'description':'A longer description', 'location':'Here', 'victim_id':group['victims'][1].id}).status_code == 422
    assert client.post('/complaints', headers=h, json={'subject':'   ', 'description':'A longer description', 'location':'Here'}).status_code == 422
    assert client.get('/complaints').status_code == 401
    group['officers'][0].active=True; db.commit()
    assert client.post(path+'/assign', headers=headers(group['admins'][0]), json={'officer_id':group['profiles'][0].id}).status_code == 200
    assert client.post(path+'/messages', headers=h, json={'body':'Hello'}).status_code == 201


def test_officer_provisioning_and_notification_delivery(client, db, monkeypatch):
    import create_staff
    email = f'{uuid.uuid4()}@example.test'
    answers = iter(['3', 'Synthetic Officer', email, '1', 'Synthetic station'])
    monkeypatch.setattr('builtins.input', lambda prompt: next(answers))
    monkeypatch.setattr(create_staff, 'getpass', lambda prompt: 'Synthetic-staff-password-2026')
    create_staff.main()
    user = db.scalar(select(User).where(User.email == email))
    assert user.role == Role.LAW_ENFORCEMENT and user.district_id
    assert db.scalar(select(LawEnforcementOfficer).where(LawEnforcementOfficer.user_id == user.id))
    assert client.post('/auth/login', json={'email': email, 'password': 'Synthetic-staff-password-2026'}).status_code == 200
    for path in ['/ngos', '/schemes', '/analytics/district', '/analytics/state', '/analytics/national']:
        assert client.get(path, headers=headers(user)).status_code == 403


def test_fir_validation_and_notification_visibility(client, db, group):
    from datetime import timedelta
    row = create(client, group); path = f"/complaints/{row['id']}"; officer = assigned(group, row)
    victim = group['victims'][0]
    body = {'number':'VALIDATION-1', 'police_station':'Synthetic station', 'registered_on':str(date.today()+timedelta(days=1))}
    assert client.post(path+'/fir', headers=headers(officer), json=body).status_code == 422
    body['registered_on'] = str(date.today()-timedelta(days=1))
    assert client.post(path+'/fir', headers=headers(officer), json=body).status_code == 422
    assert client.post(path+'/messages', headers=headers(victim), json={'body':'   '}).status_code == 422
    assert client.post(path+'/messages', headers=headers(victim), json={'body':'Synthetic notification check'}).status_code == 201
    notices = client.get('/notifications', headers=headers(officer)).json()
    assert any(n['title']=='You have a new complaint message' for n in notices)
    assert 'Synthetic notification check' not in str(notices)
    other_ids = {n['id'] for n in client.get('/notifications', headers=headers(group['officers'][2])).json()}
    assert not other_ids.intersection(n['id'] for n in notices)
