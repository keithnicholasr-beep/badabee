import uuid
import pytest
from sqlalchemy import select
from app.models import (User, Role, Victim, CounsellorAssignment, Counsellor, Case, LegalOfficer,
                        CasePermission, Complaint, LawEnforcementOfficer, ChatMessage, AuditLog)
from app.security import token_for


def account(db, email):
    return db.scalar(select(User).where(User.email == email))


def victim_id(db, number=1):
    return db.scalar(select(Victim.id).where(Victim.user_id == account(db, f'victim{number}@demo.invalid').id))


def path(db, number=1, recipient='legal1@demo.invalid'):
    return f'/communications/clients/{victim_id(db, number)}/messages/{account(db, recipient).id}'


@pytest.mark.parametrize('sender,recipient', [
    ('victim1@demo.invalid','legal1@demo.invalid'),
    ('victim1@demo.invalid','counsellor1@demo.invalid'),
    ('victim1@demo.invalid','police1@demo.invalid'),
    ('legal1@demo.invalid','counsellor1@demo.invalid'),
    ('legal1@demo.invalid','police1@demo.invalid'),
    ('counsellor1@demo.invalid','police1@demo.invalid'),
])
def test_pair_messages_persist_and_reply(client, db, auth, sender, recipient):
    url=path(db, recipient=recipient)
    text=f'Synthetic pair check {uuid.uuid4()}'
    response=client.post(url, headers=auth(sender), json={'body':text})
    assert response.status_code==201, response.text
    assert response.json()['mine'] is True
    reverse=path(db, recipient=sender)
    received=client.get(reverse, headers=auth(recipient))
    assert received.status_code==200, received.text
    saved=next(m for m in received.json()['messages'] if m['id']==response.json()['id'])
    assert saved['body']==text and saved['mine'] is False
    assert client.post(reverse, headers=auth(recipient), json={'body':'Synthetic reply'}).status_code==201
    assert db.get(ChatMessage, response.json()['id']).sender_id==account(db, sender).id
    assert db.scalar(select(AuditLog.id).where(AuditLog.action=='SEND', AuditLog.resource_type=='support_message', AuditLog.resource_id==response.json()['id']))


def test_card_scopes_and_no_clinical_fields(client, db, auth):
    vid=victim_id(db)
    for email in ['legal1@demo.invalid','counsellor1@demo.invalid','police1@demo.invalid','victim1@demo.invalid']:
        response=client.get(f'/communications/clients/{vid}', headers=auth(email))
        assert response.status_code==200
        data=response.json()
        assert data['name']=='Demo Participant 001'
        assert set(data)=={'id','user_id','name','district','language','photo','contacts'}
        assert all(set(c)=={'id','name','role','email','phone'} for c in data['contacts'])
        assert 'note' not in response.text and 'annual_income' not in response.text and 'password_hash' not in response.text
    for email in ['victim2@demo.invalid','legal2@demo.invalid','counsellor2@demo.invalid','police2@demo.invalid']:
        assert client.get(f'/communications/clients/{vid}', headers=auth(email)).status_code==404
    for email in ['district1@demo.invalid','state1@demo.invalid','national@demo.invalid']:
        assert client.get('/communications/clients', headers=auth(email)).status_code==403
        assert client.get(f'/communications/clients/{vid}', headers=auth(email)).status_code==403
    only=client.get('/communications/clients', headers=auth('victim1@demo.invalid')).json()
    assert only['total']==1 and only['items'][0]['id']==vid
    first=client.get('/communications/clients?limit=3', headers=auth('legal1@demo.invalid')).json()
    second=client.get('/communications/clients?limit=3&offset=3', headers=auth('legal1@demo.invalid')).json()
    assert not {x['id'] for x in first['items']} & {x['id'] for x in second['items']}
    assert client.get('/communications/clients?search=001', headers=auth('legal1@demo.invalid')).json()['total']==1


def test_third_parties_cannot_read_other_pair_threads(client, db, auth):
    marker=f'Private synthetic pair {uuid.uuid4()}'
    url=path(db, recipient='counsellor1@demo.invalid')
    assert client.post(url, headers=auth('victim1@demo.invalid'), json={'body':marker}).status_code==201
    legal=client.get(url, headers=auth('legal1@demo.invalid'))
    assert legal.status_code==200 and marker not in legal.text
    assert marker not in client.get(url, headers=auth('police1@demo.invalid')).text
    for email in ['victim2@demo.invalid','legal2@demo.invalid','national@demo.invalid']:
        assert client.get(url, headers=auth(email)).status_code in (403,404)
    # Same pair in another victim's context is a different conversation.
    assert marker not in client.get(path(db, number=2, recipient='counsellor1@demo.invalid'), headers=auth('legal1@demo.invalid')).text
    wrong=path(db, recipient='counsellor2@demo.invalid')
    assert client.post(wrong, headers=auth('victim1@demo.invalid'), json={'body':'Unauthorized'}).status_code==404
    assert client.get(path(db, recipient='victim1@demo.invalid'), headers=auth('victim1@demo.invalid')).status_code==404
    assert client.post(url, headers=auth('legal1@demo.invalid'), json={'body':'Valid body', 'sender_id':account(db,'victim1@demo.invalid').id}).status_code==422
    assert client.post(url, headers=auth('legal1@demo.invalid'), json={'body':'  '}).status_code==422


def test_revoked_counsellor_loses_cards_and_both_sides_chat(client, db, auth):
    vid=victim_id(db,4)
    counsellor=account(db,'counsellor1@demo.invalid')
    cid=db.scalar(select(Counsellor.id).where(Counsellor.user_id==counsellor.id))
    assignment=db.scalar(select(CounsellorAssignment).where(CounsellorAssignment.victim_id==vid,CounsellorAssignment.counsellor_id==cid))
    url=path(db,number=4,recipient='counsellor1@demo.invalid')
    assert client.post(url,headers=auth('victim4@demo.invalid'),json={'body':'Before revocation'}).status_code==201
    assignment.active=False;db.commit()
    try:
        assert client.get(f'/communications/clients/{vid}',headers=auth('counsellor1@demo.invalid')).status_code==404
        assert client.get(url,headers=auth('victim4@demo.invalid')).status_code==404
        assert client.post(url,headers=auth('legal1@demo.invalid'),json={'body':'After revocation'}).status_code==404
        assert counsellor.id not in [c['id'] for c in client.get(f'/communications/clients/{vid}',headers=auth('legal1@demo.invalid')).json()['contacts']]
    finally:
        assignment.active=True;db.commit()


def test_inactive_and_transferred_officers_lose_access(client, db, auth):
    vid=victim_id(db)
    officer=account(db,'police1@demo.invalid'); original=officer.district_id
    officer.district_id=account(db,'police2@demo.invalid').district_id;db.commit()
    try:
        assert client.get(f'/communications/clients/{vid}',headers=auth('police1@demo.invalid')).status_code==404
        assert client.get(path(db,recipient='police1@demo.invalid'),headers=auth('legal1@demo.invalid')).status_code==404
    finally:
        officer.district_id=original;db.commit()
    officer.active=False;db.commit()
    try:
        assert client.get(path(db,recipient='police1@demo.invalid'),headers=auth('victim1@demo.invalid')).status_code==404
    finally:
        officer.active=True;db.commit()


def test_contact_phone_validation_and_preservation(client, db, auth):
    user=account(db,'legal1@demo.invalid');h=auth(user.email)
    payload={'name':user.name,'email':user.email,'phone':'+1 202 555 0100'}
    assert client.patch('/profile',headers=h,json=payload).status_code==200
    profile=client.get('/profile',headers=h).json()
    assert profile['phone']==payload['phone']
    assert client.patch('/profile',headers=h,json={'name':user.name,'email':user.email,'theme':'light'}).status_code==200
    contacts=client.get(f'/communications/clients/{victim_id(db)}',headers=auth('counsellor1@demo.invalid')).json()['contacts']
    assert next(c for c in contacts if c['id']==user.id)['phone']==payload['phone']
    assert client.patch('/profile',headers=h,json={**payload,'phone':'javascript:alert(1)'}).status_code==422
    assert client.patch('/profile',headers=h,json={**payload,'phone':''}).status_code==200
    assert client.get('/profile',headers=h).json()['phone'] is None


def test_default_theme_and_authentication(client, auth):
    assert client.get('/profile',headers=auth('victim5@demo.invalid')).json()['theme']=='light'
    assert client.get('/communications/clients').status_code==401


def test_legal_permission_removal_revokes_contact_and_history(client, db, auth):
    vid=victim_id(db,6)
    case=db.scalar(select(Case).where(Case.victim_id==vid))
    legal_user=account(db,'legal2@demo.invalid')
    lawyer=db.scalar(select(LegalOfficer).where(LegalOfficer.user_id==legal_user.id))
    permission=CasePermission(case_id=case.id,legal_officer_id=lawyer.id,can_edit=False)
    db.add(permission);db.commit()
    url=path(db,number=6,recipient='counsellor1@demo.invalid')
    assert client.get(f'/communications/clients/{vid}',headers=auth(legal_user.email)).status_code==200
    assert client.post(url,headers=auth(legal_user.email),json={'body':'Synthetic permitted coordination'}).status_code==201
    db.delete(permission);db.commit()
    assert client.get(url,headers=auth(legal_user.email)).status_code==404
    assert client.get(path(db,number=6,recipient=legal_user.email),headers=auth('counsellor1@demo.invalid')).status_code==404


def test_replacement_lawyer_cannot_read_previous_lawyer_thread(client, db, auth):
    vid=victim_id(db,7)
    case=db.scalar(select(Case).where(Case.victim_id==vid));old=case.legal_officer_id
    url=path(db,number=7,recipient='counsellor1@demo.invalid')
    marker=f'Previous lawyer thread {uuid.uuid4()}'
    assert client.post(url,headers=auth('legal1@demo.invalid'),json={'body':marker}).status_code==201
    next_user=account(db,'legal2@demo.invalid')
    case.legal_officer_id=db.scalar(select(LegalOfficer.id).where(LegalOfficer.user_id==next_user.id));db.commit()
    try:
        assert client.get(url,headers=auth('legal1@demo.invalid')).status_code==404
        response=client.get(url,headers=auth(next_user.email))
        assert response.status_code==200 and marker not in response.text
    finally:
        case.legal_officer_id=old;db.commit()
