import base64
from io import BytesIO
import uuid

import pytest
from PIL import Image
from sqlalchemy import select

from app.models import User, UserSettings, Role, District, AuditLog
from app.security import passwords, token_for, verify_password

PASSWORD = 'Original-profile-password-2026'


@pytest.fixture
def account(db):
    district = db.scalar(select(District))
    user = User(name='Synthetic Profile User', email=f'{uuid.uuid4()}@example.test',
                password_hash=passwords.hash(PASSWORD), role=Role.LEGAL_OFFICER,
                district_id=district.id, state_id=district.state_id, active=True)
    db.add(user)
    db.commit()
    return user


def headers(user):
    return {'Authorization': f'Bearer {token_for(user)}'}


def form(user, **extra):
    return {'name': user.name, 'email': user.email, **extra}


@pytest.mark.parametrize('role', list(Role))
def test_all_roles_can_edit_only_their_profile(client, db, account, role):
    account.role = role
    db.commit()
    h = headers(account)
    response = client.patch('/profile', headers=h, json=form(account, name='Updated Name', theme='dark', language='Tamil', text_size='large', high_contrast=True, reduced_motion=True))
    assert response.status_code == 200, response.text
    saved = client.get('/profile', headers=h).json()
    assert saved['name'] == 'Updated Name'
    assert saved['theme'] == 'dark' and saved['language'] == 'Tamil'
    assert saved['text_size'] == 'large' and saved['high_contrast'] and saved['reduced_motion']
    assert 'password_hash' not in saved
    assert client.patch('/profile', headers=h, json=form(account, role='NATIONAL_ADMIN')).status_code == 422
    assert client.patch('/profile', headers=h, json=form(account, user_id='another-user')).status_code == 422
    other = db.scalar(select(User).where(User.id != account.id))
    assert client.get('/profile', headers=headers(other)).json()['id'] == other.id


def test_profile_requires_authentication(client):
    assert client.get('/profile').status_code == 401
    assert client.post('/profile/photo', json={'data_url': None}).status_code == 401


def test_email_requires_password_and_unique_address(client, db, account):
    h = headers(account)
    email = f'{uuid.uuid4()}@example.test'
    assert client.patch('/profile', headers=h, json=form(account, email=email)).status_code == 400
    other = db.scalar(select(User).where(User.id != account.id))
    assert client.patch('/profile', headers=h, json=form(account, email=other.email, current_password=PASSWORD)).status_code == 409
    assert client.patch('/profile', headers=h, json=form(account, email='invalid', current_password=PASSWORD)).status_code == 422
    old_email = account.email
    result = client.patch('/profile', headers=h, json=form(account, email=' '+email.upper()+' ', current_password=PASSWORD))
    assert result.status_code == 200
    assert result.json()['email'] == email
    assert client.post('/auth/login', json={'email': old_email, 'password': PASSWORD}).status_code == 401
    assert client.post('/auth/login', json={'email': email, 'password': PASSWORD}).status_code == 200


def test_password_change_revokes_existing_sessions(client, db, account):
    h = headers(account)
    assert client.post('/profile/password', headers=h, json={'current_password': 'wrong', 'new_password': 'A-new-password-2026'}).status_code == 400
    assert client.post('/profile/password', headers=h, json={'current_password': PASSWORD, 'new_password': 'short'}).status_code == 422
    assert client.post('/profile/password', headers=h, json={'current_password': PASSWORD, 'new_password': 'A-new-password-2026'}).status_code == 200
    assert client.get('/profile', headers=h).status_code == 401
    assert client.post('/auth/login', json={'email': account.email, 'password': PASSWORD}).status_code == 401
    assert client.post('/auth/login', json={'email': account.email, 'password': 'A-new-password-2026'}).status_code == 200
    db.refresh(account)
    assert verify_password('A-new-password-2026', account.password_hash)


def test_photo_upload_replace_remove_and_validation(client, db, account):
    h = headers(account)
    for color in ('red', 'blue'):
        buffer = BytesIO()
        Image.new('RGB', (600, 400), color).save(buffer, format='PNG')
        url = 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode()
        response = client.post('/profile/photo', headers=h, json={'data_url': url})
        assert response.status_code == 200
        photo = client.get('/profile', headers=h).json()['photo']
        with Image.open(BytesIO(base64.b64decode(photo.split(',')[1]))) as image:
            assert image.format == 'JPEG' and image.width == 512
            assert image.getpixel((10, 10))[0 if color == 'red' else 2] > 240
            assert not image.getexif()
    for bad in ('data:image/svg+xml;base64,PHN2Zz4=', 'data:image/png;base64,bm90LWltYWdl', 'data:image/png;base64,!!!'):
        assert client.post('/profile/photo', headers=h, json={'data_url': bad}).status_code == 422
    assert client.get('/profile', headers=h).json()['photo'] is not None
    assert client.post('/profile/photo', headers=h, json={'data_url': None}).status_code == 200
    assert client.get('/profile', headers=h).json()['photo'] is None
    row = db.scalar(select(UserSettings).where(UserSettings.user_id == account.id))
    assert row.photo is None
    assert db.scalar(select(AuditLog.id).where(AuditLog.actor_id == account.id, AuditLog.action == 'REMOVE_PHOTO'))
