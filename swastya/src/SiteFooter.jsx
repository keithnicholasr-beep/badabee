import ContactDetails from "./ContactDetails";
export default function SiteFooter({ compact = false, showBrand = false }) {
  return <footer className={compact ? 'site-footer compact-footer' : 'public-footer site-footer'}>
    <div className="public-container footer-grid">
      <div>{showBrand && <strong>SWASTYA</strong>}<p>Victim Support & Case Coordination Platform</p></div>
      <nav aria-label="Footer">
        <a href="#/privacy">Privacy</a>
        <a href="#/accessibility">Accessibility</a>
        <a href="#/help">Help</a>
        <a href="#/help/contact">Contact</a>
      </nav>
      <ContactDetails />
    </div>
    {!compact && <div className="public-container footer-bottom">Not an official Government of India production website.</div>}
  </footer>;
}
