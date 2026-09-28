from uuid import uuid4
from datetime import timedelta
from sqlalchemy import select
from app.models import User, Victim, DistressPrediction, Alert, now
from app.ai.distress import Features, predict_distress, text_signals
from app.reminders import run_reminders


def victim_id(db, email='victim1@demo.invalid'):
    return db.scalar(select(Victim.id).join(User, Victim.user_id == User.id).where(User.email == email))


def test_profile_bootstrap_and_scoping(client, db, auth):
    v = victim_id(db)
    victim = auth('victim1@demo.invalid')
    assert client.get('/portal/me', headers=victim).json()['profile_id'] == v
    data = client.get(f'/portal/victims/{v}', headers=victim).json()
    assert data['predictions'] == [] and data['notes'] == []
    assert data['counsellors'] and data['cases']
    assert client.get(f'/portal/victims/{v}', headers=auth('victim2@demo.invalid')).status_code == 404
    assert client.get(f'/portal/victims/{v}', headers=auth('counsellor2@demo.invalid')).status_code == 404
    assert client.get('/portal/me', headers=auth('legal1@demo.invalid')).status_code == 403
    assert client.get('/portal/caseload', headers=victim).status_code == 403


def test_checkin_creates_prediction_alert_and_is_idempotent(client, db, auth):
    v = victim_id(db)
    headers = auth('victim1@demo.invalid')
    payload = {'request_id': str(uuid4()), 'mood': 1, 'stress': 5, 'sleep': 1, 'feels_unsafe': True, 'text': 'Threatened', 'language': 'en'}
    first = client.post('/portal/checkins', headers=headers, json=payload)
    assert first.status_code == 201, first.text
    assert first.json()['wellbeing'] == 'EXTRA_SUPPORT'
    assert 'score' not in first.json() and 'confidence' not in first.json()
    again = client.post('/portal/checkins', headers=headers, json=payload)
    assert again.json()['id'] == first.json()['id']
    assert client.post('/portal/checkins', headers=headers, json={**payload, 'mood': 2}).status_code == 409
    prediction = db.scalar(select(DistressPrediction).where(DistressPrediction.victim_id == v).order_by(DistressPrediction.created_at.desc()))
    assert prediction.level == 'CRITICAL' and prediction.confidence == 0
    assert db.scalar(select(Alert).where(Alert.prediction_id == prediction.id))
    assert client.get('/notifications', headers=auth('counsellor1@demo.invalid')).json()
    assert client.post('/portal/checkins', headers=auth('counsellor1@demo.invalid'), json=payload).status_code == 403
    assert client.post('/portal/checkins', headers=headers, json={**payload, 'mood': 8}).status_code == 422
    assert client.post('/portal/checkins', headers=headers, json={**payload, 'victim_id': v}).status_code == 422


def test_action_ownership_and_emergency_repeat(client, db, auth):
    v = victim_id(db)
    headers = auth('victim1@demo.invalid')
    body = {'kind': 'EMERGENCY', 'note': 'Please review my support request'}
    first = client.post(f'/portal/victims/{v}/actions', headers=headers, json=body)
    assert first.status_code == 201
    assert client.post(f'/portal/victims/{v}/actions', headers=headers, json=body).json()['id'] == first.json()['id']
    assert client.post(f'/portal/victims/{v}/actions', headers=headers, json={'kind': 'REVIEW', 'note': 'test'}).status_code == 403
    assert client.post(f'/portal/actions/{first.json()["id"]}/resolve', headers=auth('counsellor2@demo.invalid')).status_code == 404
    result = client.post(f'/portal/actions/{first.json()["id"]}/resolve', headers=auth('counsellor1@demo.invalid'))
    assert result.json()['status'] == 'COMPLETED'
    assert result.json()['resolved_at']


def test_notes_and_last_contact(client, db, auth):
    v = victim_id(db)
    headers = auth('counsellor1@demo.invalid')
    row = client.post('/followups', headers=headers, json={'victim_id': v, 'due_at': (now() + timedelta(days=1)).isoformat()}).json()
    path = f'/portal/followups/{row["id"]}/note'
    assert client.post(path, headers=headers, json={'note': 'First note'}).status_code == 200
    assert client.post(path, headers=headers, json={'note': 'Updated private note'}).json()['note'] == 'Updated private note'
    assert client.post(path, headers=auth('counsellor2@demo.invalid'), json={'note': 'Forbidden'}).status_code == 404
    assert client.post(path, headers=auth('victim1@demo.invalid'), json={'note': 'Forbidden'}).status_code == 403
    assert client.patch(f'/followups/{row["id"]}', headers=headers, json={'status':'COMPLETED'}).status_code == 200
    rows = client.get('/portal/caseload', headers=headers).json()
    assert next(r for r in rows if r['id'] == v)['last_contact']


def test_grounded_chat_and_no_cross_user_history(client, auth):
    headers = auth('victim1@demo.invalid')
    body = {'request_id':str(uuid4()), 'message':'Who is my counsellor?', 'language':'en'}
    response = client.post('/portal/chat', headers=headers, json=body)
    assert response.status_code == 201, response.text
    assert response.json()['intent'] == 'counsellor'
    assert 'Counsellor' in response.json()['reply']
    assert client.post('/portal/chat', headers=headers, json=body).json()['id'] == response.json()['id']
    assert client.get('/portal/chat', headers=auth('victim2@demo.invalid')).json() == []
    assert client.get('/portal/chat', headers=auth('legal1@demo.invalid')).status_code == 403
    assert client.post('/portal/chat', headers=headers, json={**body, 'message':'Changed'}).status_code == 409


def test_safety_overrides_chat_shortcut_and_multilingual(client, auth):
    for lang, message in [('en','I feel unsafe'), ('hi','मुझे मदद चाहिए'), ('kn','ಸಹಾಯ ಬೇಕು')]:
        body = {'request_id':str(uuid4()), 'message':message, 'language':lang, 'intent':'hearing'}
        reply = client.post('/portal/chat', headers=auth('victim1@demo.invalid'), json=body).json()
        assert reply['intent'] == 'safety' and '112' in reply['reply']


def test_demo_risk_interface_and_negation():
    low = predict_distress(Features(5,1,5,False,'I am not unsafe'))
    assert low['level'] == 'LOW' and low['score'] == 0
    assert not text_signals('I am not unsafe')['threat']
    high = predict_distress(Features(1,5,1,True,'', previous_score=10))
    assert high['level'] == 'CRITICAL' and high['trend'] == 'RISING'
    assert high['confidence'] == 0 and 'human' in high['recommended_action']


def test_reminders_are_idempotent_and_private(client, db, auth):
    first = run_reminders(db)
    db.commit()
    assert first > 0
    assert run_reminders(db) == 0
    db.commit()
    rows = client.get('/notifications', headers=auth('victim2@demo.invalid')).json()
    assert any('check-in' in x['title'] for x in rows)
    assert client.post(f'/notifications/{rows[0]["id"]}/read', headers=auth('victim3@demo.invalid')).status_code == 404
