import { useState } from "react";
import { patch, post } from "./api";
import { ErrorBox } from "./ui";
import { human } from "./format";
import "./Profile.css";

export function Avatar({ name, photo }) {
  return photo ? <img className="profile-photo" src={photo} alt="Your profile" /> :
    <span className="profile-photo profile-initials" aria-label="Profile initials">{name?.trim().split(/\s+/).slice(0, 2).map(x => x[0]).join("").toUpperCase()}</span>;
}

export default function Profile(props) {
  if (props.profileError) return <section className="panel pad"><ErrorBox error={props.profileError} /><button onClick={props.onRetry}>Try again</button></section>;
  if (!props.profile) return <p role="status">Loading your profile…</p>;
  return <ProfileForm key={props.profile.id} {...props} />;
}

function ProfileForm({ profile, onUpdate, onLogout }) {
  const [form, setForm] = useState(() => {
    const { name, email, phone, language, theme, text_size, high_contrast, reduced_motion } = profile;
    return { name, email, phone: phone || "", language, theme, text_size, high_contrast, reduced_motion, current_password: "" };
  });
  const [current, setCurrent] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  async function perform(action) {
    setBusy(true); setError(""); setMessage("");
    try { await action(); } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  function field(name, value) { setForm(old => ({ ...old, [name]: value })); }
  async function upload(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    await perform(async () => {
      if (!["image/jpeg", "image/png"].includes(file.type) || file.size > 2 * 1024 * 1024) throw new Error("Choose a PNG or JPEG up to 2 MB.");
      const data_url = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error("Unable to read this photo."));
        reader.readAsDataURL(file);
      });
      onUpdate(await post("/profile/photo", { data_url }));
      setMessage("Profile photo saved.");
    });
  }
  return <div className="profile-settings">
    <div className="page-heading"><div><h1>My Profile</h1><p className="muted">Manage your details, preferences and account security.</p></div></div>
    <ErrorBox error={error} />
    {message && <p className="settings-success" role="status">{message}</p>}
    <section className="panel pad">
      <h2>Profile picture</h2>
      <div className="photo-editor"><Avatar name={profile.name} photo={profile.photo} /><div><p>PNG or JPEG, up to 2 MB and 16 megapixels.</p>
        <label className="photo-upload">{profile.photo ? "Change picture" : "Add picture"}<input aria-label="Upload profile picture" type="file" accept="image/png,image/jpeg" disabled={busy} onChange={upload} /></label>
        {profile.photo && <button disabled={busy} onClick={() => perform(async () => { onUpdate(await post("/profile/photo", { data_url: null })); setMessage("Profile photo removed."); })}>Remove picture</button>}
      </div></div>
      <p className="muted">Account type: {human(profile.role)} · Joined {new Date(profile.created_at).toLocaleDateString()}</p>
    </section>
    <form className="panel pad" onSubmit={event => { event.preventDefault(); perform(async () => { onUpdate(await patch("/profile", form)); field("current_password", ""); setMessage("Profile and preferences saved."); }); }}>
      <fieldset disabled={busy}><legend>Personal details & preferences</legend>
        <div className="settings-grid">
          <label>Full name<input autoComplete="name" required minLength={2} maxLength={120} value={form.name} onChange={e => field("name", e.target.value)} /></label>
          <label>Email address<input type="email" autoComplete="email" required maxLength={254} value={form.email} onChange={e => field("email", e.target.value)} /></label>
          <label>Contact phone number<input type="tel" autoComplete="tel" maxLength={32} value={form.phone} onChange={e => field("phone", e.target.value)} /><small>Staff contact numbers are visible to assigned victims and their support team.</small></label>
          {form.email.trim().toLowerCase() !== profile.email && <label>Current password to change email<input type="password" autoComplete="current-password" required maxLength={256} value={form.current_password} onChange={e => field("current_password", e.target.value)} /></label>}
          <label>Preferred communication language<select value={form.language} onChange={e => field("language", e.target.value)}>{["English", "Hindi", "Tamil", "Kannada", "Telugu", "Malayalam", "Marathi", "Bengali"].map(x => <option key={x}>{x}</option>)}</select><small>The interface is currently available in English.</small></label>
          <label>Appearance<select value={form.theme} onChange={e => field("theme", e.target.value)}><option value="system">Use device setting</option><option value="light">Light</option><option value="dark">Dark</option></select></label>
          <label>Text size<select value={form.text_size} onChange={e => field("text_size", e.target.value)}><option value="standard">Standard</option><option value="large">Large</option><option value="extra-large">Extra large</option></select></label>
        </div>
        <div className="accessibility-toggles"><label className="settings-check"><input type="checkbox" checked={form.high_contrast} onChange={e => field("high_contrast", e.target.checked)} />High contrast</label>
        <label className="settings-check"><input type="checkbox" checked={form.reduced_motion} onChange={e => field("reduced_motion", e.target.checked)} />Reduce animations and motion</label></div>
        <button className="primary" type="submit">{busy ? "Saving…" : "Save changes"}</button>
      </fieldset>
    </form>
    <form className="panel pad" onSubmit={event => { event.preventDefault(); perform(async () => {
      if (password !== confirmation) throw new Error("New passwords do not match.");
      await post("/profile/password", { current_password: current, new_password: password });
      setCurrent(""); setPassword(""); setConfirmation("");
      onLogout();
    }); }}>
      <fieldset disabled={busy}><legend>Change password</legend><p>Use at least 12 characters. Changing your password signs you out on all devices. Sign in again with your new password.</p>
        <div className="settings-grid">
          <label>Current password<input type="password" autoComplete="current-password" required maxLength={256} value={current} onChange={e => setCurrent(e.target.value)} /></label>
          <label>New password<input type="password" autoComplete="new-password" required minLength={12} maxLength={256} value={password} onChange={e => setPassword(e.target.value)} /></label>
          <label>Confirm new password<input type="password" autoComplete="new-password" required minLength={12} maxLength={256} value={confirmation} onChange={e => setConfirmation(e.target.value)} /></label>
        </div><button type="submit">Change password and sign out</button>
      </fieldset>
    </form>
    <section className="panel pad"><h2>Privacy & access</h2><p>Your role and access permissions are managed by the support administrator. Updating your profile does not change which cases or records you may access.</p><p>Profile changes are recorded in the audit log. Passwords are stored as secure hashes. Uploaded photos have embedded location metadata removed.</p></section>
  </div>;
}
