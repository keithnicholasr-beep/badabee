import { useEffect, useRef } from "react";
import { Avatar } from "./Profile";

export default function DashboardHeader({ user, photo, onNavigate, onProfile, profileActive }) {
  const header = useRef(null);
  useEffect(() => {
    const update = () => document.documentElement.style.setProperty("--dashboard-header-height", `${header.current.getBoundingClientRect().height}px`);
    const observer = new ResizeObserver(update);
    observer.observe(header.current);
    update();
    return () => { observer.disconnect(); document.documentElement.style.removeProperty("--dashboard-header-height"); };
  }, []);
  return <header ref={header} className="dashboard-header">
    <div className="dashboard-header-main">
      <button type="button" className="dashboard-header-brand" onClick={() => onNavigate("home")} aria-label="SWASTYA home"><strong>SWASTYA</strong></button>
      <button className="dashboard-header-user header-profile-button" onClick={onProfile} aria-current={profileActive ? "page" : undefined} title={`${user.name}\n${user.email}`}><Avatar name={user.name} photo={photo} /><span>My Profile</span></button>
    </div>
    <nav className="dashboard-header-nav" aria-label="About SWASTYA">
      {[["home", "Home"], ["services", "Services"], ["features", "Platform"], ["security", "Security"], ["support", "Support"]].map(([id, label]) => <button key={id} onClick={() => onNavigate(id)}>{label}</button>)}
    </nav>
  </header>;
}
