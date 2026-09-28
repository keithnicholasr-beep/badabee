import { useState } from "react";
import { ErrorBox, Badge } from "../ui";
import { supportApi } from "./services";
import { Panel, ResourceState, useResource, RiskChart } from "./shared";
import { dateTime } from "./i18n";

export function Caseload({ t, lang, onSelect }) {
  const resource = useResource(supportApi.caseload, "caseload");
  const [search, setSearch] = useState(""),
    [risk, setRisk] = useState("");
  const rows = resource.data || [];
  const filtered = rows.filter(
    (r) =>
      r.name.toLowerCase().includes(search.toLowerCase()) &&
      (!risk || r.risk?.level === risk),
  );
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">COUNSELLOR WORKSPACE</p>
          <h1>Care starts with a conversation.</h1>
          <p>Review your assigned people and decide the next step.</p>
        </div>
        <button onClick={resource.reload}>{t("refresh")}</button>
      </div>
      <ResourceState resource={resource} t={t} />
      {resource.data && (
        <>
          <div className="support-metrics">
            {[
              ["Assigned victims", rows.length],
              [
                "High / critical risk",
                rows.filter((r) => ["HIGH", "CRITICAL"].includes(r.risk?.level))
                  .length,
              ],
              ["Due today (UTC)", rows.reduce((s, r) => s + r.due_today, 0)],
              ["Missed / overdue", rows.reduce((s, r) => s + r.missed, 0)],
              ["Escalated people", rows.filter((r) => r.escalated).length],
            ].map(([label, value]) => (
              <article className="panel metric" key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
              </article>
            ))}
          </div>
          <Panel title="Assigned people">
            <div className="support-filters">
              <label>
                Search by name
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search your caseload"
                />
              </label>
              <label>
                Risk level
                <select value={risk} onChange={(e) => setRisk(e.target.value)}>
                  <option value="">All levels</option>
                  {["LOW", "MODERATE", "HIGH", "CRITICAL"].map((x) => (
                    <option key={x}>{x}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="support-table-scroll">
              <table>
                <caption className="sr-only">
                  Assigned victims and their latest support information
                </caption>
                <thead>
                  <tr>
                    {[
                      "Victim",
                      "Risk",
                      "Trend",
                      "Last contact",
                      "Next follow-up",
                      "Case stage",
                    ].map((x) => (
                      <th scope="col" key={x}>
                        {x}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((r) => (
                    <tr key={r.id}>
                      <td>
                        <button
                          className="text-button"
                          onClick={() => onSelect(r.id)}
                        >
                          {r.name}
                        </button>
                        <small className="support-block">{r.district}</small>
                      </td>
                      <td>
                        <Badge value={r.risk?.level || "UNASSESSED"} />
                      </td>
                      <td>{r.risk?.trend || "—"}</td>
                      <td>{dateTime(r.last_contact, lang)}</td>
                      <td>{dateTime(r.next_followup, lang)}</td>
                      <td>{r.stage}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!filtered.length && <p>{t("empty")}</p>}
          </Panel>
        </>
      )}
    </>
  );
}

function CareActions({ data, profileId, t, reload }) {
  const ngos = useResource(
    () => supportApi.ngos(data.profile.id),
    data.profile.id,
  );
  const [kind, setKind] = useState("REVIEW"),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [message, setMessage] = useState("");
  async function run(task) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await task();
      setMessage("Saved.");
      reload();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Panel title="Schedule a follow-up">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            run(() =>
              supportApi.schedule({
                victim_id: data.profile.id,
                due_at: new Date(f.get("due")).toISOString(),
                note: f.get("note") || null,
              }),
            );
          }}
        >
          <label>
            Date and time (your local time)
            <input name="due" type="datetime-local" required />
          </label>
          <label>
            Private note (optional)
            <textarea name="note" maxLength="10000" />
          </label>
          <button className="primary" disabled={busy}>
            Schedule follow-up
          </button>
        </form>
      </Panel>
      <Panel title="Record a care action">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            run(() =>
              supportApi.action(data.profile.id, {
                kind,
                note: f.get("note"),
                ngo_id: kind === "REFERRAL" ? f.get("ngo") : null,
              }),
            );
          }}
        >
          <label>
            Action
            <select value={kind} onChange={(e) => setKind(e.target.value)}>
              {[
                ["REVIEW", "Mark reviewed"],
                ["ESCALATION", "Escalate for human review"],
                ["ALERT", "Create alert"],
                ["REFERRAL", "Refer to NGO"],
                ["INTERVENTION", "Record intervention"],
              ].map(([v, l]) => (
                <option value={v} key={v}>
                  {l}
                </option>
              ))}
            </select>
          </label>
          {kind === "REFERRAL" && (
            <>
              <ResourceState resource={ngos} t={t} />
              <label>
                Organization
                <select name="ngo" required defaultValue="">
                  <option value="" disabled>
                    Choose an organization
                  </option>
                  {ngos.data?.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.name}
                    </option>
                  ))}
                </select>
              </label>
              <p className="support-disclaimer">
                Records the referral only. Contact the organization separately;
                no message is sent.
              </p>
            </>
          )}
          <label>
            Reason / outcome
            <textarea name="note" required maxLength="4000" />
          </label>
          <button className="primary" disabled={busy}>
            Save care action
          </button>
        </form>
        <ErrorBox error={error} />
        <p role="status">{message}</p>
      </Panel>
      <Panel title="Follow-up schedule">
        {!data.followups.length && <p>No follow-ups scheduled.</p>}
        {data.followups.map((f) => (
          <article className="followup-card" key={f.id}>
            <div className="support-between">
              <strong>{dateTime(f.due_at)}</strong>
              <Badge value={f.status} />
            </div>
            {f.completed_at && (
              <p>Contact recorded: {dateTime(f.completed_at)}</p>
            )}
            {f.counsellor_id === profileId && (
              <>
                <div className="support-actions">
                  {["COMPLETED", "MISSED", "CANCELLED"]
                    .filter((s) => s !== f.status)
                    .map((s) => (
                      <button
                        disabled={busy}
                        key={s}
                        onClick={() =>
                          run(() => supportApi.updateFollowup(f.id, s))
                        }
                      >
                        {s === "COMPLETED"
                          ? "Record contact now"
                          : s === "MISSED"
                            ? "Mark missed"
                            : "Cancel"}
                      </button>
                    ))}
                </div>
                <details>
                  <summary>Add or edit private note</summary>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      const form = new FormData(e.currentTarget);
                      run(() => supportApi.note(f.id, form.get("note")));
                    }}
                  >
                    <label>
                      Your private note
                      <textarea
                        name="note"
                        required
                        maxLength="10000"
                        defaultValue={
                          data.notes.find((n) => n.followup_id === f.id)
                            ?.note || ""
                        }
                      />
                    </label>
                    <button disabled={busy}>Save note</button>
                  </form>
                </details>
              </>
            )}
          </article>
        ))}
      </Panel>
    </>
  );
}

export function VictimDetail({ victimId, profileId, t, lang, onBack }) {
  const resource = useResource(() => supportApi.profile(victimId), victimId);
  const [error, setError] = useState("");
  const data = resource.data,
    latest = data?.predictions[0];
  async function resolve(id) {
    try {
      await supportApi.resolve(id);
      resource.reload();
    } catch (e) {
      setError(e.message);
    }
  }
  return (
    <>
      <button onClick={onBack}>← {t("back")}</button>
      <ResourceState resource={resource} t={t} />
      {data && (
        <>
          <div className="page-heading">
            <div>
              <p className="eyebrow">ASSIGNED VICTIM PROFILE</p>
              <h1>{data.profile.name}</h1>
              <p>
                {data.profile.district} · {data.profile.state} ·{" "}
                {data.profile.language}
              </p>
            </div>
            <Badge value={latest?.level || "UNASSESSED"} />
          </div>
          <div className="support-grid">
            <Panel title="Latest distress assessment">
              {latest ? (
                <>
                  <div className="score-display">
                    {latest.score}
                    <small>/ 100</small>
                  </div>
                  <p>
                    {latest.trend} · {dateTime(latest.observed_at, lang)}
                  </p>
                  <ul>
                    {latest.factors.map((f, i) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                  <strong>{latest.recommended_action}</strong>
                  <p className="support-disclaimer">
                    {latest.model_version}.{" "}
                    {latest.model_version.startsWith("demo-")
                      ? "Unvalidated demo rules; confidence is not calibrated. A human must review the context."
                      : "Decision support only. Review the source and context before acting."}
                  </p>
                </>
              ) : (
                <p>No assessment recorded.</p>
              )}
            </Panel>
            <Panel title="Distress history">
              <RiskChart predictions={data.predictions} lang={lang} />
            </Panel>
          </div>
          <Panel title="Case context">
            {data.cases.map((c) => (
              <article className="case-summary" key={c.id}>
                <strong>
                  {c.case_id} · {c.case_type}
                </strong>
                <p>
                  {c.stage} · {c.status}
                </p>
                <p>Upcoming hearing: {dateTime(c.next_hearing, lang)}</p>
                <p>Legal officer: {c.legal_officer || "Not assigned"}</p>
              </article>
            ))}
            {!data.cases.length && <p>No case recorded.</p>}
          </Panel>
          <div className="support-grid">
            <div>
              <CareActions
                data={data}
                profileId={profileId}
                t={t}
                reload={resource.reload}
              />
            </div>
            <div>
              <Panel title="Previous private notes">
                {data.notes.map((n) => (
                  <article className="followup-card" key={n.id}>
                    <small>{dateTime(n.created_at, lang)}</small>
                    <p className="preserve-lines">{n.note}</p>
                  </article>
                ))}
                {!data.notes.length && <p>No notes authored by you yet.</p>}
              </Panel>
              <Panel title="Interventions, reviews & requests">
                <ErrorBox error={error} />
                {data.actions.map((a) => (
                  <article className="followup-card" key={a.id}>
                    <div className="support-between">
                      <Badge value={a.kind} />
                      <Badge value={a.status} />
                    </div>
                    <p className="preserve-lines">{a.note}</p>
                    {a.ngo && <p>Organization: {a.ngo}</p>}
                    <small>
                      {a.author} · {dateTime(a.created_at, lang)}
                    </small>
                    {a.status === "OPEN" && (
                      <div>
                        <button onClick={() => resolve(a.id)}>
                          Mark completed
                        </button>
                      </div>
                    )}
                  </article>
                ))}
                {!data.actions.length && <p>No care actions recorded yet.</p>}
              </Panel>
            </div>
          </div>
        </>
      )}
    </>
  );
}

export function CounsellorAlerts({ t, lang, onSelect }) {
  const resource = useResource(supportApi.alerts, "alerts");
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(null);
  async function acknowledge(id) {
    setBusy(id);
    try {
      await supportApi.acknowledge(id);
      resource.reload();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  }
  return (
    <Panel title="Support alerts">
      <p>
        Review the person's context before choosing an intervention.
        Acknowledgement records review of this alert only.
      </p>
      <ResourceState resource={resource} t={t} />
      <ErrorBox error={error} />
      {resource.data?.map((a) => (
        <article className="support-list-row" key={a.id}>
          <div>
            <Badge value={a.severity} />
            <h3>{a.message}</h3>
            <p>{dateTime(a.created_at, lang)}</p>
            <button onClick={() => onSelect(a.victim_id)}>
              Open victim profile
            </button>
          </div>
          {a.acknowledged_at ? (
            <span>Acknowledged</span>
          ) : (
            <button disabled={busy === a.id} onClick={() => acknowledge(a.id)}>
              Acknowledge
            </button>
          )}
        </article>
      ))}
      {resource.data?.length === 0 && <p>{t("empty")}</p>}
    </Panel>
  );
}
