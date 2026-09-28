# Victim and counsellor support integration

This integration starts from `main` at `350bb35` (Keith's September 28 frontend merge). It keeps the public landing page, sign-up, victim dashboard, case pages, schemes, directory, and existing legal and admin routes. The victim dashboard gains check-ins, support chat, requests, emergency guidance, and notifications. Counsellors get the caseload, follow-ups, review alerts, and decision support portal.

The old `feature/victim-counsellor-ai` branch has a different repository root and no shared merge base with this `main`. Open a **new** pull request from a new branch created on the current `main`; do not merge or force-push the old branch.

## Apply the accompanying overlay in a fresh clone

From your home directory on your Mac:

```sh
git clone https://github.com/keithnicholasr-beep/badabee.git badabee-integrated
cd ~/badabee-integrated
git switch -c feature/victim-counsellor-ai-v2
unzip -o ~/Downloads/badabee-support-main-overlay.zip -d .
git status --short
```

The repository root now contains `backend/` and `swastya/` directly; there is no second `badabee/` folder inside it. If `git status` shows unexpected changes from a newer `main`, inspect those changes before committing.

## Verify locally

Use the setup in the repository README for backend dependencies and `.env`. Apply migrations to your normal development database:

```sh
cd backend
python -m alembic upgrade head
python -m pytest -q
cd ../swastya
npm ci
npm run build
npm run lint
```

The frontend lint currently reports three React warnings from `src/support/shared.jsx`; it has no lint errors. The tests and build passed against the integration base above.

## Share for review

```sh
cd ~/badabee-integrated
git add backend swastya docs/SUPPORT-INTEGRATION.md
git commit -m "Integrate victim and counsellor support with new dashboard"
git push -u origin feature/victim-counsellor-ai-v2
```

Open the pull-request link GitHub prints and set base to `main`. If Keith makes further changes while you work, fetch and review the new diff before updating the PR. Keep the previous branch as a backup until this PR is accepted.

## Demo boundaries

The distress scores and chat responses are deterministic demo decision support, not a diagnosis or live counsellor. The emergency button shows India's 112 number and records a request for human review; it does not dispatch help. Scheme and directory entries may be synthetic. Only authorized roles can access clinical records and requests.
