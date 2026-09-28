import { useEffect, useState } from "react";
import { api, post, setToken } from "./api";
import { LegalDashboard, CaseDetail } from "./Legal";
import { AdminDashboard } from "./Admin";
import { Directory, Schemes, Alerts } from "./Resources";
import { ErrorBox } from "./ui";
import { human } from "./format";
import VictimDashboard from "./victim";
import SupportPortal from "./support/SupportPortal";
import "./App.css";
function PublicHome({ onLoginClick }) {
  return (
    <div className="public-site">
      <div className="public-topbar">
        <div className="public-container">
          <span>SIH 2026 Prototype</span>

          <div className="public-accessibility">
            <span>Skip to Main Content</span>
            <span>A-</span>
            <span>A</span>
            <span>A+</span>
            <span>English</span>
          </div>
        </div>
      </div>

      <header className="public-header">
        <div className="public-container header-inner">
          <div className="public-logo">S</div>

          <div className="public-brand">
            <small>Integrated Citizen Support Platform</small>
            <h1>SWASTHYA</h1>
            <p>Victim Support & Case Coordination Platform</p>
          </div>

          <button
            className="header-login-button"
            onClick={onLoginClick}
          >
            Login
          </button>
        </div>
      </header>

      <div className="public-tricolour">
        <span />
        <span />
        <span />
      </div>

      <nav className="public-nav">
        <div className="public-container nav-inner">
          <a href="#home">Home</a>
          <a href="#services">Services</a>
          <a href="#features">Platform</a>
          <a href="#security">Security</a>
          <a href="#support">Support</a>
        </div>
      </nav>

      <main>
        <section className="hero" id="home">
          <div className="public-container hero-grid">
            <div>
              <p className="section-tag">
                INTEGRATED SUPPORT & COORDINATION
              </p>

              <h2>
                One secure platform for coordinated victim support.
              </h2>

              <p className="hero-description">
                SWASTHYA connects legal case coordination, support services,
                government schemes, NGO resources and administrative insights
                through a unified digital platform.
              </p>

              <div className="hero-actions">
                <button
                  className="main-login-button"
                  onClick={onLoginClick}
                >
                  Login to Portal
                </button>

                <a href="#services" className="secondary-link">
                  Explore Services
                </a>
              </div>
            </div>

            <div className="hero-info-card">
              <div className="info-card-title">
                Platform Services
              </div>

              <div className="quick-service">
                <span>01</span>
                <div>
                  <strong>Legal Case Management</strong>
                  <p>Cases, hearings, timelines and case progress.</p>
                </div>
              </div>

              <div className="quick-service">
                <span>02</span>
                <div>
                  <strong>Support Coordination</strong>
                  <p>
                    Alerts, follow-ups and coordinated assistance.
                  </p>
                </div>
              </div>

              <div className="quick-service">
                <span>03</span>
                <div>
                  <strong>Public Services</strong>
                  <p>
                    Government schemes and NGO support directory.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="services-section" id="services">
          <div className="public-container">
            <div className="section-heading">
              <p className="section-tag">SERVICES</p>
              <h2>Integrated support ecosystem</h2>
              <p>
                Different services work together while access remains
                restricted according to the user's role and jurisdiction.
              </p>
            </div>

            <div className="service-grid">
              <article className="service-card">
                <div className="service-number">01</div>
                <h3>Legal Support</h3>
                <p>
                  Track cases, FIR information, legal milestones,
                  hearings, prosecutors and case status.
                </p>
              </article>

              <article className="service-card">
                <div className="service-number">02</div>
                <h3>Case Coordination</h3>
                <p>
                  Maintain case timelines, protection requests,
                  compensation progress and rehabilitation status.
                </p>
              </article>

              <article className="service-card">
                <div className="service-number">03</div>
                <h3>Support Alerts</h3>
                <p>
                  Authorized support teams can review and acknowledge
                  operational alerts within their permitted scope.
                </p>
              </article>

              <article className="service-card">
                <div className="service-number">04</div>
                <h3>NGO Directory</h3>
                <p>
                  Search support organisations based on service,
                  language and location.
                </p>
              </article>

              <article className="service-card">
                <div className="service-number">05</div>
                <h3>Government Schemes</h3>
                <p>
                  View available schemes, benefits, eligibility rules,
                  application processes and required documents.
                </p>
              </article>

              <article className="service-card">
                <div className="service-number">06</div>
                <h3>Administrative Analytics</h3>
                <p>
                  District, state and national administrative views
                  provide aggregated operational insights.
                </p>
              </article>
            </div>
          </div>
        </section>

        <section className="platform-section" id="features">
          <div className="public-container platform-grid">
            <div>
              <p className="section-tag">SWASTHYA PLATFORM</p>

              <h2>Designed around coordinated assistance</h2>

              <p>
                SWASTHYA provides different interfaces for legal officers
                and administrative users while enforcing jurisdiction and
                role-based access through the backend.
              </p>
            </div>

            <div className="platform-list">
              <div>
                <strong>Role-based access</strong>
                <span>
                  Information is shown according to user permissions.
                </span>
              </div>

              <div>
                <strong>Jurisdiction controls</strong>
                <span>
                  Administrative information follows district, state
                  and national scopes.
                </span>
              </div>

              <div>
                <strong>Case visibility</strong>
                <span>
                  Legal officers only access cases permitted to them.
                </span>
              </div>

              <div>
                <strong>Secure activity</strong>
                <span>
                  Sensitive reads and actions are recorded by the
                  backend audit system.
                </span>
              </div>
            </div>
          </div>
        </section>

        <section className="security-section" id="security">
          <div className="public-container security-content">
            <div>
              <p className="section-tag">SECURITY & PRIVACY</p>
              <h2>Access controlled by design</h2>
            </div>

            <p>
              SWASTHYA uses authenticated access, jurisdiction controls,
              role checks, short-lived sessions and audit records to help
              protect sensitive support information.
            </p>
          </div>
        </section>

        <section className="portal-cta" id="support">
          <div className="public-container cta-inner">
            <div>
              <p className="section-tag">SECURE PORTAL</p>
              <h2>Already registered?</h2>
              <p>
                Sign in to access the services available for your role.
              </p>
            </div>

            <button
              className="main-login-button"
              onClick={onLoginClick}
            >
              Login to SWASTHYA
            </button>
          </div>
        </section>
      </main>

      <footer className="public-footer">
        <div className="public-container footer-grid">
          <div>
            <strong>SWASTHYA</strong>
            <p>
              Victim Support & Case Coordination Platform
            </p>
          </div>

          <div>
            <span>Privacy</span>
            <span>Accessibility</span>
            <span>Help</span>
            <span>Contact</span>
          </div>
        </div>

        <div className="public-container footer-bottom">
          Prototype developed for Smart India Hackathon 2026.
          Not an official Government of India production website.
        </div>
      </footer>
    </div>
  );
}

function Login({ onLogin, onBack }) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();

    const values = Object.fromEntries(new FormData(event.currentTarget));

    setError("");
    setBusy(true);

    try {
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
            <strong>SWASTHYA</strong>
            <span>Secure Portal</span>
          </div>
        </div>
      </div>

      <main className="minimal-login-main">
        <section className="minimal-login-card">
          <div className="login-card-header">
            <p className="section-tag">SECURE LOGIN</p>
            <h1>Sign in</h1>
            <p>Enter your registered credentials to continue.</p>
          </div>

          <form onSubmit={submit}>
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
                autoComplete="current-password"
                placeholder="Enter your password"
                required
              />
            </label>

            <ErrorBox error={error} />

            <button
              className="login-submit-button"
              type="submit"
              disabled={busy}
            >
              {busy ? "Signing in..." : "Login"}
            </button>
          </form>

          <div className="login-security-message">
            🔒 Secure role-based access
          </div>
        </section>
      </main>

      <div className="minimal-login-footer">
        SWASTHYA · SIH 2026 Prototype
      </div>
    </div>
  );
}

function App() {
  const [user, setUser] = useState(null),
    [showLogin, setShowLogin] = useState(false),
    [page, setPage] = useState("Overview"),
    [selectedCase, setSelectedCase] = useState(null),
    [notice, setNotice] = useState("");

  function logout() {
    setToken(null);
    setUser(null);
    setShowLogin(false);
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

  if (!user) {
    if (!showLogin) {
      return (
        <>
          <ErrorBox error={notice} />

          <PublicHome
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
      />
    );
  }
  if (user.role === "COUNSELLOR") {
    return <SupportPortal user={user} onLogout={logout} />;
  }
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
          SWASTYA
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
