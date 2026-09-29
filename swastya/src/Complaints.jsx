import { useEffect, useState } from "react";
import { api, post, patch } from "./api";
import { Badge, ErrorBox } from "./ui";
import { human } from "./format";
import "./Complaints.css";

const today = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
const formValues = event => Object.fromEntries(new FormData(event.currentTarget));

export default function Complaints({ user }) {
  const [rows, setRows] = useState(null), [selected, setSelected] = useState(null);
  const [error, setError] = useState(""), [revision, setRevision] = useState(0), [offset, setOffset] = useState(0);
  const [creating, setCreating] = useState(false), [busy, setBusy] = useState(false);
  const victim = user.role === "VICTIM";
  useEffect(() => {
    let active = true;
    api(`/complaints?offset=${offset}&limit=20`).then(data => { if (active) setRows(data); }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [revision, offset]);
  async function create(event) {
    event.preventDefault(); const values = formValues(event);
    values.incident_date ||= null;
    setBusy(true); setError("");
    try { const row = await post("/complaints", values); setCreating(false); setSelected(row.id); setRevision(x => x + 1); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  if (selected) return <ComplaintDetail key={selected} id={selected} victim={victim} onBack={() => { setSelected(null); setRevision(x => x + 1); }} />;
  return <section className="complaints-workspace">
    <div className="page-heading"><div><h1>{victim ? "My complaints & FIRs" : "Law enforcement"}</h1><p className="muted">{victim ? "File a complaint, view its FIR record and speak with your assigned officer." : "Manage your assigned complaints, FIR registrations and victim conversations."}</p></div>
    <div className="complaint-actions"><button onClick={() => setRevision(x => x + 1)}>Refresh</button>{victim && <button className="primary" onClick={() => setCreating(x => !x)}>{creating ? "Cancel" : "File a complaint"}</button>}</div></div>
    <ErrorBox error={error} />
    {creating && <form className="panel pad complaint-form" onSubmit={create}><h2>File a complaint</h2>
      <p>Your complaint is routed to an available officer in your registered district. This platform does not replace emergency services or submit to an external police system.</p>
      <label>Subject<input name="subject" required minLength={3} maxLength={200} /></label>
      <label>What happened?<textarea name="description" rows={5} required minLength={10} maxLength={10000} /></label>
      <div className="settings-grid"><label>Incident location<input name="location" required minLength={2} maxLength={250} /></label><label>Incident date (optional)<input name="incident_date" type="date" max={today()} /></label></div>
      <button className="primary" disabled={busy}>{busy ? "Submitting…" : "Submit complaint"}</button>
    </form>}
    {!rows && !error && <p role="status">Loading complaints…</p>}
    {rows && !rows.length && <div className="panel pad"><h2>{victim ? "No complaints yet" : "No assigned complaints"}</h2><p>{victim ? "Use File a complaint to contact your district’s law enforcement team." : "Complaints assigned to your account will appear here. Your district administrator can assign queued complaints."}</p></div>}
    <div className="complaint-list">{rows?.map(row => <article className="panel pad" key={row.id}>
      <Badge value={row.status} /><h2>{row.subject}</h2>
      <p>{victim ? `Officer: ${row.officer_name || "Awaiting assignment"}` : `Victim: ${row.victim_name}`}</p>
      <p className="muted">{row.district} · {new Date(row.created_at).toLocaleDateString()}</p>
      <p>FIR: {row.fir ? `${row.fir.number} · ${row.fir.police_station}` : "Not registered"}</p>
      <button onClick={() => setSelected(row.id)}>Open complaint & messages</button>
    </article>)}</div>
    <div className="complaint-actions"><button disabled={offset === 0} onClick={() => setOffset(x => Math.max(0, x - 20))}>Previous</button><span>Page {offset / 20 + 1}</span><button disabled={!rows || rows.length < 20} onClick={() => setOffset(x => x + 20)}>Next</button></div>
  </section>;
}

function ComplaintDetail({ id, victim, onBack }) {
  const [row, setRow] = useState(null), [messages, setMessages] = useState([]), [offset, setOffset] = useState(0);
  const [error, setError] = useState(""), [busy, setBusy] = useState(false), [revision, setRevision] = useState(0), [notice, setNotice] = useState("");
  const [draft, setDraft] = useState("");
  useEffect(() => {
    let active = true;
    async function refresh() {
      try {
        const [detail, chat] = await Promise.all([api(`/complaints/${id}`), api(`/complaints/${id}/messages?offset=${offset}&limit=100`)]);
        if (active) { setRow(detail); setMessages(chat); setError(""); }
      } catch (e) { if (active) { setRow(null); setMessages([]); setError(e.message); } }
    }
    refresh();
    const timer = setInterval(() => { if (document.visibilityState === "visible") refresh(); }, 15000);
    return () => { active = false; clearInterval(timer); };
  }, [id, revision, offset]);
  async function mutate(action, success) {
    setBusy(true); setError(""); setNotice("");
    try { await action(); setNotice(success); setRevision(x => x + 1); return true; }
    catch (e) { setError(e.message); return false; } finally { setBusy(false); }
  }
  async function send(event) {
    event.preventDefault();
    if (await mutate(() => post(`/complaints/${id}/messages`, { body: draft }), "Message sent.")) { setDraft(""); setOffset(0); }
  }
  async function register(event) {
    event.preventDefault(); const values = formValues(event);
    await mutate(() => post(`/complaints/${id}/fir`, values), "FIR recorded. The victim can now view it in their dashboard.");
  }
  return <section className="complaints-workspace">
    <div className="complaint-actions"><button onClick={onBack}>← All complaints</button><button disabled={busy} onClick={() => setRevision(x => x + 1)}>Refresh</button></div>
    <ErrorBox error={error} />{notice && <p role="status" className="settings-success">{notice}</p>}
    {!row && !error && <p role="status">Loading complaint…</p>}
    {row && <><div className="page-heading"><div><h1>{row.subject}</h1><Badge value={row.status} /></div></div>
    <div className="complaint-detail-grid"><div>
      <section className="panel pad"><h2>Complaint details</h2><p className="preserve-lines">{row.description}</p><dl className="complaint-facts">
        <dt>Victim</dt><dd>{row.victim_name}</dd><dt>Location</dt><dd>{row.location}, {row.district}</dd><dt>Incident date</dt><dd>{row.incident_date || "Not provided"}</dd>
        <dt>Assigned officer</dt><dd>{row.officer_name || "Awaiting assignment"}</dd><dt>Police station</dt><dd>{row.police_station || "Not assigned"}</dd>
        <dt>Complaint reference</dt><dd>{row.id}</dd></dl>
        {!row.officer_id && <p>An administrator will assign an officer. Messaging becomes available after assignment.</p>}
        {!victim && row.status !== "CLOSED" && <div className="complaint-actions">{row.status === "SUBMITTED" && <button disabled={busy} onClick={() => mutate(() => patch(`/complaints/${id}/status`, { status: "IN_REVIEW" }), "Complaint marked in review.")}>Start review</button>}
          <button disabled={busy} onClick={() => { if (window.confirm("Close this complaint? Its message thread will become read-only.")) mutate(() => patch(`/complaints/${id}/status`, { status: "CLOSED" }), "Complaint closed."); }}>Close complaint</button></div>}
      </section>
      <section className="panel pad"><h2>FIR registration</h2>{row.fir ? <dl className="complaint-facts"><dt>FIR number</dt><dd>{row.fir.number}</dd><dt>Police station</dt><dd>{row.fir.police_station}</dd><dt>Registered on</dt><dd>{row.fir.registered_on}</dd></dl> : <p>No FIR has been recorded for this complaint.</p>}
      {!victim && !row.fir && row.status !== "CLOSED" && <form className="complaint-form" onSubmit={register}>
        <p>Record the issued FIR details. Saving here makes them visible to the victim; it does not register an FIR in an external police system.</p>
        <label>FIR number<input name="number" required maxLength={80} /></label><label>Registering police station<input name="police_station" required minLength={2} maxLength={160} defaultValue={row.police_station || ""} /></label>
        <label>Registration date<input name="registered_on" type="date" required min={row.incident_date || undefined} max={today()} /></label>
        <button className="primary" disabled={busy}>Save FIR registration</button></form>}
      </section>
    </div><section className="panel pad complaint-chat"><h2>{victim ? "Message your officer" : "Victim conversation"}</h2><p className="muted">Visible to this victim and the currently assigned officer. Updates every 15 seconds.</p>
      <div className="message-list" aria-label="Conversation">{[...messages].reverse().map(m => <article key={m.id} className={m.mine ? "message mine" : "message"}><strong>{m.mine ? "You" : m.sender_name}</strong><p className="preserve-lines">{m.body}</p><time dateTime={m.created_at}>{new Date(m.created_at).toLocaleString()}</time></article>)}{!messages.length && <p>No messages on this page.</p>}</div>
      <div className="complaint-actions"><button disabled={messages.length < 100} onClick={() => setOffset(x => x + 100)}>Older messages</button><button disabled={!offset} onClick={() => setOffset(x => Math.max(0, x - 100))}>Newer messages</button></div>
      {row.status === "CLOSED" ? <p>This conversation is read-only because the complaint is closed.</p> : <form onSubmit={send} className="complaint-form"><label>Message<textarea value={draft} onChange={e => setDraft(e.target.value)} maxLength={4000} required rows={4} disabled={!row.officer_id} /></label><button className="primary" disabled={busy || !row.officer_id || !draft.trim()}>Send message</button></form>}
    </section></div></>}
  </section>;
}

export function ComplaintAssignments() {
  const [rows, setRows] = useState(null), [officers, setOfficers] = useState([]), [error, setError] = useState(""), [busy, setBusy] = useState(false), [revision, setRevision] = useState(0);
  const [offset, setOffset] = useState(0);
  useEffect(() => {
    let active = true;
    Promise.all([api(`/complaints/assignment-queue?offset=${offset}&limit=50`), api("/complaints/officers")]).then(([a, b]) => { if (active) { setRows(a); setOfficers(b); setError(""); } }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [revision, offset]);
  async function assign(event, id) {
    event.preventDefault(); const values = formValues(event); setBusy(true); setError("");
    try { await post(`/complaints/${id}/assign`, values); setRevision(x => x + 1); } catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  return <section><div className="page-heading"><div><h1>Complaint assignments</h1><p>Assign or transfer open complaints to an active officer in the same district. Complaint narratives and conversations remain private.</p></div><button onClick={() => setRevision(x => x + 1)}>Refresh</button></div><ErrorBox error={error} />
    {!rows && !error && <p role="status">Loading assignments…</p>}{rows?.length === 0 && <p>No open complaints in your jurisdiction.</p>}
    <div className="complaint-list">{rows?.map(row => <form key={`${row.id}-${row.officer_id}`} className="panel pad complaint-form" onSubmit={e => assign(e, row.id)}><h2>{row.district}</h2><p className="record-reference">Reference: {row.id}</p><p>{human(row.status)} · {new Date(row.created_at).toLocaleDateString()}</p><label>Assigned officer<select name="officer_id" required defaultValue={row.officer_id || ""}><option value="" disabled>Choose an officer</option>{officers.filter(o => o.district_id === row.district_id).map(o => <option key={o.id} value={o.id}>{o.name} · {o.police_station}</option>)}</select></label><button disabled={busy}>Save assignment</button></form>)}</div>
    <div className="complaint-actions"><button disabled={!offset} onClick={() => setOffset(x => Math.max(0, x - 50))}>Previous</button><span>Page {offset / 50 + 1}</span><button disabled={!rows || rows.length < 50} onClick={() => setOffset(x => x + 50)}>Next</button></div>
  </section>;
}
