import os
import uuid
from pathlib import Path

# Set TEST_DATABASE_URL to a disposable PostgreSQL database to exercise the same suite there.
os.environ['DATABASE_URL'] = os.environ.get('TEST_DATABASE_URL', f'sqlite:///{Path(__file__).parent.parent / "test-suite.db"}')
os.environ['JWT_SECRET'] = 'test-only-jwt-secret-with-at-least-32-characters'
os.environ['DISTRESS_INGEST_KEY'] = 'test-only-integration-key-with-at-least-32-characters'
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.db import Base, engine, SessionLocal
from app.models import User
from app.main import app
from app.seed import seed
from app.security import token_for
from app.auth import attempts


@pytest.fixture(scope='session', autouse=True)
def database():
    # Disposable test DB only. Refuse generic PostgreSQL database names.
    if engine.dialect.name != 'sqlite' and 'test' not in (engine.url.database or ''):
        raise RuntimeError('TEST_DATABASE_URL must name a disposable database containing test')
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal.begin() as db:
        seed(db, 'Synthetic-test-password-2026')
    yield
    engine.dispose()


@pytest.fixture
def client():
    attempts.clear()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def auth(db):
    def headers(email):
        user = db.scalar(select(User).where(User.email == email))
        return {'Authorization': f'Bearer {token_for(user)}'}
    return headers
