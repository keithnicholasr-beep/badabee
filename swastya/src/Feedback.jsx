import { useState } from "react";

export default function Feedback({ user }) {
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [notice, setNotice] = useState("");
  const configuredEmail = (import.meta.env.VITE_FEEDBACK_EMAIL || "sreehari.m@btech.christuniversity.in").trim();
  const email = /^[^\s@?&#]+@[^\s@?&#]+\.[^\s@?&#]+$/.test(configuredEmail) ? configuredEmail : "";

  if (user?.role !== "VICTIM") return <section><h1>Feedback</h1><p>Feedback is available from a signed-in victim dashboard.</p><a href="#">Back to {user ? "workspace" : "home"}</a></section>;

  function openEmail(event) {
    event.preventDefault();
    if (!email || !subject.trim() || !message.trim()) return;
    window.location.href = `mailto:${email}?subject=${encodeURIComponent(`SWASTYA feedback: ${subject.trim()}`)}&body=${encodeURIComponent(message.trim())}`;
    setNotice("Continue in your email app to review and send your feedback. If no app opens, copy your message into an email addressed to the administrator below.");
  }

  return <section className="feedback-page">
    <h1>Feedback</h1>
    <p>Share suggestions or tell the administrator about your experience with SWASTYA.</p>
    <p className="muted">This opens a draft in your email app. You review and send the email there. Avoid including passwords or unnecessary personal, case or health details.</p>
    {email ? <p>Administrator email: <a href={`mailto:${email}`}>{email}</a></p> : <p role="status" className="panel pad">The administrator’s feedback email has not been configured yet. Email feedback will be available once the address is added.</p>}
    <form className="panel pad feedback-form" onSubmit={openEmail}>
      <label>Subject<input value={subject} onChange={event => setSubject(event.target.value)} required maxLength={120} autoComplete="off" /></label>
      <label>Your feedback<textarea value={message} onChange={event => setMessage(event.target.value)} rows={8} required maxLength={1500} /></label>
      <button className="primary" type="submit" disabled={!email || !subject.trim() || !message.trim()}>Open email draft</button>
    </form>
    {notice && <p role="status">{notice}</p>}
  </section>;
}
