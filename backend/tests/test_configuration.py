import pytest
from pydantic import ValidationError
from app.config import Settings


def test_example_and_reused_secrets_rejected():
    with pytest.raises(ValidationError):
        Settings(jwt_secret='replace-with-a-long-random-secret-before-running',
                 distress_ingest_key='different-secret-with-32-or-more-characters')
    with pytest.raises(ValidationError):
        Settings(jwt_secret='same-secret-that-is-at-least-32-characters',
                 distress_ingest_key='same-secret-that-is-at-least-32-characters')
