import { useRef, useState } from "react";
import { ErrorBox, Badge } from "../ui";
import { supportApi } from "./services";
import { Panel, ResourceState, useResource } from "./shared";
import { dateTime } from "./i18n";

export function VictimHome({ data, t, lang, navigate, reload }) {
  const [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [error, setError] = useState("");
  const next = data.followups
    .filter((f) => f.status === "PENDING")
    .sort((a, b) => new Date(a.due_at) - new Date(b.due_at))[0];
  async function request() {
    setBusy(true);
    setError("");
    try {
      await supportApi.action(data.profile.id, {
        kind: "SUPPORT",
        note: "Victim requested a counsellor follow-up.",
      });
      setMessage(t("supportSaved"));
      reload();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <section className="care-hero">
        <div>
          <p className="eyebrow">BADABEE · {data.profile.name}</p>
          <h1>{t("welcome")}</h1>
          <p>{t("intro")}</p>
          <button className="primary" onClick={() => navigate("checkin")}>
            {t("begin")} →
          </button>
        </div>
        <div className="care-mark" aria-hidden="true">
          ✳
        </div>
      </section>
      <div className="wellbeing-note">
        <span aria-hidden="true">✦</span>
        <p>
          {t(
            data.wellbeing === "EXTRA_SUPPORT"
              ? "wellbeingExtra"
              : data.wellbeing === "CHECK_IN"
                ? "wellbeingNew"
                : "wellbeingRecorded",
          )}
        </p>
      </div>
      <div className="support-grid three">
        <Panel title={t("nextFollowup")}>
          <strong>{dateTime(next?.due_at, lang)}</strong>
        </Panel>
        <Panel title={t("lastCheckin")}>
          <strong>{dateTime(data.last_checkin, lang)}</strong>
        </Panel>
        <Panel title={t("nextCheckin")}>
          <strong>{dateTime(data.next_checkin, lang)}</strong>
        </Panel>
      </div>
      <div className="support-grid">
        <Panel title={t("case")}>
          {!data.cases.length && <p>{t("noCase")}</p>}
          {data.cases.map((c) => (
            <article className="case-summary" key={c.id}>
              <div className="support-between">
                <strong>{c.case_id}</strong>
                <Badge value={c.stage} />
              </div>
              <p>{c.case_type}</p>
              <dl>
                <dt>{t("hearing")}</dt>
                <dd>{dateTime(c.next_hearing, lang)}</dd>
                <dt>{t("legal")}</dt>
                <dd>{c.legal_officer || t("noAssignment")}</dd>
              </dl>
            </article>
          ))}
        </Panel>
        <Panel title={t("care")}>
          {!data.counsellors.length && <p>{t("noAssignment")}</p>}
          {data.counsellors.map((c) => (
            <article className="support-person" key={c.id}>
              <span className="avatar">{c.name.slice(0, 1)}</span>
              <div>
                <strong>{c.name}</strong>
                <p>
                  {t("counsellor")} · {c.specialization}
                </p>
              </div>
            </article>
          ))}
          <button disabled={busy} onClick={request}>
            {busy ? t("saving") : t("request")}
          </button>
          <ErrorBox error={error} />
          <p role="status">{message}</p>
        </Panel>
      </div>
      <Panel title={t("requests")}>
        {!data.actions.length && <p>{t("empty")}</p>}
        {data.actions.map((a) => (
          <div className="support-list-row" key={a.id}>
            <div>
              <strong>{a.kind}</strong>
              <p>{dateTime(a.created_at, lang)}</p>
            </div>
            <Badge value={a.status} />
          </div>
        ))}
      </Panel>
    </>
  );
}

export function Checkin({ t, lang, onSaved }) {
  const [values, setValues] = useState({ mood: 3, stress: 3, sleep: 3 });
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [saved, setSaved] = useState(false);
  const requestId = useRef(crypto.randomUUID());
  async function submit(e) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setBusy(true);
    setError("");
    try {
      await supportApi.checkin({
        request_id: requestId.current,
        ...values,
        text: form.get("text"),
        feels_unsafe: form.has("unsafe"),
        language: lang,
      });
      setSaved(true);
      onSaved();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  if (saved)
    return (
      <Panel title={t("saved")}>
        <p role="status">{t("wellbeingRecorded")}</p>
        <p>{t("demo")}</p>
      </Panel>
    );
  return (
    <Panel title={t("checkin")}>
      <p>{t("checkinIntro")}</p>
      <form className="checkin-form" onSubmit={submit}>
        {["mood", "stress", "sleep"].map((key) => (
          <label key={key} htmlFor={`checkin-${key}`}>
            <span className="support-between">
              {t(key)}
              <output htmlFor={`checkin-${key}`}>{values[key]} / 5</output>
            </span>
            <input
              id={`checkin-${key}`}
              type="range"
              min="1"
              max="5"
              value={values[key]}
              onChange={(e) =>
                setValues({ ...values, [key]: Number(e.target.value) })
              }
              aria-describedby={`${key}-hint`}
            />
            <small id={`${key}-hint`}>
              {t(key === "stress" ? "stressScale" : "lowHigh")}
            </small>
          </label>
        ))}
        <label className="check-label">
          <input name="unsafe" type="checkbox" />
          {t("unsafe")}
        </label>
        <label>
          {t("share")}
          <textarea name="text" rows="4" maxLength="4000" />
        </label>
        <label className="check-label">
          <input type="checkbox" required />
          {t("consent")}
        </label>
        <ErrorBox error={error} />
        <button className="primary" disabled={busy}>
          {busy ? t("saving") : t("submit")}
        </button>
        <p className="support-disclaimer">{t("demo")}</p>
      </form>
    </Panel>
  );
}

export function Chat({ t, lang }) {
  const history = useResource(supportApi.chatHistory, "chat");
  const [messages, setMessages] = useState([]),
    [text, setText] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const pending = useRef(null);
  async function send(message, intent) {
    if (!message.trim() || busy) return;
    setBusy(true);
    setError("");
    if (
      !pending.current ||
      pending.current.message !== message ||
      pending.current.language !== lang
    )
      pending.current = {
        request_id: crypto.randomUUID(),
        message,
        language: lang,
        intent,
      };
    try {
      const reply = await supportApi.chat(pending.current);
      setMessages((old) => [...old.filter((x) => x.id !== reply.id), reply]);
      setText("");
      pending.current = null;
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  const shortcuts = [
    ["hearing", "hearingQuestion"],
    ["counsellor", "counsellorQuestion"],
    ["schemes", "schemesQuestion"],
    ["stage", "stageQuestion"],
    ["safety", "helpQuestion"],
  ];
  return (
    <Panel title={t("chat")}>
      <p>{t("chatbotIntro")}</p>
      <div className="chat-shortcuts">
        {shortcuts.map(([intent, key]) => (
          <button
            key={intent}
            disabled={busy || !history.data}
            onClick={() => send(t(key), intent)}
          >
            {t(key)}
          </button>
        ))}
      </div>
      <ResourceState resource={history} t={t} />
      <div
        className="chat-log"
        role="log"
        aria-label={t("chat")}
        aria-live="polite"
      >
        {[...(history.data || []), ...messages].map((m) => (
          <div key={m.id}>
            <div className="chat-message from-user">
              <strong>{t("you")}</strong>
              <p>{m.message}</p>
            </div>
            <div className="chat-message from-assistant" lang={m.language}>
              <strong>{t("assistant")}</strong>
              <p>{m.reply}</p>
            </div>
          </div>
        ))}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(text);
        }}
      >
        <label>
          {t("message")}
          <textarea
            value={text}
            maxLength="2000"
            required
            rows="2"
            onChange={(e) => setText(e.target.value)}
          />
        </label>
        <ErrorBox error={error} />
        <button className="primary" disabled={busy || !history.data}>
          {busy ? t("sending") : t("send")}
        </button>
      </form>
    </Panel>
  );
}

export function Resources({ victimId, t }) {
  const resource = useResource(
    () =>
      Promise.all([supportApi.ngos(victimId), supportApi.schemes(victimId)]),
    victimId,
  );
  return (
    <>
      <ResourceState resource={resource} t={t} />
      {resource.data && (
        <>
          <p className="support-disclaimer">{t("demoDirectory")}</p>
          <Panel title={t("ngos")}>
            <div className="support-grid">
              {resource.data[0].map((n) => (
                <article className="resource-card" key={n.id}>
                  <h3>{n.name}</h3>
                  <p>
                    {n.district} · {n.state}
                  </p>
                  <p>{n.services.join(" · ")}</p>
                  <p>{n.languages.join(" · ")}</p>
                  <p>{n.availability}</p>
                  <p>{n.phone}</p>
                </article>
              ))}
            </div>
            {!resource.data[0].length && <p>{t("empty")}</p>}
          </Panel>
          <Panel title={t("schemes")}>
            <div className="support-grid">
              {resource.data[1].map((s) => (
                <article className="resource-card" key={s.id}>
                  <h3>{s.name}</h3>
                  {s.is_demo && (
                    <p className="support-disclaimer">{t("demoScheme")}</p>
                  )}
                  <Badge value={s.eligibility} />
                  <p>{s.description}</p>
                  <p>{s.benefits}</p>
                  <p>{s.application_process}</p>
                  <p>{s.required_documents.join(" · ")}</p>
                  {!s.is_demo && s.source_url.startsWith("https://") && (
                    <a href={s.source_url} target="_blank" rel="noreferrer">
                      {t("source")}
                    </a>
                  )}
                </article>
              ))}
            </div>
            {!resource.data[1].length && <p>{t("empty")}</p>}
          </Panel>
        </>
      )}
    </>
  );
}
