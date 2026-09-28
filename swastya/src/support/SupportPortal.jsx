import { useEffect, useRef, useState } from "react";
import { supportApi } from "./services";
import { translator } from "./i18n";
import { Emergency, Notifications, ResourceState, useResource } from "./shared";
import { VictimHome, Checkin, Chat, Resources } from "./Victim";
import { Caseload, VictimDetail, CounsellorAlerts } from "./Counsellor";
import "./support.css";

function VictimPages({ me, page, t, lang, navigate }) {
  const resource = useResource(
    () => supportApi.profile(me.profile_id),
    me.profile_id,
  );
  return (
    <>
      <ResourceState resource={resource} t={t} />
      {resource.data && (
        <>
          {page === "home" && (
            <VictimHome
              data={resource.data}
              t={t}
              lang={lang}
              navigate={navigate}
              reload={resource.reload}
            />
          )}
          {page === "checkin" && (
            <Checkin t={t} lang={lang} onSaved={resource.reload} />
          )}
          {page === "chat" && <Chat t={t} lang={lang} />}
          {page === "resources" && <Resources victimId={me.profile_id} t={t} />}
          {page === "notifications" && <Notifications t={t} lang={lang} />}
        </>
      )}
    </>
  );
}

export default function SupportPortal({ user, onLogout }) {
  const isVictim = user.role === "VICTIM";
  const [page, setPage] = useState(isVictim ? "home" : "caseload"),
    [selected, setSelected] = useState(null);
  const [lang, setLang] = useState(
    () => sessionStorage.getItem("support-language") || "en",
  );
  const main = useRef(null),
    initial = useRef(true);
  const t = translator(lang);
  const resource = useResource(supportApi.me, user.id);
  const links = isVictim
    ? ["home", "checkin", "chat", "resources", "notifications"]
    : ["caseload", "alerts", "notifications"];
  useEffect(() => {
    document.documentElement.lang = lang;
    sessionStorage.setItem("support-language", lang);
    return () => {
      document.documentElement.lang = "en";
    };
  }, [lang]);
  useEffect(() => {
    if (initial.current) {
      initial.current = false;
      return;
    }
    main.current?.focus();
  }, [page, selected]);
  function navigate(next) {
    setSelected(null);
    setPage(next);
  }
  function select(id) {
    setPage("caseload");
    setSelected(id);
  }
  return (
    <div className="app-shell support-shell" lang={lang}>
      <a className="skip-link" href="#support-main">
        {t("skip")}
      </a>
      <aside className="sidebar">
        <a
          className="brand"
          href="#support-main"
          onClick={() => navigate(links[0])}
        >
          ✳ badabee
        </a>
        <p className="sidebar-label">
          {isVictim ? "YOUR SUPPORT SPACE" : "COUNSELLOR WORKSPACE"}
        </p>
        <nav aria-label="Support portal">
          {links.map((key, i) => (
            <button
              className={page === key ? "nav-link active" : "nav-link"}
              key={key}
              aria-current={page === key ? "page" : undefined}
              onClick={() => navigate(key)}
            >
              <span aria-hidden="true">{["◫", "◉", "◇", "◎", "▧"][i]}</span>
              {t(key)}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <p>{t("privacy")}</p>
          <button onClick={onLogout}>{t("logout")}</button>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div>
            <strong>{user.name}</strong>
            <small className="support-block">{t(page)}</small>
          </div>
          <div className="support-actions">
            <label className="language-label">
              <span className="sr-only">{t("language")}</span>
              <select value={lang} onChange={(e) => setLang(e.target.value)}>
                <option value="en">English</option>
                <option value="hi">हिन्दी</option>
                <option value="kn">ಕನ್ನಡ</option>
              </select>
            </label>
            {isVictim && resource.data && (
              <Emergency victimId={resource.data.profile_id} t={t} />
            )}
          </div>
        </header>
        <main
          id="support-main"
          className="content support-content"
          tabIndex="-1"
          ref={main}
        >
          <ResourceState resource={resource} t={t} />
          {resource.data &&
            (isVictim ? (
              <VictimPages
                me={resource.data}
                page={page}
                t={t}
                lang={lang}
                navigate={navigate}
              />
            ) : (
              <div lang="en">
                {selected ? (
                  <VictimDetail
                    victimId={selected}
                    profileId={resource.data.profile_id}
                    t={t}
                    lang={lang}
                    onBack={() => setSelected(null)}
                  />
                ) : page === "caseload" ? (
                  <Caseload t={t} lang={lang} onSelect={select} />
                ) : page === "alerts" ? (
                  <CounsellorAlerts t={t} lang={lang} onSelect={select} />
                ) : (
                  <Notifications t={t} lang={lang} />
                )}
              </div>
            ))}
        </main>
        <footer>{t("demo")}</footer>
      </div>
    </div>
  );
}
