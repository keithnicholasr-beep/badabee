"""Self-service account settings. No endpoint accepts a target user ID."""
import base64
import binascii
from io import BytesIO
import warnings
from typing import Literal

from fastapi import APIRouter, HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from .models import User, UserSettings
from .security import DB, Actor, audit, passwords, verify_password
from .auth import attempts, lock
import time

router = APIRouter(prefix='/profile', tags=['My profile'])


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=3, max_length=254, pattern=r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    current_password: str = Field(default='', max_length=256)
    language: Literal['English', 'Hindi', 'Tamil', 'Kannada', 'Telugu', 'Malayalam', 'Marathi', 'Bengali'] = 'English'
    theme: Literal['system', 'light', 'dark'] = 'system'
    text_size: Literal['standard', 'large', 'extra-large'] = 'standard'
    high_contrast: bool = False
    reduced_motion: bool = False

    @field_validator('name', 'email', mode='before')
    @classmethod
    def normalize(cls, value, info):
        if isinstance(value, str):
            value = value.strip()
            return value.lower() if info.field_name == 'email' else value
        return value


class PasswordUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)


class PhotoUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    # A null photo removes it. Raw upload limit is 2 MiB.
    data_url: str | None = Field(default=None, max_length=2_800_000)


def preferences(db, user):
    return db.scalar(select(UserSettings).where(UserSettings.user_id == user.id))


def editable_preferences(db, user):
    row = preferences(db, user)
    if row is None:
        row = UserSettings(user_id=user.id)
        db.add(row)
        db.flush()
    return row


def output(db, user):
    row = preferences(db, user)
    return {
        'id': user.id, 'name': user.name, 'email': user.email,
        'role': user.role.value, 'created_at': user.created_at,
        'photo': row.photo if row else None,
        'language': row.language if row else 'English',
        'theme': row.theme if row else 'system',
        'text_size': row.text_size if row else 'standard',
        'high_contrast': row.high_contrast if row else False,
        'reduced_motion': row.reduced_motion if row else False,
    }


def confirm_password(db, user, password):
    clock = time.monotonic()
    key = f'profile:{user.id}'
    with lock:
        queue = attempts[key]
        while queue and queue[0] < clock - 60:
            queue.popleft()
        if len(queue) >= 5:
            raise HTTPException(429, 'Too many attempts. Try again in one minute.')
        queue.append(clock)
    if not verify_password(password, user.password_hash):
        audit(db, user, 'PROFILE_REAUTH', 'user', user.id, outcome='DENIED')
        db.commit()
        raise HTTPException(400, 'Current password is incorrect')


@router.get('')
def get_profile(db: DB, user: Actor):
    return output(db, user)


@router.patch('')
def update_profile(payload: ProfileUpdate, db: DB, user: Actor):
    if payload.email != user.email:
        confirm_password(db, user, payload.current_password)
        if db.scalar(select(User.id).where(func.lower(User.email) == payload.email, User.id != user.id)):
            raise HTTPException(409, 'This email is already registered')
    user.name = payload.name
    user.email = payload.email
    row = editable_preferences(db, user)
    for field in ('language', 'theme', 'text_size', 'high_contrast', 'reduced_motion'):
        setattr(row, field, getattr(payload, field))
    audit(db, user, 'UPDATE_PROFILE', 'user', user.id)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Account update conflicted with another change; please reload')
    return output(db, user)


@router.post('/password')
def change_password(payload: PasswordUpdate, db: DB, user: Actor):
    confirm_password(db, user, payload.current_password)
    if verify_password(payload.new_password, user.password_hash):
        raise HTTPException(400, 'Choose a different new password')
    user.password_hash = passwords.hash(payload.new_password)
    audit(db, user, 'CHANGE_PASSWORD', 'user', user.id)
    db.commit()
    return {'message': 'Password changed. Please sign in again on all devices.'}


@router.post('/photo')
def update_photo(payload: PhotoUpdate, db: DB, user: Actor):
    photo = None
    if payload.data_url is not None:
        try:
            prefix, encoded = payload.data_url.split(',', 1)
            if prefix not in ('data:image/png;base64', 'data:image/jpeg;base64'):
                raise ValueError()
            raw = base64.b64decode(encoded, validate=True)
            if len(raw) > 2 * 1024 * 1024:
                raise ValueError()
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(BytesIO(raw)) as source:
                    if source.format not in ('PNG', 'JPEG') or source.width * source.height > 16_000_000:
                        raise ValueError()
                    source.load()
                    picture = ImageOps.exif_transpose(source).convert('RGB')
                    picture.thumbnail((512, 512))
                    clean = BytesIO()
                    # Re-encode pixels only: strip EXIF/GPS and embedded metadata.
                    picture.save(clean, format='JPEG', quality=85)
                    photo = 'data:image/jpeg;base64,' + base64.b64encode(clean.getvalue()).decode('ascii')
        except (ValueError, binascii.Error, OSError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise HTTPException(422, 'Choose a valid PNG or JPEG up to 2 MB and 16 megapixels')
    row = editable_preferences(db, user)
    row.photo = photo
    audit(db, user, 'REMOVE_PHOTO' if photo is None else 'UPDATE_PHOTO', 'user', user.id)
    db.commit()
    return output(db, user)
