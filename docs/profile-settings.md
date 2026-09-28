# Profile settings

Select **My profile & settings** from the dashboard sidebar. The counsellor placeholder also provides this option. Users can update their name and email, add/change/remove a picture, save appearance/accessibility preferences, and change their password. Email changes require the current password. Password changes sign out all sessions.

## Existing installation update

Stop the local servers, then run from the backend folder:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Start the app again. The additive migration creates user_settings and preserves existing records. It has already been applied to the current local installation. Pillow is the new photo-validation dependency.

Language preferences are stored, but full interface translations are not yet implemented. No identity-verification or government-certification claim is implied by profile settings. Roles and jurisdiction remain administrator-managed.

## Validation

Backend tests run against the disposable test database configured in tests/conftest.py, never the local account database. Run `python -m pytest -q` from backend. Frontend: run `npm run lint` and `npm run build` from swastya.
