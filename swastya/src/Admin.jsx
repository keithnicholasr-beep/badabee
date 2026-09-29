import { useEffect, useState } from "react";
import { api } from "./api";
import { ErrorBox } from "./ui";
import { human } from "./format";

function Bars({ title, values }) {
  const maximum = Math.max(1, ...Object.values(values));
  return (
    <section className="panel pad">
      <h2>{title}</h2>
      <div className="bars">
        {Object.entries(values).map(([key, value]) => (
          <div key={key}>
            <div className="bar-label">
              <span>{human(key)}</span>
              <strong>{value}</strong>
            </div>
            <div className="bar-track">
              <div style={{ width: `${(value / maximum) * 100}%` }} />
            </div>
          </div>
        ))}
        {!Object.keys(values).length && (
          <p className="muted">No data for this jurisdiction.</p>
        )}
      </div>
    </section>
  );
}

export function AdminDashboard({ user }) {
  const [locations, setLocations] = useState([]),
    [state, setState] = useState(""),
    [district, setDistrict] = useState("");
  const [data, setData] = useState(null),
    [error, setError] = useState("");
  useEffect(() => {
    api("/jurisdictions")
      .then(setLocations)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    let active = true;
    const level = user.role.split("_")[0].toLowerCase();
    const query = new URLSearchParams();
    if (state) query.set("state_id", state);
    if (district) query.set("district_id", district);
    api(`/analytics/${level}?${query}`)
      .then((result) => active && setData(result))
      .catch((e) => active && setError(e.message));
    return () => {
      active = false;
    };
  }, [state, district, user.role]);
  const states = [
    ...new Map(locations.map((x) => [x.state_id, x.state])).entries(),
  ];
  return (
    <>
      <div className="page-heading">
        <div>

          <h1>Support at a glance</h1>
          <p className="muted">
            A shared view of progress, risk, and service needs.
          </p>
        </div>
        <span className="date-pill">Aggregated insights</span>
      </div>
      <div className="filters">
        {user.role === "NATIONAL_ADMIN" && (
          <label>
            State
            <select
              value={state}
              onChange={(e) => {
                setData(null);
                setError("");
                setState(e.target.value);
                setDistrict("");
              }}
            >
              <option value="">All states</option>
              {states.map(([id, name]) => (
                <option key={id} value={id}>
                  {name}
                </option>
              ))}
            </select>
          </label>
        )}
        {user.role !== "DISTRICT_ADMIN" && (
          <label>
            District
            <select
              value={district}
              onChange={(e) => {
                setData(null);
                setError("");
                setDistrict(e.target.value);
              }}
            >
              <option value="">All districts</option>
              {locations
                .filter((x) => !state || state === x.state_id)
                .map((x) => (
                  <option key={x.district_id} value={x.district_id}>
                    {x.district}
                  </option>
                ))}
            </select>
          </label>
        )}
      </div>
      <ErrorBox error={error} />
      {!data && !error && <p role="status">Loading insights…</p>}
      {data && (
        <>
          <div className="metrics admin-metrics">
            {[
              "cases_monitored",
              "high_risk_cases",
              "critical_alerts",
              "followups_pending",
              "average_case_age_days",
            ].map((key) => (
              <article className="metric" key={key}>
                <span>{human(key)}</span>
                <strong>{data[key]}</strong>
                <small>
                  {key === "high_risk_cases"
                    ? "Latest high / critical observation"
                    : "Within selected jurisdiction"}
                </small>
              </article>
            ))}
          </div>
          <div className="detail-grid">
            <Bars title="Case categories" values={data.case_categories} />
            <Bars title="Case stages" values={data.case_stages} />
            <Bars
              title="Compensation progress"
              values={data.compensation_status}
            />
            <Bars
              title="Rehabilitation progress"
              values={data.rehabilitation_status}
            />
          </div>
          <section className="panel pad trend-panel">
            <h2>Distress trends</h2>
            <p className="muted small">
              Monthly mean of recorded scores; observations are not diagnoses.
            </p>
            <div className="trend-chart">
              {data.distress_trends.map((x) => (
                <div className="trend-column" key={x.month}>
                  <strong>{x.average_score}</strong>
                  <div
                    className="trend-bar"
                    style={{ height: `${x.average_score * 1.6}px` }}
                  />
                  <span>{x.month}</span>
                  <small>{x.observations} records</small>
                </div>
              ))}
            </div>
            {!data.distress_trends.length && <p>No observations available.</p>}
          </section>
        </>
      )}
    </>
  );
}
