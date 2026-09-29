# Badabee — support coordination MVP

React → one modular FastAPI application → PostgreSQL. This extends the existing `swastya/` React 19 / Vite 8 application. It implements legal case coordination, jurisdiction-filtered administration, NGO matching, scheme rules, and shared support API contracts. It does not implement a prediction model, victim dashboard, or counsellor dashboard.

## Run locally

Requirements: Python 3.12+, Node 22.12+ (Node 24 tested), PostgreSQL 17 or Docker Desktop with its Linux engine running.

1. From the repository root, set a local database password and start PostgreSQL:

   ```powershell
   $env:POSTGRES_PASSWORD = 'choose-a-local-database-password'
   docker compose up -d db
   ```

2. Prepare the backend:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.lock.txt
   Copy-Item .env.example .env
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   Edit `.env`: set `DATABASE_URL` to your database credentials, and set independent random `JWT_SECRET` and `DISTRESS_INGEST_KEY` values. The sample strings are placeholders, not production secrets. URL-encode any special characters in the database password. On macOS/Linux activate with `source .venv/bin/activate`.

3. Apply the migration and optionally seed a dedicated, empty demo database:

   ```powershell
   python -m alembic upgrade head
   $env:DEMO_SEED_ENABLED = 'true'
   $env:DEMO_PASSWORD = 'choose-a-demo-password-of-12-or-more-characters'
   python -m app.seed
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

   The seed refuses to run on a database containing users. It creates 108 synthetic victims/cases, 9 counsellors, 9 legal officers, 27 NGOs, 4 demo schemes, 648 stored distress observations, hearings, milestones, follow-ups and alerts. All identities, legal references, NGO contacts and schemes are synthetic. State/district names are real geography; NGO coordinates are illustrative and not real locations.

4. In another terminal:

   ```powershell
   cd swastya
   npm ci
   npm run dev
   ```

   Open http://localhost:5173. The Vite proxy forwards `/api` to FastAPI. Production hosting must proxy `/api` similarly, or set `VITE_API_URL` at build time and configure backend CORS. Vite uses its native configuration loader for Windows compatibility.

## Demo accounts

Use the password you selected in `DEMO_PASSWORD`.

| Account | Scope |
|---|---|
| `legal1@demo.invalid` | Chennai cases |
| `district1@demo.invalid` | Chennai |
| `state1@demo.invalid` | Tamil Nadu |
| `national@demo.invalid` | National aggregates, with optional narrower filters |
| `counsellor1@demo.invalid` | Assigned victims via API; profile settings available (clinical dashboard pending) |
| `victim1@demo.invalid` | Own records and victim dashboard |

District/Legal/Counsellor accounts 1–3 belong to Tamil Nadu, 4–6 to Karnataka, and 7–9 to Kerala. State accounts 1–3 follow that order. Tokens are held in browser memory and expire after 30 minutes; reloading requires login.

## Verification

```powershell
cd backend
python -m pytest -q
cd ../swastya
npm run lint
npm run build
```

Tests default to a disposable SQLite database with foreign keys enabled. To run against PostgreSQL, set `TEST_DATABASE_URL` to a separate disposable database whose name contains `test`; **the test suite drops and recreates its schema**. Never point tests at application data. The same SQLAlchemy models and APIs run in both environments. PostgreSQL remains the intended application database.

API explorer: http://127.0.0.1:8000/docs. Contracts: [docs/api.md](docs/api.md). Data relationships and authorization: [docs/architecture.md](docs/architecture.md).

## Notification delivery

Distress ingestion atomically persists the prediction, a high/critical alert, recipient notifications, and outbox entries. Deliver pending in-app notifications with:

```powershell
cd backend
python -m app.notifications
```

Run this command periodically in deployment. PostgreSQL row locks support concurrent drains. In-app delivery needs no network provider. SMS/email adapters, retries for external providers, escalation policies, and emergency dispatch are intentionally not implemented. No messages are sent to real people by the seed or the application.

## MVP boundaries

- Documents are a protected **metadata register**. Binary upload/download, malware scanning, and private object storage are not implemented.
- Initial user provisioning, first victim intake, role changes, and assignments are operator-managed database operations; there is no public registration or privilege-management API. Legal officers can create additional cases only for victims they already have permission to access.
- Scheme evaluation is preliminary and explains matching/unknown rules. Demo entries are not actual government programmes. Populate verified sources and reviewed rules before using real schemes.
- Alerts capture integration output; the application does not infer diagnoses or provide emergency monitoring guarantees.
- Analytics are aggregate-only for national admins, but there is no statistical disclosure suppression. Review small-cohort policy before using real data. This MVP calculates aggregates in application code; move expensive aggregations into SQL as volume grows.
- Deploy behind TLS with encrypted storage/backups, restricted database credentials, an external secret store, and agreed retention/access policies before handling real records. The application provides role checks, record scoping, Argon2 hashing, short-lived JWTs, and audit records; it is not a production security certification.
- Login throttling is per process. Use a shared gateway limiter for multi-worker deployment. Logout clears the browser token; server-side session revocation and refresh tokens are not implemented. Disabling a user takes effect on the next request.

## Profile settings and registration

The redesigned public homepage and login card share the existing backend. **New here? Create an account** registers a victim and signs them in. Staff roles are provisioned locally by an administrator; public signup cannot grant staff access.

From the backend folder, run `.\.venv\Scripts\python.exe create_staff.py` to create a legal officer or counsellor with their linked professional profile. Existing accounts are never overwritten. Fresh-database administrator setup remains `python -m app.bootstrap`.

**My profile & settings** is available from each dashboard and the counsellor placeholder. See [profile setup and usage](docs/profile-settings.md). Run `python -m pip install -r requirements.txt` and `python -m alembic upgrade head` before starting an updated backend. Language is a saved communication preference; the interface currently remains English.

## Law enforcement dashboard and reference UI

See [the setup and workflow guide](docs/law-enforcement.md) for officer account creation, victim complaints, FIR records, direct messaging, administrator assignment and footer email/phone configuration.
