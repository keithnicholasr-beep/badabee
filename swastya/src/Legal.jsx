import { useCallback, useEffect, useState } from "react";
import { api, post, patch } from "./api";
import { Badge, ErrorBox } from "./ui";
import { human, date } from "./format";

export function LegalDashboard({ tableOnly, onSelect }) {
  const [data, setData] = useState(null),
    [metrics, setMetrics] = useState(null),
    [error, setError] = useState("");
  const [offset, setOffset] = useState(0),
    [status, setStatus] = useState("");
  useEffect(() => {
    let active = true;
    Promise.all([
      api(
        `/cases?limit=12&offset=${offset}${status ? `&status=${status}` : ""}`,
      ),
      api("/legal/overview"),
    ])
      .then(([rows, overview]) => {
        if (active) {
          setData(rows);
          setMetrics(overview);
        }
      })
      .catch((e) => active && setError(e.message));
    return () => {
      active = false;
    };
  }, [offset, status]);
  return (
    <>
      <div className="page-heading">
        <div>

          <h1>{tableOnly ? "Case register" : "Your overview"}</h1>
          <p className="muted">Every case, a step toward resolution.</p>
        </div>
        <span className="date-pill">{date(new Date())}</span>
      </div>
      <ErrorBox error={error} />
      {!tableOnly && metrics && (
        <div className="metrics">
          {Object.entries(metrics).map(([key, value]) => (
            <article className="metric" key={key}>
              <span>{human(key)}</span>
              <strong>{value}</strong>
              <small>
                {key === "delayed_cases"
                  ? "No timeline progress for 30+ days"
                  : "Within your permitted cases"}
              </small>
            </article>
          ))}
        </div>
      )}
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Cases under your care</h2>
            <p className="muted small">
              Review progress and coordinate the next action.
            </p>
          </div>
          <label className="inline-label">
            Status
            <select
              value={status}
              onChange={(e) => {
                setData(null);
                setError("");
                setStatus(e.target.value);
                setOffset(0);
              }}
            >
              <option value="">All statuses</option>
              {["OPEN", "CLOSED", "ON_HOLD"].map((s) => (
                <option key={s} value={s}>
                  {human(s)}
                </option>
              ))}
            </select>
          </label>
        </div>
        {!data && !error ? (
          <p className="empty" role="status">
            Loading cases…
          </p>
        ) : data?.items.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  {[
                    "Case ID",
                    "Victim",
                    "Case type",
                    "Sections",
                    "District",
                    "Stage",
                    "Prosecutor",
                    "Next hearing",
                    "Status",
                  ].map((x) => (
                    <th key={x}>{x}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.items.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <button
                        className="text-button"
                        onClick={() => onSelect(c.id)}
                      >
                        {c.case_id}
                      </button>
                    </td>
                    <td>{c.victim}</td>
                    <td>{c.case_type}</td>
                    <td>
                      {c.sections
                        .map((s) => `${s.act} ${s.section}`)
                        .join(", ") || "—"}
                    </td>
                    <td>{c.district}</td>
                    <td>{human(c.stage)}</td>
                    <td>{c.prosecutor || "Unassigned"}</td>
                    <td>{date(c.next_hearing)}</td>
                    <td>
                      <Badge value={c.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="empty">No cases match this view.</p>
        )}
        <div className="pagination">
          <span>{data ? `${data.total} cases` : ""}</span>
          <button
            disabled={offset === 0 || !data}
            onClick={() => {
              setData(null);
              setError("");
              setOffset(offset - 12);
            }}
          >
            Previous
          </button>
          <button
            disabled={!data || offset + 12 >= data.total}
            onClick={() => {
              setData(null);
              setError("");
              setOffset(offset + 12);
            }}
          >
            Next
          </button>
        </div>
      </section>
    </>
  );
}

export function CaseDetail({ caseId, onBack }) {
  const [data, setData] = useState(null),
    [error, setError] = useState(""),
    [tab, setTab] = useState("Overview"),
    [busy, setBusy] = useState(false);
  const load = useCallback(async () => {
    const [record, timeline, hearings, documents, prosecutors] =
      await Promise.all([
        api(`/cases/${caseId}`),
        api(`/cases/${caseId}/timeline`),
        api(`/hearings?case_id=${caseId}`),
        api(`/cases/${caseId}/documents`),
        api("/prosecutors"),
      ]);
    setData({ record, timeline, hearings, documents, prosecutors });
  }, [caseId]);
  useEffect(() => {
    void Promise.resolve()
      .then(load)
      .catch((e) => setError(e.message));
  }, [load]);
  async function save(e, action) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const form = e.currentTarget,
      values = Object.fromEntries(new FormData(form));
    try {
      await action(values);
      await load();
      form.reset();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  if (!data)
    return (
      <>
        <button onClick={onBack}>← Cases</button>
        <ErrorBox error={error} />
        <p>Loading case…</p>
      </>
    );
  const c = data.record;
  return (
    <>
      <button className="text-button" onClick={onBack}>
        ← Back to cases
      </button>
      <div className="page-heading">
        <div>
          <p className="record-reference">{c.case_id}</p>
          <h1>{c.case_type}</h1>
          <p className="muted">
            {c.victim} · {c.district}, {c.state}
          </p>
        </div>
        <Badge value={c.status} />
      </div>
      <ErrorBox error={error} />
      <nav className="tabs" aria-label="Case sections">
        {[
          "Overview",
          "Hearings",
          "Timeline",
          "Documents",
          "Linked case",
        ].map((x) => (
          <button
            className={tab === x ? "selected" : ""}
            onClick={() => setTab(x)}
            key={x}
          >
            {x}
          </button>
        ))}
      </nav>
      {tab === "Overview" && (
        <div className="detail-grid">
          <section className="panel pad">
            <h2>Case information</h2>
            <dl>
              {[
                ["Stage", human(c.stage)],
                ["FIR", c.fir_number],
                ["FIR date", date(c.fir_date)],
                ["Police station", c.police_station],
                ["Court", c.court],
                ["Prosecutor", c.prosecutor],
                ["Legal officer", c.legal_officer],
                ["Next hearing", date(c.next_hearing)],
                ["Chargesheet", c.chargesheet_reference],
                ["Chargesheet date", date(c.chargesheet_date)],
              ].map(([k, v]) => (
                <div key={k}>
                  <dt>{k}</dt>
                  <dd>{v || "—"}</dd>
                </div>
              ))}
            </dl>
            <h3>Relevant Act / sections</h3>
            {c.sections.map((s) => (
              <p key={s.id}>
                {s.act} · {s.section}
              </p>
            ))}
            <form
              onSubmit={(e) =>
                save(e, (v) => post(`/cases/${caseId}/sections`, v))
              }
            >
              <label>
                Act
                <input name="act" required maxLength={200} />
              </label>
              <label>
                Section
                <input name="section" required maxLength={80} />
              </label>
              <button disabled={busy}>Add section</button>
            </form>
          </section>
          <section className="panel pad">
            <h2>Manage progress</h2>
            <form
              key={c.updated_at}
              onSubmit={(e) =>
                save(e, (v) =>
                  patch(`/cases/${caseId}`, {
                    ...v,
                    prosecutor_id: v.prosecutor_id || null,
                    chargesheet_date: v.chargesheet_date || null,
                    chargesheet_reference: v.chargesheet_reference || null,
                  }),
                )
              }
            >
              {Object.entries({
                status: ["OPEN", "CLOSED", "ON_HOLD"],
                investigation_status: ["PENDING", "IN_PROGRESS", "COMPLETED"],
                compensation_status: [
                  "NOT_APPLIED",
                  "PENDING",
                  "APPROVED",
                  "PAID",
                  "REJECTED",
                ],
                rehabilitation_status: [
                  "NOT_STARTED",
                  "PENDING",
                  "IN_PROGRESS",
                  "COMPLETED",
                ],
                protection_status: ["NONE", "REQUESTED", "ACTIVE", "RESOLVED"],
              }).map(([key, values]) => (
                <label key={key}>
                  {human(key)}
                  <select name={key} defaultValue={c[key]}>
                    {values.map((v) => (
                      <option key={v} value={v}>
                        {human(v)}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
              <label>
                Prosecutor
                <select
                  name="prosecutor_id"
                  defaultValue={c.prosecutor_id || ""}
                >
                  <option value="">Unassigned</option>
                  {data.prosecutors
                    .filter((p) => p.district_id === c.district_id)
                    .map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                </select>
              </label>
              <label>
                Court
                <input
                  name="court"
                  defaultValue={c.court || ""}
                  maxLength={160}
                />
              </label>
              <label>
                Chargesheet reference
                <input
                  name="chargesheet_reference"
                  defaultValue={c.chargesheet_reference || ""}
                  maxLength={160}
                />
              </label>
              <label>
                Chargesheet date
                <input
                  type="date"
                  name="chargesheet_date"
                  defaultValue={c.chargesheet_date || ""}
                />
              </label>
              <button className="primary" disabled={busy}>
                Save changes
              </button>
            </form>
          </section>
        </div>
      )}
      {tab === "Timeline" && (
        <div className="detail-grid">
          <section className="panel pad">
            <h2>Case timeline</h2>
            <ol className="timeline">
              {data.timeline.map((x) => (
                <li key={x.id}>
                  <small>{date(x.occurred_at)}</small>
                  <h3>{human(x.stage)}</h3>
                  <p>{x.description}</p>
                </li>
              ))}
            </ol>
          </section>
          <section className="panel pad">
            <h2>Record a milestone</h2>
            <form
              onSubmit={(e) =>
                save(e, (v) =>
                  post(`/cases/${caseId}/timeline`, {
                    ...v,
                    occurred_at: new Date(v.occurred_at).toISOString(),
                  }),
                )
              }
            >
              <label>
                Event type
                <input name="event_type" required maxLength={80} />
              </label>
              <label>
                Stage
                <input
                  name="stage"
                  required
                  maxLength={80}
                  placeholder="e.g. TRIAL"
                />
              </label>
              <label>
                Occurred at
                <input name="occurred_at" type="datetime-local" required />
              </label>
              <label>
                Description
                <textarea name="description" required maxLength={4000} />
              </label>
              <button className="primary" disabled={busy}>
                Add milestone
              </button>
            </form>
          </section>
        </div>
      )}
      {tab === "Hearings" && (
        <div className="detail-grid">
          <section className="panel pad">
            <h2>Hearings</h2>
            {data.hearings.map((x) => (
              <article className="list-item" key={x.id}>
                <Badge value={x.status} />
                <h3>{x.purpose}</h3>
                <p>{new Date(x.scheduled_at).toLocaleString()}</p>
                <p>{x.outcome}</p>
                {x.status === "SCHEDULED" && (
                  <form
                    onSubmit={(e) =>
                      save(e, (v) => patch(`/hearings/${x.id}`, v))
                    }
                  >
                    <label>
                      Outcome
                      <input name="outcome" maxLength={4000} />
                    </label>
                    <label>
                      Status
                      <select name="status">
                        <option>COMPLETED</option>
                        <option>CANCELLED</option>
                      </select>
                    </label>
                    <button disabled={busy}>Update hearing</button>
                  </form>
                )}
              </article>
            ))}
          </section>
          <section className="panel pad">
            <h2>Schedule a hearing</h2>
            <form
              onSubmit={(e) =>
                save(e, (v) =>
                  post(`/cases/${caseId}/hearings`, {
                    ...v,
                    scheduled_at: new Date(v.scheduled_at).toISOString(),
                  }),
                )
              }
            >
              <label>
                Date and time
                <input type="datetime-local" name="scheduled_at" required />
              </label>
              <label>
                Purpose
                <input name="purpose" required maxLength={200} />
              </label>
              <button className="primary" disabled={busy}>
                Schedule hearing
              </button>
            </form>
          </section>
        </div>
      )}
      {tab === "Documents" && (
        <section className="panel pad">
          <h2>Document register</h2>
          <p className="muted">
            Document references are recorded here. File upload and download are
            not enabled in this MVP.
          </p>
          {data.documents.map((x) => (
            <article className="list-item" key={x.id}>
              <strong>{x.name}</strong>
              <p>
                {x.document_type} · {date(x.created_at)}
              </p>
            </article>
          ))}
        </section>
      )}
      {tab === "Linked case" && (
        <section className="panel pad">
          <h2>Open a linked case</h2>
          <p className="muted">
            Create an additional case for {c.victim}. Your existing victim
            permission applies.
          </p>
          <form
            onSubmit={(e) =>
              save(e, async (values) => {
                await post("/cases", { ...values, victim_id: c.victim_id });
                onBack();
              })
            }
          >
            <label>
              Case ID
              <input name="case_id" required maxLength={60} />
            </label>
            <label>
              Case type
              <input name="case_type" required maxLength={100} />
            </label>
            <label>
              FIR number
              <input name="fir_number" maxLength={80} />
            </label>
            <label>
              Police station
              <input name="police_station" maxLength={160} />
            </label>
            <button className="primary" disabled={busy}>
              Create linked case
            </button>
          </form>
        </section>
      )}

    </>
  );
}
