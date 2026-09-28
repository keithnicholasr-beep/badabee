from .responses import TokenOut, UserOut, LocationOut
from collections import defaultdict, deque
from threading import Lock
import time
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from .models import User, Victim, District, Role
from .schemas import Login, Register
from .security import (
    DB, Actor, verify_password, DUMMY_HASH,
    token_for, audit, passwords,
)
from .presenters import fields, location
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix='/auth', tags=['Authentication'])
attempts = defaultdict(deque)
lock = Lock()


@router.post('/login', response_model=TokenOut)
def login(payload: Login, request: Request, db: DB):
    # Single-process MVP throttle; use gateway/shared rate limiting for multiple workers.
    key = request.client.host if request.client else 'unknown'
    clock = time.monotonic()
    with lock:
        for stale in [k for k, v in attempts.items() if not v or v[-1] < clock - 60]:
            del attempts[stale]
        queue = attempts[key]
        while queue and queue[0] < clock - 60:
            queue.popleft()
        if len(queue) >= 10:
            raise HTTPException(429, 'Too many login attempts; retry in one minute', headers={'Retry-After': '60'})
        queue.append(clock)
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    valid = verify_password(payload.password, user.password_hash if user else DUMMY_HASH)
    if not valid or not user or not user.active:
        audit(db, None, 'LOGIN', 'auth', outcome='DENIED')
        db.commit()
        raise HTTPException(401, 'Invalid email or password')
    audit(db, user, 'LOGIN', 'auth')
    return {'access_token': token_for(user), 'token_type': 'bearer'}


@router.get('/me', response_model=UserOut)
def me(db: DB, user: Actor):
    result = fields(
        user,
        'id',
        'email',
        'name',
        'role',
        'district_id',
        'state_id',
    )

    result['victim_id'] = None

    if user.role == Role.VICTIM:
        result['victim_id'] = db.scalar(
            select(Victim.id).where(Victim.user_id == user.id)
        )

    return result

@router.get('/registration-options', response_model=list[LocationOut])
def registration_options(db: DB):
    """Public geography list for the signup form."""
    districts = db.scalars(
        select(District).order_by(District.name)
    )
    return [location(db, district.id) for district in districts]


@router.post('/register', response_model=UserOut, status_code=201)
def register(payload: Register, request: Request, db: DB):
    # Basic single-process signup rate limit.
    ip = request.client.host if request.client else 'unknown'
    key = f'register:{ip}'
    clock = time.monotonic()

    with lock:
        for stale in [
            k for k, values in attempts.items()
            if not values or values[-1] < clock - 60
        ]:
            del attempts[stale]

        queue = attempts[key]

        while queue and queue[0] < clock - 60:
            queue.popleft()

        if len(queue) >= 5:
            raise HTTPException(
                429,
                'Too many signup attempts. Try again in one minute.',
                headers={'Retry-After': '60'},
            )

        queue.append(clock)

    district = db.get(District, payload.district_id)

    if district is None:
        raise HTTPException(422, 'Please select a valid district')

    existing = db.scalar(
        select(User).where(User.email == payload.email)
    )

    if existing:
        raise HTTPException(409, 'This email is already registered')

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=passwords.hash(payload.password),
        role=Role.VICTIM,
        district_id=district.id,
        state_id=district.state_id,
        active=True,
    )

    try:
        db.add(user)
        db.flush()  # Generates user.id before creating the victim.

        victim = Victim(
            user_id=user.id,
            district_id=district.id,
            language=payload.language,
        )

        db.add(victim)
        db.flush()

        audit(db, user, 'REGISTER', 'user', user.id)
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409,
            'Registration could not be completed. The account may already exist.',
        )

    return fields(
        user,
        'id',
        'email',
        'name',
        'role',
        'district_id',
        'state_id',
    )