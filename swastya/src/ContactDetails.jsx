export default function ContactDetails() {
  const email = import.meta.env.VITE_CONTACT_EMAIL?.trim();
  const phone = import.meta.env.VITE_CONTACT_PHONE?.trim();
  return <section className="footer-contact" aria-label="Contact details">
    <strong>Contact</strong>
    <dl><dt>Email</dt><dd>{email ? <a href={`mailto:${email}`}>{email}</a> : "Not configured"}</dd>
    <dt>Phone number</dt><dd>{phone ? <a href={`tel:${phone.replace(/[^+\d]/g, "")}`}>{phone}</a> : "Not configured"}</dd></dl>
  </section>;
}
