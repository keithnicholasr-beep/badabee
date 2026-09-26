from datetime import timedelta
from typing import Annotated
import secrets
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import Depends, HTTPException, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, or_, false
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import *

DB = Annotated[Session, Depends(get_db)]
bearer = HTTPBearer(auto_error=False)
passwords = PasswordHasher()
DUMMY_HASH = passwords.hash(secrets.token_urlsafe(32))


def verify_password(password, encoded):
    try:
        return passwords.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


def token_for(user):
    config = settings()
    return jwt.encode({'sub': user.id, 'iat': now(), 'exp': now() + timedelta(minutes=config.token_minutes),
                       'iss': config.jwt_issuer, 'aud': config.jwt_audience}, config.jwt_secret, algorithm='HS256')


def current_user(request: Request, db: DB, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    try:
        if credentials is None:
            raise ValueError()
        config = settings()
        payload = jwt.decode(credentials.credentials, config.jwt_secret, algorithms=['HS256'],
                             issuer=config.jwt_issuer, audience=config.jwt_audience,
                             options={'require': ['sub', 'iat', 'exp', 'iss', 'aud']})
        user = db.get(User, payload['sub'])
        if user is None or not user.active:
            raise ValueError()
        request.state.actor_id = user.id
        return user
    except (jwt.PyJWTError, ValueError, TypeError):
        raise HTTPException(401, 'Authentication required', headers={'WWW-Authenticate': 'Bearer'})


Actor = Annotated[User, Depends(current_user)]


def roles(user, *allowed):
    if user.role not in allowed:
        raise HTTPException(403, 'Role does not permit this action')


def district_scope(user, column):
    if user.role == Role.DISTRICT_ADMIN:
        return column == user.district_id
    if user.role == Role.STATE_ADMIN:
        return column.in_(select(District.id).where(District.state_id == user.state_id))
    return false()


def case_scope(user, edit=False):
    if user.role == Role.LEGAL_OFFICER:
        officer = select(LegalOfficer.id).where(LegalOfficer.user_id == user.id)
        permissions = select(CasePermission.case_id).where(CasePermission.legal_officer_id.in_(officer))
        if edit:
            permissions = permissions.where(CasePermission.can_edit.is_(True))
        return or_(Case.legal_officer_id.in_(officer), Case.id.in_(permissions))
    if edit:
        return false()
    if user.role == Role.VICTIM:
        return Case.victim_id.in_(select(Victim.id).where(Victim.user_id == user.id))
    if user.role == Role.COUNSELLOR:
        return Case.victim_id.in_(assigned_victims(user))
    return district_scope(user, Case.district_id)


def assigned_victims(user):
    return select(CounsellorAssignment.victim_id).where(
        CounsellorAssignment.active.is_(True),
        CounsellorAssignment.counsellor_id.in_(select(Counsellor.id).where(Counsellor.user_id == user.id)))


def victim_scope(user, clinical=False):
    if user.role == Role.VICTIM:
        return Victim.user_id == user.id
    if user.role == Role.COUNSELLOR:
        return Victim.id.in_(assigned_victims(user))
    if user.role == Role.LEGAL_OFFICER:
        if clinical:
            return false()
        return Victim.id.in_(select(Case.victim_id).where(case_scope(user)))
    return district_scope(user, Victim.district_id)


def get_victim(db, user, victim_id, clinical=False):
    victim = db.scalar(select(Victim).where(Victim.id == victim_id, victim_scope(user, clinical)))
    if victim is None:
        raise HTTPException(404, 'Victim not found')
    return victim


def get_case(db, user, case_id, edit=False):
    case = db.scalar(select(Case).where(Case.id == case_id, case_scope(user, edit)))
    if case is None:
        raise HTTPException(404, 'Case not found')
    return case


def audit(db, user, action, resource_type, resource_id=None, outcome='SUCCESS'):
    db.add(AuditLog(actor_id=user.id if user else None, action=action,
                    resource_type=resource_type, resource_id=resource_id, outcome=outcome))


def ingest_auth(x_ingest_key: Annotated[str | None, Header()] = None):
    if not x_ingest_key or not secrets.compare_digest(x_ingest_key, settings().distress_ingest_key):
        raise HTTPException(401, 'Invalid integration credential')
