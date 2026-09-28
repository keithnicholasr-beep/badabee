export default function Home({ onLoginClick, user }) {
  const restricted = ["LEGAL_OFFICER", "COUNSELLOR"].includes(user?.role);
  const action = user ? (user.role === "COUNSELLOR" ? "Open my profile" : "Open my dashboard") : "Login to Portal";
  return (
    <div className={user ? "public-site dashboard-home" : "public-site"}>


      {!user && <header className="public-header">
        <div className="public-container header-inner">
          <div className="public-logo">S</div>

          <div className="public-brand">
            <small>Integrated Citizen Support Platform</small>
            <h1>SWASTYA</h1>
            <p>Victim Support & Case Coordination Platform</p>
          </div>

          <button
            className="header-login-button"
            onClick={onLoginClick}
          >
            Login
          </button>
        </div>
      </header>}

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

      <div className="home-sections">
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
                {restricted ? "SWASTYA connects legal case coordination, wellbeing support and administrative insights through a unified digital platform." : "SWASTYA connects legal case coordination, support services, government schemes, NGO resources and administrative insights through a unified digital platform."}
              </p>

              <div className="hero-actions">
                <button
                  className="main-login-button"
                  onClick={onLoginClick}
                >
                  {action}
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

              {!restricted && (              <div className="quick-service">
                <span>03</span>
                <div>
                  <strong>Public Services</strong>
                  <p>
                    Government schemes and NGO support directory.
                  </p>
                </div>
              </div>)}
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

              {!restricted && (              <article className="service-card">
                <div className="service-number">04</div>
                <h3>NGO Directory</h3>
                <p>
                  Search support organisations based on service,
                  language and location.
                </p>
              </article>)}

              {!restricted && (              <article className="service-card">
                <div className="service-number">05</div>
                <h3>Government Schemes</h3>
                <p>
                  View available schemes, benefits, eligibility rules,
                  application processes and required documents.
                </p>
              </article>)}

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
              <p className="section-tag">SWASTYA PLATFORM</p>

              <h2>Designed around coordinated assistance</h2>

              <p>
                SWASTYA provides different interfaces for legal officers
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
              SWASTYA uses authenticated access, jurisdiction controls,
              role checks, short-lived sessions and audit records to help
              protect sensitive support information.
            </p>
          </div>
        </section>

        <section className="portal-cta" id="support">
          <div className="public-container cta-inner">
            <div>
              <p className="section-tag">SECURE PORTAL</p>
              <h2>{user ? "Your support workspace" : "Already registered?"}</h2>
              <p>
                {user ? "Use your workspace to access the services available for your role." : "Sign in to access the services available for your role."}
              </p>
            </div>

            <button
              className="main-login-button"
              onClick={onLoginClick}
            >
              {action}
            </button>
          </div>
        </section>
      </div>

      <footer className="public-footer">
        <div className="public-container footer-grid">
          <div>
            <strong>SWASTYA</strong>
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
          Not an official Government of India production website.
        </div>
      </footer>
    </div>
  );
}

