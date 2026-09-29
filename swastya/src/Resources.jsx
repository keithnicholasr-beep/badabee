import { useEffect, useState } from "react";
import { api, post } from "./api";
import { Badge, ErrorBox } from "./ui";
import { date } from "./format";

export function Directory({ victimId = "" }) {
  const [items, setItems] = useState(null),
    [error, setError] = useState(""),
    [service, setService] = useState(""),
    [victim, setVictim] = useState(victimId);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    api(
      victimId
        ? `/ngos/match?victim_id=${encodeURIComponent(victimId)}`
        : "/ngos",
    )
      .then(setItems)
      .catch((e) => setError(e.message));
  }, [victimId]);
  async function search(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const matchVictim = victimId || victim;
      const query = new URLSearchParams(
        matchVictim
          ? {
              victim_id: matchVictim,
              ...(service ? { required_service: service } : {}),
            }
          : service
            ? { service }
            : {},
      );
      setItems(await api(`${matchVictim ? "/ngos/match" : "/ngos"}?${query}`));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>

          <h1>NGO directory</h1>
          <p className="muted">Find the right support, closer to home.</p>
        </div>
      </div>
      <form className="filters" onSubmit={search}>
        <label>
          Required service
          <select value={service} onChange={(e) => setService(e.target.value)}>
            <option value="">All services</option>
            {[
              "counselling",
              "shelter",
              "legal aid",
              "women support",
              "SC/ST support",
              "medical support",
              "rehabilitation",
            ].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
        {!victimId && <label>
          Match a permitted victim (optional)
          <input
            value={victim}
            onChange={(e) => setVictim(e.target.value)}
            placeholder="Victim ID"
          />
        </label>}
        <button className="primary" disabled={busy}>
          {busy ? "Searching…" : "Find support"}
        </button>
      </form>
      <ErrorBox error={error} />
      {!items && !error && <p>Loading directory…</p>}
      <div className="cards">
        {items?.map((x) => (
          <article className="panel pad" key={x.id}>
            <p className="record-location">
              {x.district} · {x.state}
            </p>
            <h2>{x.name}</h2>
            <div className="tags">
              {x.services.map((s) => (
                <Badge key={s} value={s} />
              ))}
            </div>
            <p>{x.languages.join(" · ")}</p>
            <p>{x.availability}</p>
            <p>{x.phone}</p>
            {x.match_reasons && (
              <p className="match">
                {x.match_reasons.join(" · ") || "Alternative location"}
              </p>
            )}
          </article>
        ))}
      </div>
      {items?.length === 0 && (
        <p className="empty">No matching organizations.</p>
      )}
    </>
  );
}

export function Schemes() {
  const [items, setItems] = useState(null),
    [error, setError] = useState("");
  useEffect(() => {
    api("/schemes")
      .then(setItems)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <>
      <div className="page-heading">
        <div>

          <h1>Government schemes</h1>
          <p className="muted">
            Structured support options and application requirements.
          </p>
        </div>
      </div>
      <ErrorBox error={error} />
      {!items && !error && <p>Loading schemes…</p>}
      <div className="cards">
        {items?.map((x) => (
          <article className="panel pad" key={x.id}>
            {x.is_demo && <Badge value="DEMO SCHEME" />}
            <h2>{x.name}</h2>
            <p className="muted">
              {x.authority} · {x.applicability}
            </p>
            <p>{x.description}</p>
            <h3>Benefits</h3>
            <p>{x.benefits}</p>
            <h3>How to apply</h3>
            <p>{x.application_process}</p>
            <h3>Eligibility criteria</h3>
            {x.eligibility_criteria.map((r, i) => (
              <p key={i}>
                {r.field.replaceAll("_", " ")}{" "}
                {{ lte: "≤", gte: "≥", eq: "=", in: "in" }[r.operator] ||
                  r.operator}{" "}
                {String(r.value)}
              </p>
            ))}
            <h3>Required documents</h3>
            <p>{x.required_documents.join(", ") || "None listed"}</p>
            {!x.is_demo && /^https:\/\//.test(x.source_url) && (
              <a href={x.source_url} target="_blank" rel="noreferrer">
                Official source ↗
              </a>
            )}
          </article>
        ))}
      </div>
    </>
  );
}

export function Alerts() {
  const [items, setItems] = useState(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(null);
  useEffect(() => {
    api("/alerts")
      .then(setItems)
      .catch((e) => setError(e.message));
  }, []);
  async function acknowledge(id) {
    setBusy(id);
    setError("");
    try {
      await post(`/alerts/${id}/acknowledge`, {});
      setItems(await api("/alerts"));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>

          <h1>Alerts needing attention</h1>
          <p className="muted">
            Support review requests within your jurisdiction.
          </p>
        </div>
      </div>
      <ErrorBox error={error} />
      <section className="panel pad">
        {!items && !error && <p>Loading alerts…</p>}
        {items?.map((x) => (
          <article className="alert-item" key={x.id}>
            <Badge value={x.severity} />
            <div>
              <h3>{x.message}</h3>
              <p className="muted small">{date(x.created_at)}</p>
            </div>
            {x.acknowledged_at ? (
              <span>Acknowledged {date(x.acknowledged_at)}</span>
            ) : (
              <button
                disabled={busy === x.id}
                onClick={() => acknowledge(x.id)}
              >
                Acknowledge
              </button>
            )}
          </article>
        ))}
        {items?.length === 0 && <p>No alerts in this jurisdiction.</p>}
      </section>
    </>
  );
}
