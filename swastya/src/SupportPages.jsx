import ContactDetails from "./ContactDetails";
import { useState } from 'react';
import { patch } from './api';
import { ErrorBox } from './ui';
import SiteFooter from './SiteFooter';
import { defaultPreferences } from './preferences';
import './SupportPages.css';

const articles = [
  ['Cases & support', 'How do I file a complaint and speak to an officer?', 'Open Complaints & FIRs in the victim dashboard and choose File a complaint. An available officer in your registered district is assigned automatically. If none is available, the complaint waits for administrator assignment. Open the complaint to message your assigned officer and view any FIR details they record. Messages refresh every 15 seconds. This does not submit an FIR to an external police system.'],
  ['Cases & support', 'Who can read my complaint messages?', 'Only you and the currently assigned law enforcement officer can read the conversation. District and state administrators manage assignments without accessing the narrative or messages. Law enforcement officers cannot read counselling notes or clinical records.'],
  ['Getting started', 'What is SWASTYA?', 'SWASTYA brings case progress, legal coordination, support follow-ups and public-service information into one website. The services you can open depend on your account role and permitted records.'],
  ['Getting started', 'How do I create an account?', 'Choose Sign up in the homepage header, enter your name, email, district, preferred language and a password of at least 12 characters, then confirm your password. Public signup creates a victim account. Legal officers, counsellors, law enforcement officers and administrators receive accounts from the platform administrator.'],
  ['Getting started', 'Is SWASTYA an official government website?', 'No. SWASTYA is not an official Government of India production website. Scheme information should be checked against the official source before you apply.'],
  ['Account & security', 'Why can’t I sign in?', 'Check your email and password. Incorrect credentials display an error on the login screen. Repeated attempts may temporarily be limited; wait a minute before retrying. If the problem continues, contact the administrator who manages your installation.'],
  ['Account & security', 'How do I change my name, email or password?', 'Open My Profile at the top right. Edit your details and save. Changing your email requires your current password. Changing your password signs out existing sessions; sign in again with your new password.'],
  ['Account & security', 'What if I have forgotten my password?', 'Ask your platform administrator to help restore access. An automated email-based password-reset service is not currently available. Never send your password to another person.'],
  ['Account & security', 'How do I add or remove a profile picture?', 'Open My Profile and use Add picture, Change picture or Remove picture. PNG and JPEG images up to 2 MB and 16 megapixels are accepted. Images are resized and embedded metadata is removed before storage.'],
  ['Cases & support', 'Why are there no cases or follow-ups in my dashboard?', 'Your account must have a linked victim profile, and your support team must create or assign the relevant records. A new account may have no records yet. Ask your assigned support team if something is missing.'],
  ['Cases & support', 'Who can see my case information?', 'Access follows roles, assignments and jurisdiction. Victims see their own records; legal officers see assigned or permitted cases; counsellors work with assigned victims. Administrative reporting is scoped to district, state or national access.'],
  ['Cases & support', 'Can my lawyer see counselling notes?', 'Counselling notes are separate from legal case information. Legal officers do not automatically receive access to private counselling notes.'],
  ['Cases & support', 'What is available for counsellors?', 'Counsellor accounts can access the shared homepage and My Profile. The full clinical dashboard is still being developed; assigned-victim and follow-up functionality exists in the backend.'],
  ['Services & schemes', 'How does Find support match NGOs?', 'For victims, matching uses their location and can consider required service and language. Select a service and choose Find support. Contact the organisation directly to confirm availability and suitability.'],
  ['Services & schemes', 'Does scheme eligibility mean I have been approved?', 'No. Eligibility results are preliminary rule checks. The responsible authority determines approval. Verify requirements, documents and application steps with the official source. Records marked as demo schemes are examples.'],
  ['Services & schemes', 'Why are NGOs and schemes missing from my lawyer or counsellor dashboard?', 'Those sections are not shown in lawyer or counsellor dashboards. Victims can use their support directory and scheme views; administrators have directory access.'],
  ['Accessibility', 'How do I change theme, text size or contrast?', 'Use Accessibility in the footer to choose device, light or dark theme, increase text size, enable high contrast or reduce motion. Signed-in settings save to your account. Before login, settings save only in this browser.'],
  ['Accessibility', 'Will changing language translate the website?', 'The language setting records your preferred communication language. The interface is currently available in English; choosing another language does not translate every page.'],
  ['Accessibility', 'Can I navigate using the keyboard?', 'Use Tab and Shift+Tab to move through links and controls, Enter to follow links or submit buttons, and Space or Enter to expand FAQ questions. You can also use browser zoom to enlarge content.'],
  ['Contact & help', 'How do I report a problem or incorrect record?', 'Contact the administrator or support team that provided your SWASTYA access. Include the page, what you expected and the error message. Do not include your password or unnecessary personal, legal or health information. See Contact for this installation’s email and phone details. A ticket service is not currently available.'],
  ['Contact & help', 'Can I use this site to get urgent assistance?', 'SWASTYA is not an emergency-response channel. For immediate danger or urgent medical assistance, contact your local emergency services or an appropriate professional directly.'],
];

function FAQ({ contact }) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState(contact ? 'Contact & help' : 'All topics');
  const categories = ['All topics', ...new Set(articles.map(x => x[0]))];
  const filtered = articles.filter(([topic, question, answer]) => (category === 'All topics' || topic === category) && `${topic} ${question} ${answer}`.toLowerCase().includes(query.trim().toLowerCase()));
  return <>
    <h1>How can we help?</h1>{contact && <ContactDetails />}
    <p className="muted">Find answers about your account, support services and using SWASTYA.</p>
    <label className="help-search">Search frequently asked questions<input type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Try “password”, “cases” or “NGO”" /></label>
    <div className="help-topics" aria-label="Help topics">{categories.map(topic => <button key={topic} aria-pressed={topic === category} onClick={() => setCategory(topic)}>{topic}</button>)}</div>
    <p className="muted" role="status">{filtered.length} {filtered.length === 1 ? 'answer' : 'answers'}</p>
    <div className="faq-list">{filtered.map(([_topic, question, answer]) => <details key={question}><summary>{question}</summary><div><p>{answer}</p></div></details>)}</div>
    {!filtered.length && <div className="panel pad"><h2>No matching answers</h2><p>Try a shorter search or choose another topic.</p><button onClick={() => { setQuery(''); setCategory('All topics'); }}>Show all answers</button></div>}
    <aside className="panel pad support-callout"><h2>Still need help?</h2><p>Your platform administrator or assigned support team can help with account access and missing records.</p><a href="#/help/contact">Contact guidance</a></aside>
  </>;
}

function Privacy() {
  return <article className="privacy-copy"><h1>Privacy policy</h1><p className="muted">Last updated: 29 September 2026</p>
    <p>This policy describes how the current SWASTYA application handles information. The organisation operating your installation is responsible for its hosting, access administration and handling of privacy requests.</p>
    <h2>Information stored</h2><p>Account information includes your name, email, role, password hash, location where applicable, optional profile picture and preferences. Depending on your use and support needs, records may include cases, hearings, assignments, follow-ups, assessments, distress outputs, alerts and communications entered by authorised teams.</p>
    <h2>How information is used</h2><p>Information supports sign-in, case coordination, follow-ups, service matching, preliminary scheme eligibility and administrative reporting. Activity logs record account and access actions for auditing. Your profile preferences control appearance and accessibility.</p>
    <h2>Access and confidentiality</h2><p>Access is controlled by role, assignment and jurisdiction. National administrators receive aggregated reporting. Private counselling notes are kept separate from legal case information and are not automatically available to legal officers. Operators with database or hosting administration privileges may have technical access to stored information.</p>
    <h2>Passwords and photographs</h2><p>Passwords are stored as Argon2 hashes, not readable passwords. Changing a password invalidates previously issued sessions. Profile images are decoded, resized and re-encoded to remove embedded metadata, including location metadata, before storage.</p>
    <h2>Browser storage and external services</h2><p>Before login, accessibility preferences are stored in this browser’s local storage. Signed-in preferences are stored with your account. Sign-in tokens are held in application memory. The current interface loads fonts from Google Fonts, which receives a network request from your browser. Following an external scheme or organisation link takes you to that provider’s website and privacy practices.</p>
    <h2>Retention and requests</h2><p>The current application has no automatic account-deletion or data-retention schedule. Contact the organisation operating your installation to ask about retention, correction, export or deletion. These requests are not submitted automatically through this page.</p>
    <h2>Your controls</h2><p>My Profile lets you update your name and email, change your password and add or remove your picture. You can also change display preferences. Contact your support team about corrections to case or clinical records. Removing a profile picture clears the current application record; hosting backups are managed by the operator.</p>
    <h2>Privacy questions</h2><p>Contact the administrator or support team that provided your access. See Contact for the contact details configured for this installation. Share only the details needed to explain your request; never share your password.</p><a href="#/help/contact">Read contact guidance</a>
  </article>;
}

function Accessibility({ user, profileProps }) {
  if (user && profileProps.profileError) return <><h1>Accessibility settings</h1><ErrorBox error={profileProps.profileError} /><button onClick={profileProps.onRetry}>Try again</button></>;
  if (user && !profileProps.profile) return <p role="status">Loading account preferences…</p>;
  return <AccessibilityForm key={user?.id || 'guest'} user={user} profileProps={profileProps} />;
}

function AccessibilityForm({ user, profileProps }) {
  const source = user ? profileProps.profile : profileProps.guestPreferences;
  const [form, setForm] = useState(() => Object.fromEntries(Object.keys(defaultPreferences).map(key => [key, source[key]])));
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [message, setMessage] = useState('');
  function field(key, value) { setForm(previous => ({ ...previous, [key]: value })); }
  async function save(event) {
    event.preventDefault(); setBusy(true); setError(''); setMessage('');
    try {
      if (user) {
        const { name, email, language } = profileProps.profile;
        profileProps.onUpdate(await patch('/profile', { name, email, language, ...form }));
        setMessage('Accessibility settings saved to your account.');
      } else {
        const saved = profileProps.onGuestPreferencesChange(form);
        setMessage(saved ? 'Settings saved in this browser.' : 'Settings applied for this visit. Your browser could not save them.');
      }
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  return <><h1>Accessibility settings</h1><p>{user ? 'These preferences follow your account when you sign in.' : 'No login needed. These preferences apply to this browser; your account settings take over after sign-in.'}</p>
    <ErrorBox error={error} />{message && <p role="status" className="settings-success">{message}</p>}
    <form className="panel pad accessibility-form" onSubmit={save}><fieldset disabled={busy}><legend>Display preferences</legend>
      <label>Theme<select value={form.theme} onChange={e => field('theme', e.target.value)}><option value="system">Use device setting</option><option value="light">Light</option><option value="dark">Dark</option></select></label>
      <label>Text size<select value={form.text_size} onChange={e => field('text_size', e.target.value)}><option value="standard">Standard</option><option value="large">Large</option><option value="extra-large">Extra large</option></select></label>
      <label className="settings-check"><input type="checkbox" checked={form.high_contrast} onChange={e => field('high_contrast', e.target.checked)} />High contrast</label>
      <label className="settings-check"><input type="checkbox" checked={form.reduced_motion} onChange={e => field('reduced_motion', e.target.checked)} />Reduce motion</label>
      <div className="help-actions"><button className="primary" type="submit">{busy ? 'Saving…' : 'Save settings'}</button><button type="button" onClick={() => setForm({ ...defaultPreferences })}>Reset form to defaults</button></div>
    </fieldset></form><section className="panel pad"><h2>Keyboard and browser controls</h2><p>Use Tab and Shift+Tab to move between controls. Use Enter to activate links and buttons. Browser zoom can further enlarge the page. Report accessibility barriers to your platform administrator.</p><a href="#/help/contact">Get help</a></section></>;
}

export default function SupportPages({ page, user, profileProps }) {
  return <div className="support-site"><a className="skip-link" href="#support-content" onClick={event => { event.preventDefault(); document.getElementById("support-content")?.focus(); }}>Skip to content</a>
    <header className="support-header"><a href="#" className="support-brand">SWASTYA</a><nav aria-label="Support navigation"><a href="#">Back to {user ? 'workspace' : 'home'}</a><a href="#/privacy" aria-current={page === 'privacy' ? 'page' : undefined}>Privacy</a><a href="#/accessibility" aria-current={page === 'accessibility' ? 'page' : undefined}>Accessibility</a><a href="#/help" aria-current={page.startsWith('help') ? 'page' : undefined}>Help</a></nav></header>
    <main id="support-content" tabIndex={-1} className="support-content">{page === 'privacy' ? <Privacy /> : page === 'accessibility' ? <Accessibility user={user} profileProps={profileProps} /> : <FAQ key={page} contact={page === 'help/contact'} />}</main>
    <SiteFooter />
  </div>;
}
