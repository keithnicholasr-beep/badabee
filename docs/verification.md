# Verification — 25 September 2026

- **26/26 backend tests passed on SQLite**, with foreign-key enforcement.
- **26/26 backend tests passed on PostgreSQL 18.6**, using an isolated local cluster on port 55432. Existing PostgreSQL databases were not changed.
- Migration upgrade → schema drift check → downgrade → upgrade succeeded on SQLite and PostgreSQL. Alembic reported no new upgrade operations.
- `npm run lint`: passed without lint warnings/errors.
- `npm run build`: passed on Node 24.21.0 / Vite 8.3.0.
- Live browser checks against the PostgreSQL-backed API: legal login/overview, permitted case detail, protection-status update, new timeline milestone, victim-specific NGO matching, scheme eligibility, national overview, state filter (36 cases), district filter (12 cases).
- The connected browser reported no console errors. The protection-status change was also checked directly in the demo database.
- Screens inspected in the connected browser for the legal overview and admin overview. Mobile styling is included but a full device/browser compatibility matrix was not tested.
- Backend tests cover expired/tampered JWTs, account deactivation, all six role scopes, foreign-ID denial, explicit read/edit case permissions and revocation, counselling-note isolation, aggregate-only national access, jurisdiction filter escalation, idempotent ingestion, outbox delivery, alert/notification ownership, login throttling, audit records, input validation, custom timeline stages, hearings, documents, follow-ups, NGO ranking, eligibility unknowns, pagination, and OpenAPI availability.

One upstream test-library deprecation warning remains: the installed Starlette test client warns about future replacement of its HTTPX adapter. It does not affect the passing tests or runtime API.

CI includes PostgreSQL 17 migration/security tests and frontend build/lint jobs. CI has been configured but has not been run on GitHub because changes were not pushed.

These checks validate this MVP implementation, not production readiness or security certification. See the README for remaining deployment and feature boundaries.

## 29 September 2026 — reference layout and law enforcement

- Retained the React/Vite and modular FastAPI/PostgreSQL setup; no new dependencies or duplicate dashboard implementations.
- Added shared complaint workspace, victim submission, district-matched assignment, administrator transfer, officer FIR records and persisted private messages.
- Backend: 44 tests passed, including ownership, cross-district denial, reassignment revocation, clinical isolation, staff provisioning and notification delivery.
- Frontend: lint and production build passed; six existing authentication/preferences tests passed.
- Migration: fresh SQLite upgrade and metadata check passed, preserving both existing jurisdiction constraints. PostgreSQL upgrade and `alembic check` passed. No existing records were reset or seeded.
- Browser: synthetic officer recorded an FIR and sent a message; the synthetic victim saw both and successfully filed a new complaint with automatic assignment. Desktop reference styling and a 390px mobile homepage were inspected. No horizontal page overflow at 390px; navigation scrolls within its own row.
- Restarted the normal hidden development services and verified that the live backend exposes complaint/message routes and Vite responds on 5173. Stopped isolated test servers.
- Public contact details remain unset pending the operator's email and phone number. See `law-enforcement.md` for configuration and officer creation.
