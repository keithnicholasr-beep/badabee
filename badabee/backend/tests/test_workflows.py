from datetime import timedelta
from sqlalchemy import select
from app.models import *
from app.directories import evaluate_rule
from test_security import case_for


def test_legal_case_workflow(client, db, auth):
    case = case_for(db, 'victim1@demo.invalid')
    headers = auth('legal1@demo.invalid')
    response = client.patch(f'/cases/{case.id}', headers=headers, json={'protection_status': 'REQUESTED', 'compensation_status': 'PENDING'})
    assert response.status_code == 200
    assert client.patch(f'/cases/{case.id}', headers=headers, json={'status': None}).status_code == 422
    assert client.patch(f'/cases/{case.id}', headers=headers, json={'victim_id': 'other'}).status_code == 422
    assert client.patch(f'/cases/{case.id}', headers=headers, json={'prosecutor_id': 'missing'}).status_code == 422
    milestone = {'event_type': 'CUSTOM_REVIEW', 'stage': 'MEDIATION_REVIEW', 'description': 'Synthetic review completed', 'occurred_at': now().isoformat()}
    assert client.post(f'/cases/{case.id}/timeline', headers=headers, json=milestone).status_code == 201
    assert client.get(f'/cases/{case.id}', headers=headers).json()['stage'] == 'MEDIATION_REVIEW'
    assert client.post(f'/cases/{case.id}/timeline', headers=headers, json={**milestone, 'occurred_at': (now() + timedelta(days=2)).isoformat()}).status_code == 422
    hearing = client.post(f'/cases/{case.id}/hearings', headers=headers, json={'scheduled_at': (now() + timedelta(hours=1)).isoformat(), 'purpose': 'Synthetic review'})
    assert hearing.status_code == 201
    assert client.patch(f'/hearings/{hearing.json()["id"]}', headers=headers, json={'status': 'COMPLETED', 'outcome': 'Reviewed'}).status_code == 200
    assert client.post(f'/cases/{case.id}/documents', headers=headers, json={'name': 'Test reference', 'document_type': 'FIR', 'storage_key': 'private/demo/reference'}).status_code == 201
    assert 'storage_key' not in client.get(f'/cases/{case.id}/documents', headers=headers).text
    new_case = client.post('/cases', headers=headers, json={'victim_id': case.victim_id, 'case_id': 'DEMO-EXTRA', 'case_type': 'Synthetic linked case', 'sections': [{'act': 'Demo Act', 'section': '1'}]})
    assert new_case.status_code == 201
    assert new_case.json()['sections'][0]['section'] == '1'
    assert client.post('/cases', headers=headers, json={'victim_id': case.victim_id, 'case_id': 'DEMO-EXTRA', 'case_type': 'Duplicate'}).status_code == 409


def test_followup_contract(client, db, auth):
    case = case_for(db, 'victim1@demo.invalid')
    payload = {'victim_id': case.victim_id, 'due_at': now().isoformat(), 'note': 'Private test note'}
    assert client.post('/followups', headers=auth('legal1@demo.invalid'), json=payload).status_code == 403
    assert client.post('/followups', headers=auth('counsellor2@demo.invalid'), json=payload).status_code == 404
    result = client.post('/followups', headers=auth('counsellor1@demo.invalid'), json=payload)
    assert result.status_code == 201 and 'note' not in result.json()
    assert client.patch(f'/followups/{result.json()["id"]}', headers=auth('counsellor1@demo.invalid'), json={'status': 'COMPLETED'}).status_code == 200


def test_directory_matching_and_scheme_rules(client, db, auth):
    case = case_for(db, 'victim1@demo.invalid')
    headers = auth('legal1@demo.invalid')
    response = client.get(f'/ngos/match?victim_id={case.victim_id}&required_service=legal%20aid', headers=headers)
    assert response.status_code == 200
    rows = response.json()
    assert rows[0]['district_id'] == case.district_id
    assert all('legal aid' in x['services'] for x in rows)
    assert client.get(f'/ngos/{rows[0]["id"]}', headers=headers).status_code == 200
    schemes = client.get(f'/victims/{case.victim_id}/eligible-schemes', headers=headers)
    assert schemes.status_code == 200
    assert len(schemes.json()) == 2
    victim = db.get(Victim, case.victim_id)
    assert evaluate_rule(victim, {'field': 'age', 'operator': 'gte', 'value': 18}) is True
    assert evaluate_rule(victim, {'field': '__dict__', 'operator': 'eq', 'value': 0}) is None
    assert evaluate_rule(victim, {'field': 'age', 'operator': 'execute', 'value': 0}) is None
    victim.annual_income = None
    assert evaluate_rule(victim, {'field': 'annual_income', 'operator': 'lte', 'value': 300000}) is None


def test_pagination_and_openapi(client, auth):
    headers = auth('legal1@demo.invalid')
    first = client.get('/cases?limit=5&offset=0', headers=headers).json()
    second = client.get('/cases?limit=5&offset=5', headers=headers).json()
    assert not {x['id'] for x in first['items']} & {x['id'] for x in second['items']}
    assert client.get('/cases?limit=10000', headers=headers).status_code == 422
    spec = client.get('/openapi.json').json()
    assert '/integrations/distress' in spec['paths']
    assert len(spec['paths']) >= 30
