import { useEffect, useState } from "react";
import { api, post, setToken } from "./api";
import { LegalDashboard, CaseDetail } from "./Legal";
import { AdminDashboard } from "./Admin";
import { Directory, Schemes, Alerts } from "./Resources";
import { ErrorBox } from "./ui";
import { human } from "./format";
import "./App.css";

function Login({ onLogin }) {
  const [signup, setSignup] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [locations, setLocations] = useState([]);
  const [loadingLocations, setLoadingLocations] = useState(true);

  useEffect(() => {
    let active = true;

    api("/auth/registration-options")
      .then((data) => {
        if (active) setLocations(data);
      })
      .catch(() => {
        if (active) {
          setError("Could not load signup locations. Please refresh.");
        }
      })
      .finally(() => {
        if (active) setLoadingLocations(false);
      });

    return () => {
      active = false;
    };
  }, []);

  function switchMode() {
    setSignup(!signup);
    setError("");
    setMessage("");
  }

  async function submit(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form));

    setError("");
    setMessage("");

    if (signup && values.password !== values.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setBusy(true);

    try {
      if (signup) {
        await post("/auth/register", {
          name: values.name,
          email: values.email,
          password: values.password,
          district_id: values.district_id,
          language: values.language,
        });

        form.reset();
        setSignup(false);
        setMessage("Account created. You can now sign in.");
      } else {
        const result = await post("/auth/login", {
          email: values.email,
          password: values.password,
        });

        setToken(result.access_token);
        onLogin(await api("/auth/me"));
      }
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
            Bring legal support, case progress, and public services
            together in one secure workspace.
          </p>
        </div>

        <small>Victim support & case coordination</small>
      </section>

      <main className="login-panel">
        <form
          key={signup ? "signup" : "login"}
          onSubmit={submit}
        >
          <p className="eyebrow">YOUR SECURE WORKSPACE</p>

          <h2>{signup ? "Create an account" : "Welcome back"}</h2>

          <p className="muted">
            {signup
              ? "Register for a personal support account."
              : "Sign in with your email and password."}
          </p>

          {signup && (
            <label>
              Full name
              <input
                name="name"
                autoComplete="name"
                minLength={2}
                maxLength={120}
                required
              />
            </label>
          )}

          <label>
            Email
            <input
              name="email"
              type="email"
              autoComplete="username"
              maxLength={254}
              required
            />
          </label>

          <label>
            Password
            <input
              name="password"
              type="password"
              autoComplete={
                signup ? "new-password" : "current-password"
              }
              minLength={signup ? 12 : 1}
              maxLength={256}
              required
            />
          </label>

          {signup && (
            <>
              <p className="muted small">
                Use at least 12 characters.
              </p>

              <label>
                Confirm password
                <input
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  minLength={12}
                  maxLength={256}
                  required
                />
              </label>

              <label>
                District and state
                <select
                  name="district_id"
                  defaultValue=""
                  disabled={loadingLocations}
                  required
                >
                  <option value="" disabled>
                    {loadingLocations
                      ? "Loading locations…"
                      : "Select your district"}
                  </option>

                  {locations.map((item) => (
                    <option
                      key={item.district_id}
                      value={item.district_id}
                    >
                      {item.district}, {item.state}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Preferred language
                <input
                  name="language"
                  defaultValue="English"
                  maxLength={60}
                  required
                />
              </label>

              {!loadingLocations && locations.length === 0 && (
                <p role="alert">
                  Signup locations are not configured yet.
                </p>
              )}
            </>
          )}

          <ErrorBox error={error} />

          {message && <p role="status">{message}</p>}

          <button
            type="submit"
            className="primary"
            disabled={
              busy ||
              (signup &&
                (loadingLocations || locations.length === 0))
            }
          >
            {busy
              ? "Please wait…"
              : signup
                ? "Create account"
                : "Sign in →"}
          </button>

          <button
            type="button"
            onClick={switchMode}
            disabled={busy}
          >
            {signup
              ? "Already have an account? Sign in"
              : "New here? Create an account"}
          </button>
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
