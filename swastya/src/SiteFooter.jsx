import ContactDetails from "./ContactDetails";
export default function SiteFooter({ compact = false, showBrand = false, user }) {
  return <footer className={compact ? 'site-footer compact-footer' : 'public-footer site-footer'}>
    <div className="public-container footer-grid">
      <div>{showBrand && <strong>SWASTYA</strong>}<p>Victim Support & Case Coordination Platform</p></div>
      <div className="footer-support-group"><nav aria-label="Footer">
        <a href="#/privacy">Privacy</a>
        <a href="#/accessibility">Accessibility</a>
        <a href="#/help">Help</a>
        {user?.role === "VICTIM" && <a href="#/feedback">Feedback</a>}
      </nav>
      <ContactDetails /></div>
    </div>
    {!compact && <div className="public-container footer-bottom">Not an official Government of India production website.</div>}
  </footer>;
}
