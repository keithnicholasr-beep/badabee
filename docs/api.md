# API contract v0.1

Base URL: `http://127.0.0.1:8000`. Browser development proxy: `/api`. JSON request/response bodies. Interactive OpenAPI is served at `/docs` and `/openapi.json`.

All routes except `/health`, authentication login and integration ingestion require `Authorization: Bearer <JWT>`. Integration ingestion instead requires `X-Ingest-Key` and `Idempotency-Key`. IDs in URL paths are internal UUID strings, not the human-readable case number. Responses use ISO-8601 UTC datetimes and `YYYY-MM-DD` dates. Empty lists are successful responses. Errors use `{"detail": "message"}`; validation errors use FastAPI's standard structured `detail` array. Unknown request fields are rejected.

## Authentication

| Method/path | Contract |
|---|---|
| POST `/auth/login` | `{email,password}` → `{access_token,token_type:"bearer"}`; 401 generic invalid credentials, 429 throttled |
| GET `/auth/me` | `{id,email,name,role,district_id,state_id}`; never returns a hash |

JWT: HS256, required issuer/audience/subject/issued-at/expiry; default 30-minute lifetime. Role and assignment checks read the database on each call. In-memory browser token; no refresh token. `email` is normalized to lowercase during login.

## Cases

| Method/path | Contract |
|---|---|
| GET `/cases` | `offset=0&limit=50` (max 200), optional `status`, `district_id`; scoped `{items:Case[],total}` |
| POST `/cases` | Legal role; `{victim_id,case_id,case_type,fir_number?,fir_date?,police_station?,court?,prosecutor_id?,sections:[{act,section}]}`; returns case, 201 |
| GET `/cases/{id}` | One permitted case; 404 outside scope |
| PATCH `/cases/{id}` | Legal edit permission; investigation, chargesheet date/reference, court, prosecutor, status, compensation, rehabilitation, protection fields; returns updated case |
| GET `/cases/{id}/timeline` | Chronological `{id,event_type,stage,description,occurred_at}[]` |
| POST `/cases/{id}/timeline` | `{event_type,stage,description,occurred_at}`; append, 201; future timestamps rejected |
| POST `/cases/{id}/sections` | `{act,section}`; 201; duplicate pair returns 409 |
| GET `/hearings` | Optional `case_id`, `offset=0&limit=100` (max 200); scoped hearing list |
| POST `/cases/{id}/hearings` | `{scheduled_at,purpose}`; 201 |
| PATCH `/hearings/{id}` | `{status:"SCHEDULED|COMPLETED|CANCELLED",outcome?}` |
| GET `/cases/{id}/documents` | `{id,name,document_type,created_at}[]`; no binary/storage-key exposure |
| POST `/cases/{id}/documents` | `{name,document_type,storage_key}`; trusted legal metadata registration, 201 |
| GET `/legal/overview` | `total_cases,hearings_this_week,pending_investigation,delayed_cases,protection_requests,compensation_pending` |
| GET `/prosecutors` | Prosecutors in districts covered by officer's permitted cases |

`Case` includes `id,case_id,victim_id,victim,case_type,sections,district_id,district,state_id,state,stage,fir_number,fir_date,police_station,investigation_status,chargesheet_date,chargesheet_reference,court,prosecutor_id,prosecutor,legal_officer_id,legal_officer,next_hearing,status,compensation_status,rehabilitation_status,protection_status,created_at,updated_at`.

Case statuses: OPEN/CLOSED/ON_HOLD. Investigation: PENDING/IN_PROGRESS/COMPLETED. Compensation: NOT_APPLIED/PENDING/APPROVED/PAID/REJECTED. Rehabilitation: NOT_STARTED/PENDING/IN_PROGRESS/COMPLETED. Protection: NONE/REQUESTED/ACTIVE/RESOLVED. Null is not accepted for status updates. An assigned prosecutor must belong to the case district. A case takes its district from the permitted victim and its officer from the authenticated creator.

## Shared victim/counsellor contracts

| Method/path | Contract |
|---|---|
| GET `/victims/{id}` | Minimal permitted profile: `id,name,language,district_id,district,state_id,state` |
| GET `/victims/{id}/case` | Array of permitted cases; supports multiple cases per victim |
| GET `/victims/{id}/followups` | Up to 200 latest follow-up metadata rows; legal officers denied |
| GET `/victims/{id}/distress` | Up to 200 latest predictions; own victim or assigned counsellor only |
| GET `/counsellors/{id}/victims` | Active assignments for the authenticated counsellor's own profile |
| POST `/followups` | Assigned counsellor: `{victim_id,due_at,note?}` → metadata, 201; note saved separately |
| PATCH `/followups/{id}` | Assigned owning counsellor: `{status:"PENDING|COMPLETED|MISSED|CANCELLED"}` |
| GET `/followups` | Scoped metadata, `offset=0&limit=100` (max 200) |
| GET `/followups/{id}/note` | Authoring counsellor, still assigned: `{id,note,created_at}` |

Follow-up metadata is `{id,victim_id,counsellor_id,due_at,status}`. Notes are never embedded. Chat and assessment tables define persistence boundaries only; their operational APIs and dashboards belong to the separate support-team workstream.

## Distress producer contract

POST `/integrations/distress` with an independent `X-Ingest-Key` and a producer-generated unique `Idempotency-Key` (1–120 characters):

```json
{
  "victim_id": "<existing victim UUID>",
  "score": 82,
  "level": "HIGH",
  "trend": "RISING",
  "confidence": 0.81,
  "factors": ["negative sentiment increased", "two missed follow-ups"],
  "recommended_action": "Priority counsellor review"
}
```

Optional `model_version` defaults to `unspecified`; optional timezone-aware `observed_at` defaults to receipt time and cannot be in the future. Score range is 0–100, confidence 0–1. Levels: LOW/MODERATE/HIGH/CRITICAL. Trends: RISING/STABLE/FALLING. Up to 30 factors of at most 500 characters each. No model implementation is imported.

Returns the persisted object with `id,created_at,observed_at,model_version` and the original fields. Same key + same payload returns the existing observation (201); same key + different payload returns 409. A concurrent unique-key conflict returns 409; retry the identical request to retrieve the existing observation. HIGH/CRITICAL creates an alert and pending in-app notifications atomically. The producer owns score/level consistency; the backend does not recompute clinical thresholds.

## Alerts and notifications

| Method/path | Contract |
|---|---|
| GET `/alerts` | Scoped operational alerts: `{id,victim_id,severity,message,acknowledged_at,created_at}[]`; `offset/limit` |
| POST `/alerts/{id}/acknowledge` | Assigned counsellor or scoped district/state admin; `{id,acknowledged_at}`; idempotent |
| GET `/notifications` | Up to 100 delivered notifications for current user; assignment rechecked |
| POST `/notifications/{id}/read` | Current user's permitted notification; idempotent read timestamp |

In-app outbox delivery is executed through `python -m app.notifications`. External delivery is not configured. National and legal users cannot access individual distress alerts.

## Directories and schemes

| Method/path | Contract |
|---|---|
| GET `/ngos` | Filters `district_id,state_id,service,language`; offset/limit; NGO list |
| GET `/ngos/match` | Required `victim_id`, optional `required_service,language`; at most 20 ranked results |
| GET `/ngos/{id}` | NGO record |
| GET `/schemes` | Optional `state_id`; includes national schemes |
| GET `/victims/{id}/eligible-schemes` | State-applicable schemes plus rule results; victim access required |
| GET `/jurisdictions` | District/state IDs and names; admins see permitted filter choices |

NGO responses include `id,name,services,languages,district_id,district,state_id,state,latitude,longitude,phone,availability`. Matching first filters required service and unavailable providers. It scores same district +60, otherwise same state +25, preferred language +25, requested service +15. Results include `match_score,match_reasons`. Language is a preference, not a hard exclusion. This is location-based ranking, not road-distance routing.

Schemes include `id,name,authority,description,benefits,application_process,source_url,state_id,applicability,is_demo,eligibility_criteria,required_documents`. Rules are ANDed. Allowlisted fields: `age,annual_income,support_category`; operators: `eq,lte,gte,in`. Unknown/missing/unsupported rules produce NEEDS_REVIEW, not assumed eligibility. Any failed rule produces NOT_ELIGIBLE; all matching nonempty rules produce POTENTIALLY_ELIGIBLE. Responses explain results without exposing the victim's raw eligibility values. A reviewed rule match does not guarantee approval.

## Analytics

- GET `/analytics/district?district_id=...`: district user's own district is implicit; state/national users must select a permitted district.
- GET `/analytics/state?state_id=...&district_id=...`: state user's own state is implicit; national users must select a state. Optional district narrows within the state.
- GET `/analytics/national?state_id=...&district_id=...`: national role only. Optional filters narrow aggregates.

Response: `jurisdiction,cases_monitored,high_risk_cases,critical_alerts,followups_pending,case_categories,case_stages,average_case_age_days,compensation_status,rehabilitation_status,distress_trends`. Breakdowns are `{label: count}` objects; trends are `{month,average_score,observations}[]`. No victim IDs, identities, private notes or prediction factors are returned. See architecture documentation for metric definitions.

## Error handling

401 missing/invalid/expired credentials; 403 role/jurisdiction violation; 404 missing or inaccessible record; 409 duplicate/reference conflict; 422 invalid input; 429 login throttle; 500 generic unexpected error. Raw SQL, credentials and exception payloads are not returned. All responses use `Cache-Control: no-store`. Paginated lists use stable ordering. Frontend shows loading, empty and error states and redirects to login on 401.
