import { useEffect, useRef, useState } from "react";
import { ErrorBox } from "../ui";
import { supportApi } from "./services";
import { dateTime } from "./i18n";

export function useResource(loader, key) {
  const [data, setData] = useState(null),
    [error, setError] = useState(""),
    [version, setVersion] = useState(0);
  const load = useRef(loader);
  const previousKey = useRef(key);
  load.current = loader;
  useEffect(() => {
    let active = true;
    if (previousKey.current !== key) {
      setData(null);
      previousKey.current = key;
    }
    setError("");
    load
      .current()
      .then((value) => {
        if (active) setData(value);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [key, version]);
  return { data, error, reload: () => setVersion((v) => v + 1) };
}
export function ResourceState({ resource, t }) {
  return resource.error ? (
    <div>
      <ErrorBox error={resource.error} />
      <button onClick={resource.reload}>{t("retry")}</button>
    </div>
  ) : !resource.data ? (
    <p role="status">{t("loading")}</p>
  ) : null;
}
export function Panel({ title, children, className = "" }) {
  return (
    <section className={`panel support-panel ${className}`}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}
export function Emergency({ victimId, t, onSaved }) {
  const dialog = useRef(null);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [saved, setSaved] = useState(false);
  async function submit() {
    setBusy(true);
    setError("");
    try {
      await supportApi.action(victimId, {
        kind: "EMERGENCY",
        note: "Victim requested urgent human support.",
      });
      setSaved(true);
      onSaved?.();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <button
        className="emergency-button"
        onClick={() => {
          setSaved(false);
          setError("");
          dialog.current.showModal();
        }}
      >
        {t("emergency")}
      </button>
      <dialog
        ref={dialog}
        className="support-dialog"
        aria-labelledby="emergency-title"
      >
        <h2 id="emergency-title">{t("emergency")}</h2>
        <p>{t("emergencyText")}</p>
        <a className="call-button" href="tel:112">
          {t("call")}
        </a>
        <ErrorBox error={error} />
        {saved && (
          <p role="status" className="success-note">
            {t("supportSaved")}
          </p>
        )}
        <div className="support-actions">
          <button className="primary" disabled={busy || saved} onClick={submit}>
            {busy ? t("saving") : t("recordEmergency")}
          </button>
          <button onClick={() => dialog.current.close()}>{t("close")}</button>
        </div>
      </dialog>
    </>
  );
}
export function RiskChart({ predictions, lang }) {
  const points = predictions.slice(0, 12).reverse();
  if (!points.length) return <p>No assessments recorded yet.</p>;
  const coordinates = points.map(
    (p, i) =>
      `${40 + (i * 520) / Math.max(1, points.length - 1)},${160 - p.score * 1.3}`,
  );
  return (
    <>
      <svg
        className="risk-chart"
        viewBox="0 0 600 190"
        role="img"
        aria-label="Distress scores, oldest to newest. Exact values available in the table below."
      >
        {[0, 50, 100].map((v) => (
          <g key={v}>
            <line
              x1="40"
              y1={160 - v * 1.3}
              x2="565"
              y2={160 - v * 1.3}
              stroke="currentColor"
              opacity=".15"
            />
            <text x="5" y={165 - v * 1.3} fontSize="12" fill="currentColor">
              {v}
            </text>
          </g>
        ))}
        <polyline
          points={coordinates.join(" ")}
          fill="none"
          stroke="#28664f"
          strokeWidth="3"
        />
        {points.map((p, i) => (
          <circle
            key={p.id}
            cx={coordinates[i].split(",")[0]}
            cy={coordinates[i].split(",")[1]}
            r="4"
            fill="#28664f"
          />
        ))}
        <text x="40" y="186" fontSize="12" fill="currentColor">
          Older
        </text>
        <text x="520" y="186" fontSize="12" fill="currentColor">
          Latest
        </text>
      </svg>
      <details>
        <summary>View exact scores · last {points.length} observations</summary>
        <div className="support-table-scroll">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Score</th>
                <th>Level</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {points.map((p) => (
                <tr key={p.id}>
                  <td>{dateTime(p.observed_at, lang)}</td>
                  <td>{p.score}</td>
                  <td>{p.level}</td>
                  <td>{p.model_version}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </>
  );
}
export function Notifications({ t, lang }) {
  const resource = useResource(supportApi.notifications, "notifications");
  const [error, setError] = useState("");
  async function read(id) {
    try {
      await supportApi.read(id);
      resource.reload();
    } catch (e) {
      setError(e.message);
    }
  }
  return (
    <Panel title={t("notifications")}>
      <ResourceState resource={resource} t={t} />
      <ErrorBox error={error} />
      {resource.data?.length === 0 && <p>{t("empty")}</p>}
      {resource.data?.map((n) => (
        <article className="support-list-row" key={n.id}>
          <div>
            <strong>{n.title}</strong>
            <p>{dateTime(n.created_at, lang)}</p>
          </div>
          {!n.read_at && (
            <button onClick={() => read(n.id)}>{t("unread")}</button>
          )}
        </article>
      ))}
    </Panel>
  );
}
