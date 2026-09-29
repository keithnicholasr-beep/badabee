import SupportTeam from "./SupportTeam";
import Complaints, { ComplaintAssignments } from "./Complaints";
import SupportPages from "./SupportPages";
import SiteFooter from "./SiteFooter";
import DashboardHeader from "./DashboardHeader";
import { useEffect, useState } from "react";
import { api, post, setToken } from "./api";
import { LegalDashboard, CaseDetail } from "./Legal";
import { AdminDashboard } from "./Admin";
import { Directory, Schemes, Alerts } from "./Resources";
import { ErrorBox } from "./ui";
import VictimDashboard from "./victim";
import "./App.css";
import Home from "./Home";
import Profile from "./Profile";
import { useProfile } from "./useProfile";
import { Eye, EyeOff } from "lucide-react";
function Login({ onLogin, onBack, notice, initialSignup = false }) {
  const [signup, setSignup] = useState(initialSignup);
  const [locations, setLocations] = useState([]);
  const [locationError, setLocationError] = useState("");
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
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


          <div>
            <strong>SWASTYA</strong>

          </div>
        </div>
      </div>

      <main className="minimal-login-main">
        <section className="minimal-login-card">
          <div className="login-card-header">

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

              <div className="password-input-wrapper">
                <input
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete={signup ? "new-password" : "current-password"}
                  minLength={signup ? 12 : 1}
                  maxLength={256}
                  placeholder="Enter your password"
                  required
                />

                <button
                  type="button"
                  className="password-eye-button"
                  onClick={() => setShowPassword((value) => !value)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </label>
            {signup && (
              <label>
                Confirm password

                <div className="password-input-wrapper">
                  <input
                    name="confirmation"
                    type={showConfirmation ? "text" : "password"}
                    autoComplete="new-password"
                    required
                    minLength={12}
                    maxLength={256}
                    placeholder="Confirm your password"
                  />

                  <button
                    type="button"
                    className="password-eye-button"
                    onClick={() =>
                      setShowConfirmation((value) => !value)
                    }
                    aria-label={
                      showConfirmation
                        ? "Hide confirm password"
                        : "Show confirm password"
                    }
                  >
                    {showConfirmation ? (
                      <EyeOff size={20} />
                    ) : (
                      <Eye size={20} />
                    )}
                  </button>
                </div>

                <small>Use at least 12 characters.</small>
              </label>
            )}
            <ErrorBox error={error || notice} />

            <button
              className="login-submit-button"
              type="submit"
              disabled={busy || (signup && !locations.length)}
            >
              {busy ? (signup ? "Creating account…" : "Signing in…") : (signup ? "Create account" : "Login")}
            </button>
          </form>
          <button className="account-switch" type="button" disabled={busy} onClick={() => {
            setError("");
            setShowPassword(false);
            setShowConfirmation(false);
            setSignup((value) => !value);
          }} >{signup ? "Already registered? Sign in" : "New here? Create an account"}</button>
          {signup && <p className="registration-note">Public signup creates a victim account. Legal officers, counsellors, law enforcement officers and administrators receive staff accounts from the platform administrator.</p>}


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
  const [homeSection, setHomeSection] = useState(null);
  const [initialSignup, setInitialSignup] = useState(false);
  const [supportPage, setSupportPage] = useState(() => window.location.hash.slice(2));
  useEffect(() => {
    const changed = () => setSupportPage(window.location.hash.slice(2));
    window.addEventListener("hashchange", changed);
    return () => window.removeEventListener("hashchange", changed);
  }, []);
  const supportRoute = ["privacy", "accessibility", "help", "help/contact", "feedback"].includes(supportPage) ? supportPage : "";
  useEffect(() => {
    document.title = supportRoute ? `${supportRoute === "feedback" ? "Feedback" : supportRoute === "privacy" ? "Privacy policy" : supportRoute === "accessibility" ? "Accessibility" : "Help centre"} | SWASTYA` : "SWASTYA | Support coordination";
    window.scrollTo(0, 0);
  }, [supportRoute]);

  function logout() {
    setToken(null);
    setUser(null);
    setShowLogin(false);
    setInitialSignup(false);
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

  if (supportRoute) return <SupportPages page={supportRoute} user={user} profileProps={profileProps} />;

  if (!user) {
    if (!showLogin) {
      return (
        <>
          <ErrorBox error={notice} />

          <Home
            onSignupClick={() => { setNotice(""); setInitialSignup(true); setShowLogin(true); }}
            onLoginClick={() => {
              setNotice("");
              setInitialSignup(false);
              setShowLogin(true);
            }}
          />
        </>
      );
    }

    return (
      <Login
        initialSignup={initialSignup}
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
  const law = user.role === "LAW_ENFORCEMENT";
  const legal = user.role === "LEGAL_OFFICER",
    admin = user.role.endsWith("_ADMIN");
  const links = law ? ["Complaints & FIRs", "Clients"] : legal
    ? ["Overview", "Cases", "Clients"]
    : admin ? ["Overview", ...(user.role !== "NATIONAL_ADMIN" ? ["Alerts", "Complaint assignments"] : []), "NGO directory", "Government schemes"]
    : user.role === "COUNSELLOR" ? ["Clients"] : [];
  function navigate(name) {
    setPage(name);
    setSelectedCase(null);
  }
  return (
    <div className="app-shell">
<DashboardHeader onProfile={() => navigate("Profile")} profileActive={page === "Profile"} user={user} photo={profileProps.profile?.photo} onNavigate={id => { navigate("Home"); setHomeSection({ id }); }} />
      <aside className="sidebar">
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

          <button onClick={logout}>Sign out</button>
        </div>
      </aside>
      <div className="workspace">
        <main className={page === "Home" ? "dashboard-home-content" : "content"}>
          {page === "Home" ? <Home user={user} section={homeSection} onLoginClick={() => navigate(law ? "Complaints & FIRs" : user.role === "COUNSELLOR" ? "Clients" : "Overview")} /> : page === "Profile" ? <Profile {...profileProps} onLogout={logout} /> : page === "Clients" && ["LEGAL_OFFICER", "COUNSELLOR", "LAW_ENFORCEMENT"].includes(user.role) ? <SupportTeam user={user} /> : law ? <Complaints user={user} /> : page === "Complaint assignments" && admin ? <ComplaintAssignments /> : selectedCase ? (
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
        {page !== "Home" && <SiteFooter user={user} compact />}
      </div>
    </div>
  );
}

export default App;
