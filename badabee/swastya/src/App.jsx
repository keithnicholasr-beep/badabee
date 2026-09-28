import { useEffect, useState } from "react";
import { api, post, setToken } from "./api";
import { LegalDashboard, CaseDetail } from "./Legal";
import { AdminDashboard } from "./Admin";
import { Directory, Schemes, Alerts } from "./Resources";
import { ErrorBox } from "./ui";
import { human } from "./format";
import "./App.css";
import SupportPortal from "./support/SupportPortal";

function Login({ onLogin }) {
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(e.currentTarget);
    try {
      const result = await post("/auth/login", Object.fromEntries(form));
      setToken(result.access_token);
      onLogin(await api("/auth/me"));
    } catch (err) {
      setError(err.message);
      setToken(null);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="login-layout">
      <section className="welcome">
        <div className="brand">✳ badabee</div>
        <div>
          <p className="eyebrow">SUPPORT. PROTECT. RESTORE.</p>
          <h1>
            A clearer path
            <br />
            to coordinated care.
          </h1>
          <p>
            Bring legal support, case progress, and public services together in
            one secure workspace.
          </p>
        </div>
        <small>Victim support & case coordination</small>
      </section>
      <main className="login-panel">
        <form onSubmit={submit}>
          <p className="eyebrow">YOUR SECURE WORKSPACE</p>
          <h2>Welcome back</h2>
          <p className="muted">Sign in with your assigned account.</p>
          <label>
            Email
            <input name="email" type="email" autoComplete="username" required />
          </label>
          <label>
            Password
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              required
            />
          </label>
          <ErrorBox error={error} />
          <button className="primary" disabled={busy}>
            {busy ? "Signing in…" : "Sign in →"}
          </button>
          <p className="muted small">
            Access follows your role and jurisdiction.
          </p>
        </form>
      </main>
    </div>
  );
}

function App() {
  const [user, setUser] = useState(null),
    [page, setPage] = useState("Overview"),
    [selectedCase, setSelectedCase] = useState(null),
    [notice, setNotice] = useState("");
  function logout() {
    setToken(null);
    setUser(null);
    setSelectedCase(null);
    setPage("Overview");
  }
  useEffect(() => {
    function expired() {
      logout();
      setNotice("Your session ended. Please sign in again.");
    }
    window.addEventListener("session-expired", expired);
    return () => window.removeEventListener("session-expired", expired);
  }, []);
  if (!user)
    return (
      <>
        <ErrorBox error={notice} />
        <Login
          onLogin={(value) => {
            setNotice("");
            setUser(value);
          }}
        />
      </>
    );
  if (user.role === "VICTIM" || user.role === "COUNSELLOR")
    return <SupportPortal user={user} onLogout={logout} />;
  const legal = user.role === "LEGAL_OFFICER",
    admin = user.role.endsWith("_ADMIN");
  if (!legal && !admin)
    return (
      <main className="unsupported">
        <h1>Signed in securely</h1>
        <p>
          Your {human(user.role)} account can use the shared API. Its dashboard
          is being developed separately.
        </p>
        <button onClick={logout}>Sign out</button>
      </main>
    );
  const links = legal
    ? ["Overview", "Cases", "NGO directory", "Government schemes"]
    : [
        "Overview",
        ...(user.role !== "NATIONAL_ADMIN" ? ["Alerts"] : []),
        "NGO directory",
        "Government schemes",
      ];
  function navigate(name) {
    setPage(name);
    setSelectedCase(null);
  }
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            navigate("Overview");
          }}
        >
          ✳ badabee
        </a>
        <p className="sidebar-label">
          {legal ? "LEGAL WORKSPACE" : "ADMINISTRATION"}
        </p>
        <nav>
          {links.map((link, i) => (
            <button
              key={link}
              className={page === link ? "nav-link active" : "nav-link"}
              onClick={() => navigate(link)}
            >
              <span aria-hidden="true">{["◫", "▤", "◎", "▧"][i]}</span>
              {link}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="secure-dot">● Secure access</div>
          <p>{human(user.role)}</p>
          <button onClick={logout}>Sign out</button>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span>
            Support coordination <span className="muted">/ {page}</span>
          </span>
          <div className="profile">
            <span className="avatar">
              {user.name
                .split(" ")
                .slice(0, 2)
                .map((s) => s[0])
                .join("")}
            </span>
            <div>
              <strong>{user.name}</strong>
              <small>{human(user.role)}</small>
            </div>
          </div>
        </header>
        <main className="content">
          {selectedCase ? (
            <CaseDetail
              caseId={selectedCase}
              onBack={() => setSelectedCase(null)}
            />
          ) : page === "NGO directory" ? (
            <Directory />
          ) : page === "Government schemes" ? (
            <Schemes />
          ) : page === "Alerts" ? (
            <Alerts />
          ) : legal ? (
            <LegalDashboard
              tableOnly={page === "Cases"}
              onSelect={setSelectedCase}
            />
          ) : (
            <AdminDashboard user={user} />
          )}
        </main>
        <footer>Sensitive information • Access is recorded</footer>
      </div>
    </div>
  );
}
export default App;
