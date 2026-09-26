from .responses import TokenOut, UserOut
from collections import defaultdict, deque
from threading import Lock
import time
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from .models import User
from .schemas import Login
from .security import DB, Actor, verify_password, DUMMY_HASH, token_for, audit
from .presenters import fields

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
def me(user: Actor):
    return fields(user, 'id', 'email', 'name', 'role', 'district_id', 'state_id')
