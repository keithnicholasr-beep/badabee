import { useEffect, useState } from "react";
import { api, post, setToken } from "./api";
import { LegalDashboard, CaseDetail } from "./Legal";
import { AdminDashboard } from "./Admin";
import { Directory, Schemes, Alerts } from "./Resources";
import { ErrorBox } from "./ui";
import { human } from "./format";
import VictimDashboard from "./victim";
import "./App.css";
import Home from "./Home";
import Profile, { Avatar } from "./Profile";
import { useProfile } from "./useProfile";
function Login({ onLogin, onBack, notice }) {
  const [signup, setSignup] = useState(false);
  const [locations, setLocations] = useState([]);
  const [locationError, setLocationError] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api("/auth/registration-options").then(rows => { if (active) setLocations(rows); })
      .catch(err => { if (active) setLocationError(err.message); });
    return () => { active = false; };
  }, []);
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();

    const values = Object.fromEntries(new FormData(event.currentTarget));

    setError("");
    setBusy(true);

    try {
      if (signup) {
        if (values.password !== values.confirmation) throw new Error("Passwords do not match.");
        await post("/auth/register", {
          name: values.name, email: values.email, password: values.password,
          district_id: values.district_id, language: values.language,
        });
      }
      const result = await post("/auth/login", {
        email: values.email,
        password: values.password,
      });

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
    <div className="minimal-login-page">
      <div className="minimal-login-header">
        <button
          type="button"
          className="back-home-button"
          onClick={onBack}
        >
          ← Back to Home
        </button>

        <div className="minimal-brand">
          <div className="minimal-logo">S</div>

          <div>
            <strong>SWASTYA</strong>
            <span>Secure Portal</span>
          </div>
        </div>
      </div>

      <main className="minimal-login-main">
        <section className="minimal-login-card">
          <div className="login-card-header">
            <p className="section-tag">{signup ? "CREATE ACCOUNT" : "SECURE LOGIN"}</p>
            <h1>{signup ? "Create your account" : "Sign in"}</h1>
            <p>{signup ? "Register to access your personal support dashboard." : "Enter your registered credentials to continue."}</p>
          </div>

          <form key={String(signup)} onSubmit={submit}>
            {signup && <>
              <label>Full name<input name="name" autoComplete="name" required minLength={2} maxLength={120} /></label>
              <label>District<select name="district_id" required defaultValue=""><option value="" disabled>Select your district</option>{locations.map(item => <option key={item.district_id} value={item.district_id}>{item.district}, {item.state}</option>)}</select></label>
              <label>Preferred language<select name="language" defaultValue="English">{["English", "Hindi", "Tamil", "Kannada", "Telugu", "Malayalam", "Marathi", "Bengali"].map(value => <option key={value}>{value}</option>)}</select></label>
              <ErrorBox error={locationError} />
              {!locations.length && !locationError && <p role="status">Loading districts…</p>}
            </>}
            <label>
              Email address
              <input
                name="email"
                type="email"
                autoComplete="username"
                placeholder="Enter your email"
                required
              />
            </label>

            <label>
              Password
              <input
                name="password"
                type="password"
                autoComplete={signup ? "new-password" : "current-password"}
                minLength={signup ? 12 : 1}
                maxLength={256}
                placeholder="Enter your password"
                required
              />
            </label>

            {signup && <label>Confirm password<input name="confirmation" type="password" autoComplete="new-password" required minLength={12} maxLength={256} /><small>Use at least 12 characters.</small></label>}
            <ErrorBox error={error || notice} />

            <button
              className="login-submit-button"
              type="submit"
              disabled={busy || (signup && !locations.length)}
            >
              {busy ? (signup ? "Creating account…" : "Signing in…") : (signup ? "Create account" : "Login")}
            </button>
          </form>
          <button className="account-switch" type="button" disabled={busy} onClick={() => { setError(""); setSignup(value => !value); }}>{signup ? "Already registered? Sign in" : "New here? Create an account"}</button>
          {signup && <p className="registration-note">Public signup creates a victim account. Legal officers, counsellors and administrators receive staff accounts from the platform administrator.</p>}


        </section>
      </main>

      <div className="minimal-login-footer">
        SWASTYA
      </div>
    </div>
  );
}

function App() {
  const [user, setUser] = useState(null),
    [showLogin, setShowLogin] = useState(false),
    [page, setPage] = useState("Home"),
    [selectedCase, setSelectedCase] = useState(null),
    [notice, setNotice] = useState("");

  const profileProps = useProfile(user, setUser);

  function logout() {
    setToken(null);
    setUser(null);
    setShowLogin(false);
    setSelectedCase(null);
    setPage("Home");
  }

  useEffect(() => {
    function expired() {
      logout();
      setShowLogin(true);
      setNotice("Your session ended. Please sign in again.");
    }

    window.addEventListener("session-expired", expired);
    return () => window.removeEventListener("session-expired", expired);
  }, []);

  if (!user) {
    if (!showLogin) {
      return (
        <>
          <ErrorBox error={notice} />

          <Home
            onLoginClick={() => {
              setNotice("");
              setShowLogin(true);
            }}
          />
        </>
      );
    }

    return (
      <Login
        notice={notice}
        onBack={() => {
          setNotice("");
          setShowLogin(false);
        }}
        onLogin={(value) => {
          setNotice("");
          setShowLogin(false);
          setUser(value);
        }}
      />
    );
  }

  if (user.role === "VICTIM") {
    return (
      <VictimDashboard
        key={user.id}
        user={user}
        onLogout={logout}
        profileProps={profileProps}
      />
    );
  }
  const legal = user.role === "LEGAL_OFFICER",
    admin = user.role.endsWith("_ADMIN");
  const links = legal
    ? ["Home", "Overview", "Cases"]
    : admin ? ["Home", "Overview", ...(user.role !== "NATIONAL_ADMIN" ? ["Alerts"] : []), "NGO directory", "Government schemes"]
    : ["Home"];
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
            navigate("Home");
          }}
        >
          SWASTYA
        </a>
        <p className="sidebar-label">
          {legal ? "LEGAL WORKSPACE" : admin ? "ADMINISTRATION" : "COUNSELLOR WORKSPACE"}
        </p>
        <nav>
          {links.map((link, i) => (
            <button
              key={link}
              className={page === link ? "nav-link active" : "nav-link"}
              onClick={() => navigate(link)}
            >
              <span aria-hidden="true">{["⌂", "◫", "▤", "◎", "▧"][i]}</span>
              {link}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <button className="profile-nav" onClick={() => navigate("Profile")} aria-current={page === "Profile" ? "page" : undefined}><Avatar name={user.name} photo={profileProps.profile?.photo} /> My profile & settings</button>
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
        <main className={page === "Home" ? "dashboard-home-content" : "content"}>
          {page === "Home" ? <Home user={user} onLoginClick={() => navigate(user.role === "COUNSELLOR" ? "Profile" : "Overview")} /> : page === "Profile" ? <Profile {...profileProps} onLogout={logout} /> : selectedCase ? (
            <CaseDetail
              caseId={selectedCase}
              onBack={() => setSelectedCase(null)}
            />
          ) : admin && page === "NGO directory" ? (
            <Directory />
          ) : admin && page === "Government schemes" ? (
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
