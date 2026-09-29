import { useEffect, useState } from "react";
import { api, post } from "./api";
import { ErrorBox } from "./ui";
import "./SupportTeam.css";

const roleNames = { VICTIM: "Victim", COUNSELLOR: "Counsellor", LEGAL_OFFICER: "Lawyer", LAW_ENFORCEMENT: "Law enforcement officer" };

function Contact({ person, onChat }) {
  return <article className="team-contact">
    <h3>{person.name}</h3><p className="muted">{roleNames[person.role]}</p>
    <dl><dt>Email</dt><dd><a href={`mailto:${person.email}`}>{person.email}</a></dd>
      <dt>Phone</dt><dd>{person.phone ? <a href={`tel:${person.phone.replace(/[^+\d]/g, "")}`}>{person.phone}</a> : "Not provided"}</dd></dl>
    <button type="button" onClick={() => onChat(person)}>Chat with {roleNames[person.role]?.toLowerCase()}</button>
  </article>;
}

export default function SupportTeam({ user }) {
  const [page, setPage] = useState(null), [error, setError] = useState("");
  const [search, setSearch] = useState(""), [query, setQuery] = useState(""), [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0), [selected, setSelected] = useState(null);
  const victim = user.role === "VICTIM";
  useEffect(() => {
    let active = true;
    api(`/communications/clients?search=${encodeURIComponent(query)}&offset=${offset}&limit=20`)
      .then(value => { if (active) { setPage(value); setError(""); } })
      .catch(e => { if (active) { setPage(null); setError(e.message); } });
    return () => { active = false; };
  }, [query, offset, revision]);
  function refresh() { setPage(null); setError(""); setRevision(x => x + 1); }
  if (selected) return <Conversation key={`${selected.victimId}-${selected.recipientId}`} {...selected} onBack={() => { setSelected(null); refresh(); }} />;
  function chat(client, person) { setSelected({ victimId: client.id, recipientId: person.id }); }
  return <section className="support-team">
    <div className="page-heading"><div><h1>{victim ? "My support team" : "Clients"}</h1>
      <p className="muted">{victim ? "Contact your assigned lawyer, counsellor and law enforcement officer." : "View your assigned victims and contact the other departments supporting them."}</p></div><button onClick={refresh}>Refresh</button></div>
    {!victim && <form className="team-search" onSubmit={e => { e.preventDefault(); setPage(null); setQuery(search); setOffset(0); setRevision(x => x + 1); }}><label>Find a client<input type="search" value={search} onChange={e => setSearch(e.target.value)} maxLength={120} placeholder="Search by name" /></label><button type="submit">Search</button></form>}
    <ErrorBox error={error} />
    {!page && !error && <p role="status">Loading support team…</p>}
    {page?.items.length === 0 && <div className="panel pad"><h2>{victim ? "Your support profile is not available" : "No clients found"}</h2><p>{victim ? "Ask your support administrator to check your linked victim profile." : "Clients appear when you have an active counsellor assignment, an assigned or permitted legal case, or an assigned complaint. Try another search or contact your administrator."}</p></div>}
    <div className="client-cards">{page?.items.map(client => <article className="panel pad client-card" key={client.id}>
      <div className="client-card-header">{client.photo ? <img className="profile-photo" src={client.photo} alt={`${client.name}'s profile`} /> : <span className="client-initials" aria-hidden="true">{client.name.split(/\s+/).slice(0, 2).map(x => x[0]).join("")}</span>}
        <div><h2>{client.name}</h2><p>{client.district} · Preferred language: {client.language}</p></div>
        {!victim && <button className="primary" onClick={() => chat(client, {id:client.user_id})}>Chat with victim</button>}
      </div>
      <h3>{victim ? "Your contacts" : "Other departments"}</h3>
      <div className="team-contacts">{client.contacts.map(person => <Contact key={person.id} person={person} onChat={p => chat(client, p)} />)}</div>
      {!client.contacts.length && <p className="muted">{victim ? "No support staff have been assigned yet. Your contacts will appear here after assignment." : "No other department is currently assigned to this victim."}</p>}
    </article>)}</div>
    {!victim && page && <div className="team-pagination"><button disabled={!offset} onClick={() => { setPage(null); setOffset(x => Math.max(0, x - 20)); }}>Previous</button><span>{page.total} clients · Page {offset / 20 + 1}</span><button disabled={offset + 20 >= page.total} onClick={() => { setPage(null); setOffset(x => x + 20); }}>Next</button></div>}
  </section>;
}

function Conversation({ victimId, recipientId, onBack }) {
  const [conversation, setConversation] = useState(null), [error, setError] = useState("");
  const [draft, setDraft] = useState(""), [busy, setBusy] = useState(false), [notice, setNotice] = useState("");
  const [offset, setOffset] = useState(0), [revision, setRevision] = useState(0);
  const path = `/communications/clients/${victimId}/messages/${recipientId}`;
  useEffect(() => {
    let active = true, loading = false;
    async function load() {
      if (loading) return;
      loading = true;
      try { const value = await api(`${path}?offset=${offset}&limit=50`); if (active) { setConversation(value); setError(""); } }
      catch (e) { if (active) { setConversation(null); setError(e.message); } }
      finally { loading = false; }
    }
    load();
    const timer = setInterval(() => { if (document.visibilityState === "visible") load(); }, 10000);
    return () => { active = false; clearInterval(timer); };
  }, [path, offset, revision]);
  async function send(event) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try { await post(path, {body:draft}); setDraft(""); setOffset(0); setRevision(x => x + 1); setNotice("Message sent."); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  return <section className="team-conversation"><div className="team-pagination"><button onClick={onBack}>← Back to support team</button><button disabled={busy} onClick={() => setRevision(x => x + 1)}>Refresh</button></div>
    <ErrorBox error={error} />{!conversation && !error && <p role="status">Loading conversation…</p>}
    {conversation && <><h1>Chat with {conversation.recipient_name}</h1><p>{roleNames[conversation.recipient_role]} · Regarding {conversation.victim_name}</p>
      <p className="muted">Only the two participants can read this conversation while their assignments remain valid. Messages refresh every 10 seconds. Share only information needed to coordinate support.</p>
      <section className="panel pad"><div className="team-pagination"><button disabled={conversation.messages.length < 50} onClick={() => setOffset(x => x + 50)}>Older messages</button><button disabled={!offset} onClick={() => setOffset(x => Math.max(0, x - 50))}>Newer messages</button></div>
        <div className="team-message-list" aria-label="Conversation">{[...conversation.messages].reverse().map(message => <article key={message.id} className={message.mine ? "team-message mine" : "team-message"}><strong>{message.mine ? "You" : message.sender_name}</strong><p>{message.body}</p><time dateTime={message.created_at}>{new Date(message.created_at).toLocaleString()}</time></article>)}{!conversation.messages.length && <p>No messages yet. Start the conversation below.</p>}</div>
        <form className="team-message-form" onSubmit={send}><label>Message<textarea value={draft} onChange={e => setDraft(e.target.value)} maxLength={4000} rows={4} required /></label><button className="primary" disabled={busy || !draft.trim()}>{busy ? "Sending…" : "Send message"}</button></form>
        {notice && <p role="status">{notice}</p>}
      </section></>}
  </section>;
}
