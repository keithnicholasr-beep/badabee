# Support portals — implementation handoff

This branch extends commit `de28882` inside the repository's **badabee/** folder. It preserves the legal/admin frontend and authentication behavior. The original `swastya/` starter path is no longer the application root on the current main branch.

## What works

- Victim home: case/hearing, assigned counsellors, legal officer, next follow-up, weekly check-in due date, support requests.
- Check-in: validated sliders, safety flag, optional text, explicit acknowledgement, persistent answers, idempotent submission.
- Transparent demo assessment: check-in signals, recent missed/overdue follow-ups, approaching hearing, previous score; history and high-risk alerts.
- Grounded support chat: recorded hearing, counsellor, schemes and case stage; saved conversation, safe fallback and safety guidance.
- Counsellor workspace: scoped caseload, risk filters, summary counts, profiles, accessible history chart/table, private notes, follow-up scheduling/status, care actions and alert acknowledgement.
- Saved emergency/support requests; counsellor alerts and in-app notifications. Repeated active requests return the same ticket.
- NGO referral records, interventions, review records and completion tracking.
- English/Hindi/Kannada core victim interface and chat; keyboard controls, focusable navigation, native modal and skip link.
- Repeatable in-app weekly/follow-up reminders, migration, tests and configuration example.

## Explicit limits

This is a demo-ready support workflow, not a clinically validated or production-operated service.

- The scoring provider is **unvalidated demo rules**, not a trained ML predictor or diagnostic tool. `confidence: 0.0` means uncalibrated, not a probability estimate. Text analysis is narrow phrase matching, not robust NLP/emotion analysis. Speech/IVRS/SMS ingestion is not implemented. Interaction frequency is not yet scored.
- Chat uses stored records and intent rules, not an LLM. Unsupported requests get a limited-capability response. Source case data remains in its stored language.
- Counsellor detail screens, backend validation messages and seeded content remain English. Hindi/Kannada copy needs native-speaker review. Full localization and screen-reader certification remain follow-up work.
- Emergency requests are **saved for human review only**. No dispatch, SMS, external calls or guaranteed response. The user can choose the `tel:112` link. Source: https://www.mha.gov.in/en/commoncontent/emergency-response-support-system-erss .
- Referrals are records, not messages to NGOs. Demo organizations/contacts/schemes are synthetic.
- Alert acknowledgement is separate from resolving a care request and from recording a review. A clinician/counsellor determines intervention.
- Victim portal responses omit raw risk scores. The legacy own-distress API remains available per the existing access contract; no broad authorization redesign was made.
- Reminders require an external scheduler. Run one reminder worker to avoid concurrent duplicate-key races. Portal lists/history are capped for MVP; no full-history pagination yet.
- Production deployment, real providers, verified directories, operational staffing and PostgreSQL deployment verification are not included in this local handoff.

## File map — learn in this order

| File | Purpose |
|---|---|
| `swastya/src/App.jsx` | Chooses the new portal for VICTIM and COUNSELLOR roles |
| `swastya/src/support/SupportPortal.jsx` | Shell, navigation, language and profile loading |
| `swastya/src/support/Victim.jsx` | Victim home, check-in, chat and resources |
| `swastya/src/support/Counsellor.jsx` | Caseload, profile, notes, follow-ups, actions |
| `swastya/src/support/services.js` | All support API calls |
| `swastya/src/support/shared.jsx` | Loading/error states, dialog, chart and notifications |
| `swastya/src/support/i18n.js` | Victim-flow translations and date formatting |
| `backend/app/portal.py` | Scoped API endpoints and workflow composition |
| `backend/app/ai/distress.py` | Features, provider contract and demo rules |
| `backend/app/ai/chat.py` | Grounded chat provider contract and implementation |
| `backend/app/reminders.py` | Weekly and scheduled-follow-up in-app reminders |
| `backend/migrations/versions/2_support_portals.py` | New tables and actual follow-up completion timestamps |
| `backend/tests/test_portals.py` | Support workflow/privacy regression tests |

## Run locally on macOS

From the repository's inner `badabee/` directory (the one containing `backend/`, `swastya/` and `compose.yaml`):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48)); print(secrets.token_urlsafe(48))"
```

Put the two different generated strings into `JWT_SECRET` and `DISTRESS_INGEST_KEY` in `.env`. For a quick **synthetic local demo**, set `DATABASE_URL=sqlite:///./demo.db`. For PostgreSQL, use the existing README setup and your own DB password. Do not overwrite an existing configured `.env`.

```bash
python -m alembic upgrade head
```

Only for a new empty demo database, choose a password of at least 12 characters, then seed:

```bash
export DEMO_SEED_ENABLED=true
read -s DEMO_PASSWORD
export DEMO_PASSWORD
python -m app.seed
unset DEMO_PASSWORD
python -m app.reminders
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

After `read -s DEMO_PASSWORD`, type your chosen password and press Enter; it will not echo. The seed refuses databases with existing users.

In another terminal, from the inner `badabee/` directory:

```bash
cd swastya
npm ci
npm run dev
```

Open the Local URL in your browser. Use `victim1@demo.invalid` or `counsellor1@demo.invalid` and the password you chose. Existing legal/admin demo accounts still work. Reloading requires login because tokens stay in memory.

For ongoing reminders, schedule `backend/.venv/bin/python -m app.reminders` from the `backend/` working directory hourly. It creates at most one weekly reminder per ISO calendar week and one reminder per scheduled follow-up. No external notification provider is used.

## New contracts

All portal endpoints use the existing bearer token. IDs are resolved on the server; do not hardcode a victim UUID.

| Method/path | Purpose |
|---|---|
| GET `/portal/me` | Current user's victim/counsellor `profile_id` |
| GET `/portal/victims/{id}` | Scoped composite profile; raw predictions only for counsellors |
| GET `/portal/caseload` | Assigned victims with risk/contact/follow-up summaries |
| POST `/portal/checkins` | `request_id,mood,stress,sleep,feels_unsafe,text,language`; all slider values 1–5 |
| POST `/portal/chat` | `request_id,message,language,intent?`; stored response |
| GET `/portal/chat` | Own most recent 50 chat turns |
| POST `/portal/victims/{id}/actions` | `kind,note,ngo_id?`; victim allowed SUPPORT/EMERGENCY only |
| POST `/portal/actions/{id}/resolve` | Assigned counsellor completes a care action |
| POST `/portal/followups/{id}/note` | Assigned owning counsellor saves/updates own private note |

Existing follow-up, alert and directory contracts are reused. AI ingestion secrets never enter frontend code.

## Verification commands

```bash
cd backend
source .venv/bin/activate
python -m pytest -q
python -m alembic check
cd ../swastya
npm run lint
npm run build
```

Database tests use the existing disposable test database fixture. Do not set `TEST_DATABASE_URL` to real data.

## Guided next step

Before applying or copying code, check your local `pwd`, `git status --short` and branch. We will compare your local layout, protect your work, and then walk through one component at a time. This branch has not been pushed or deployed.

## Verification performed for this branch

- 34 backend tests passed on SQLite (26 existing + 8 new workflow tests).
- Frontend production build passed. Lint has one pre-existing warning in `Resources.jsx`; no new support-file warnings.
- New migration upgrade, schema-drift check, downgrade and re-upgrade passed on a separate local SQLite demo database.
- Demo seed and in-app reminders ran successfully.
- Live browser verification was blocked: the environment could not download a valid Chromium archive. Visual/mobile behavior remains to be checked on your Mac. PostgreSQL was not re-tested in this session.
