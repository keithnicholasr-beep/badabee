# Support team cards and private messaging

## Where to find it

- **Victim → My support team:** view assigned staff, click their email/phone, or open a private chat with the lawyer, counsellor or law enforcement officer.
- **Legal / Counsellor / Law enforcement → Clients:** search assigned victims by name, see a basic victim profile card, chat with the victim, or contact another assigned department.
- **My Profile → Contact phone number:** each staff member adds or updates their number here. It becomes visible on authorized team cards. Missing numbers display **Not provided**; no phone numbers are invented.

Messages are stored in PostgreSQL and refresh every 10 seconds while the conversation tab is visible. They survive leaving the page and signing in again. Older/newer controls paginate messages. Email and phone links open the user's mail app or dialler; the app does not send external mail or place calls automatically.

## Assignment and privacy rules

The server derives all members from current records on every request:

- Counsellors: active `CounsellorAssignment` for the victim.
- Lawyers: a case assigned to their `LegalOfficer` profile, or an explicit `CasePermission` for a case concerning that victim.
- Law enforcement: a complaint assigned to their officer profile in the officer's current district.
- Staff must have an active user account with the correct role. The victim account must also be active.

A conversation belongs to **one victim context and one pair of users**. Only its two current participants can read or send messages. An administrator, another team member, or another victim cannot read the thread. Staff-to-staff conversations are between different departments. Removing an assignment or deactivating an account revokes access; a replacement officer does not inherit another person's private threads. The separate complaint message thread keeps its existing complaint-specific rules.

Cards expose only the victim's name, profile image, district and preferred language, plus assigned staff names, roles, email addresses and contact numbers. They do not expose distress assessments, income, legal documents or counselling notes. Counselling notes are never copied into chats automatically. Existing clinical access rules remain unchanged. Read and send actions are audited without copying message bodies into the audit log.

Generic notifications are persisted in the existing in-app notification infrastructure. No external messaging service or new microservice is introduced.

## API contracts

All endpoints require a bearer JWT and allow only VICTIM, LEGAL_OFFICER, COUNSELLOR or LAW_ENFORCEMENT. Administrator roles return 403. Missing/out-of-scope clients or recipients return 404. Validation errors return 422. Extra request fields are rejected.

| Endpoint | Contract |
| --- | --- |
| GET `/communications/clients` | `search?`, `offset=0`, `limit=20` (max 50). Returns `{items: Client[], total}` sorted by victim name/ID. A victim sees only their own card. |
| GET `/communications/clients/{victim_id}` | One authorized client card. |
| GET `/communications/clients/{victim_id}/messages/{recipient_id}` | `offset=0`, `limit=50` (max 100). Returns `{victim_id,victim_name,recipient_name,recipient_role,messages}`. Messages are newest first. Recipient is a user ID returned by a card. |
| POST `/communications/clients/{victim_id}/messages/{recipient_id}` | `{body}` (1–4000 characters after trimming) → message, 201. Sender is always the authenticated user. |

Client: `{id,user_id,name,district,language,photo,contacts}`. Staff contact: `{id,name,role,email,phone}`. Message: `{id,body,sender_name,mine,created_at}` with UTC timestamps. When staff chats with the victim, use the card's `user_id`; for staff contacts use the contact's `id`.

`GET /profile` now returns `phone`. `PATCH /profile` accepts optional `phone`: a 7–32-character phone string using digits, spaces, parentheses, hyphens and an optional leading plus. Empty/null clears it; omission preserves the saved number. Name/email and existing preference contracts still apply.

## Data migration and UI preferences

Migration `b316f79c21d4` adds nullable `users.phone` and an index for the existing `chat_messages` table. Existing users, assignments and messages are preserved. No replacement chat table is created.

Light is now the default for new/unsaved browser preferences, new settings rows and accounts without settings. Existing explicitly saved light/dark/device choices are respected. High contrast and reduced-motion controls sit on one row, wrapping when necessary on small screens or with enlarged text. Footer navigation is grouped beside Contact across all dashboards.

## Verification

Automated coverage checks every supported participant pair, client scope, message isolation, assignment/permission removal, officer district changes, inactive accounts, validated contact numbers and default light appearance. Browser checks use synthetic accounts on isolated development ports and do not send external emails or phone calls.
