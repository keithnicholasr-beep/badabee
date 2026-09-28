import { useEffect, useState } from "react";
import { api } from "./api";
import { Badge, ErrorBox } from "./ui";
import { human, date } from "./format";
import { Directory } from "./Resources";
import { Checkin, Chat } from "./support/Victim";
import { Emergency, Notifications, Panel, ResourceState, useResource } from "./support/shared";
import { supportApi } from "./support/services";
import { dateTime, translator } from "./support/i18n";
import "./support/support.css";

export default function VictimDashboard({ user, onLogout }) {
  const [page, setPage] = useState("Overview");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  const [lang, setLang] = useState("en");
  const [requestBusy, setRequestBusy] = useState(false);
  const [requestMessage, setRequestMessage] = useState("");
  const [requestError, setRequestError] = useState("");
  const t = translator(lang);
  const support = useResource(
    () => user.victim_id ? supportApi.profile(user.victim_id) : Promise.resolve({}),
    user.victim_id,
  );

  useEffect(() => {
    document.documentElement.lang = lang;
    return () => { document.documentElement.lang = "en"; };
  }, [lang]);

  async function requestSupport() {
    setRequestBusy(true);
    setRequestError("");
    try {
      await supportApi.action(user.victim_id, {
        kind: "SUPPORT",
        note: "Victim requested a counsellor follow-up.",
      });
      setRequestMessage(t("supportSaved"));
      support.reload();
    } catch (err) {
      setRequestError(err.message);
    } finally {
      setRequestBusy(false);
    }
  }

  useEffect(() => {
    if (!user.victim_id) return;

    let active = true;
    const victimId = encodeURIComponent(user.victim_id);

    Promise.all([
      api(`/victims/${victimId}/case`),
      api(`/victims/${victimId}/followups`),
      api(`/victims/${victimId}/eligible-schemes`),
    ])
      .then(([cases, followups, schemes]) => {
        if (active) {
          setData({ cases, followups, schemes });
        }
      })
      .catch((err) => {
        if (active) setError(err.message);
      });

    return () => {
      active = false;
    };
  }, [user.victim_id, reload]);

  function refresh() {
    setError("");
    setData(null);
    setReload((value) => value + 1);
    support.reload();
  }

  const pages = [
    ["Overview", "Overview"],
    ["My cases", "My cases"],
    ["Follow-ups", "Follow-ups"],
    ["Schemes", "Schemes"],
    ["Find support", "Find support"],
    ["checkin", t("checkin")],
    ["chat", t("chat")],
    ["notifications", t("notifications")],
  ];

  const pendingFollowups =
    data?.followups.filter((item) => item.status === "PENDING") ?? [];

  const upcomingFollowups = pendingFollowups
    .filter((item) => new Date(item.due_at) >= new Date())
    .sort((a, b) => new Date(a.due_at) - new Date(b.due_at));

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">SWASTYA</div>
        <p className="sidebar-label">YOUR SUPPORT SPACE</p>

        <nav aria-label="Victim dashboard">
          {pages.map(([id, label]) => (
            <button
              key={id}
              className={
                page === id ? "nav-link active" : "nav-link"
              }
              onClick={() => setPage(id)}
            >
              {label}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <p>{user.name}</p>
          <button onClick={onLogout}>Sign out</button>
        </div>
      </aside>

      <div className="workspace">
        <main className="content">
          <div className="page-heading">
            <div>
              <p className="eyebrow">YOUR SUPPORT SPACE</p>
              <h1>Welcome, {user.name}</h1>
              <p className="muted">
                View your case progress and available support.
              </p>
            </div>

            <div className="support-actions">
              <label>
                {t("language")}{" "}
                <select value={lang} onChange={(event) => setLang(event.target.value)}>
                  <option value="en">English</option>
                  <option value="hi">हिन्दी</option>
                  <option value="kn">ಕನ್ನಡ</option>
                </select>
              </label>
              {user.victim_id && <Emergency victimId={user.victim_id} t={t} onSaved={support.reload} />}
              {user.victim_id && <button onClick={refresh}>{t("refresh")}</button>}
            </div>
          </div>

          {!user.victim_id ? (
            <section className="panel pad">
              <h2>Your profile needs attention</h2>
              <p>
                Your account does not have a linked victim profile.
                Please contact your support administrator.
              </p>
            </section>
          ) : (
            <>
              <ErrorBox error={error} />

              {!data && !error && (
                <p role="status">Loading your dashboard…</p>
              )}

              {error && (
                <button onClick={refresh}>Try again</button>
              )}

              {data && page === "Overview" && (
                <>
                  <div className="metrics">
                    <article className="metric">
                      <span>My cases</span>
                      <strong>{data.cases.length}</strong>
                    </article>

                    <article className="metric">
                      <span>Pending follow-ups</span>
                      <strong>{pendingFollowups.length}</strong>
                    </article>

                    <article className="metric">
                      <span>Potentially eligible schemes</span>
                      <strong>
                        {
                          data.schemes.filter(
                            (item) =>
                              item.eligibility ===
                              "POTENTIALLY_ELIGIBLE"
                          ).length
                        }
                      </strong>
                    </article>
                  </div>

                  <section className="panel pad">
                    <h2>Your next follow-up</h2>

                    {upcomingFollowups.length > 0 ? (
                      <p>
                        {new Date(
                          upcomingFollowups[0].due_at
                        ).toLocaleString()}
                      </p>
                    ) : (
                      <p className="muted">
                        No upcoming follow-up is scheduled.
                      </p>
                    )}
                  </section>

                  <section className="panel pad victim-section">
                    <h2>Getting started</h2>
                    <p>
                      Your cases and appointments will appear here
                      when your support team creates them.
                    </p>
                    <button onClick={() => setPage("Find support")}>
                      Explore support organizations
                    </button>
                  </section>
                  <Panel title={t("care")}>
                    <ResourceState resource={support} t={t} />
                    {support.data && (
                      <>
                        <p>{t(support.data.wellbeing === "EXTRA_SUPPORT" ? "wellbeingExtra" : support.data.wellbeing === "CHECK_IN" ? "wellbeingNew" : "wellbeingRecorded")}</p>
                        <p>{t("lastCheckin")}: {dateTime(support.data.last_checkin, lang)}</p>
                        <p>{t("nextCheckin")}: {dateTime(support.data.next_checkin, lang)}</p>
                        {support.data.counsellors?.length ? support.data.counsellors.map((person) => (
                          <p key={person.id}>{t("counsellor")}: {person.name} · {person.specialization}</p>
                        )) : <p>{t("noAssignment")}</p>}
                        <ErrorBox error={requestError} />
                        {requestMessage && <p role="status">{requestMessage}</p>}
                        <div className="support-actions">
                          <button onClick={() => setPage("checkin")}>{t("begin")}</button>
                          <button disabled={requestBusy} onClick={requestSupport}>{requestBusy ? t("saving") : t("request")}</button>
                        </div>
                      </>
                    )}
                  </Panel>
                </>
              )}

              {data && page === "My cases" && (
                <section className="panel pad">
                  <h2>My cases</h2>

                  {data.cases.length === 0 ? (
                    <p className="muted">
                      No cases have been linked to your account yet.
                    </p>
                  ) : (
                    data.cases.map((item) => (
                      <article className="list-item" key={item.id}>
                        <Badge value={item.status} />
                        <h3>{item.case_id}</h3>
                        <p>{item.case_type}</p>
                        <p>Current stage: {human(item.stage)}</p>
                        <p>
                          Legal officer:{" "}
                          {item.legal_officer || "Not assigned yet"}
                        </p>
                        <p>
                          Next hearing: {date(item.next_hearing)}
                        </p>
                        <p>
                          Compensation:{" "}
                          {human(item.compensation_status)}
                        </p>
                        <p>
                          Rehabilitation:{" "}
                          {human(item.rehabilitation_status)}
                        </p>
                        <p>
                          Protection: {human(item.protection_status)}
                        </p>
                      </article>
                    ))
                  )}
                </section>
              )}

              {data && page === "Follow-ups" && (
                <section className="panel pad">
                  <h2>My follow-ups</h2>

                  {data.followups.length === 0 ? (
                    <p className="muted">
                      No follow-ups have been scheduled yet.
                    </p>
                  ) : (
                    data.followups.map((item) => (
                      <article className="list-item" key={item.id}>
                        <Badge value={item.status} />
                        <h3>
                          {new Date(item.due_at).toLocaleString()}
                        </h3>
                        <p>Support follow-up</p>
                      </article>
                    ))
                  )}
                </section>
              )}

              {data && page === "Schemes" && (
                <section className="panel pad">
                  <h2>Support schemes</h2>
                  <p className="muted">
                    These are preliminary rule checks, not approval
                    decisions.
                  </p>

                  {data.schemes.length === 0 ? (
                    <p>No schemes are currently listed for your state.</p>
                  ) : (
                    data.schemes.map((item) => (
                      <article className="list-item" key={item.id}>
                        {item.is_demo && (
                          <Badge value="DEMO SCHEME" />
                        )}
                        <h3>{item.name}</h3>
                        <Badge value={item.eligibility} />
                        <p>{item.description}</p>
                        <p>Benefits: {item.benefits}</p>
                        <p>How to apply: {item.application_process}</p>
                        <p>
                          Required documents:{" "}
                          {item.required_documents.join(", ") ||
                            "Not listed"}
                        </p>
                      </article>
                    ))
                  )}
                </section>
              )}

              {page === "Find support" && (
                <Directory victimId={user.victim_id} />
              )}
              {page === "checkin" && <Checkin t={t} lang={lang} onSaved={refresh} />}
              {page === "chat" && <Chat t={t} lang={lang} />}
              {page === "notifications" && <Notifications t={t} lang={lang} />}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
