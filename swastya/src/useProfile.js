import { useEffect, useState } from "react";
import { api } from "./api";

export function useProfile(user, setUser) {
  const [state, setState] = useState({ id: null, profile: null, error: "" });
  const [attempt, setAttempt] = useState(0);
  const id = user?.id;
  const profile = state.id === id ? state.profile : null;
  const error = state.id === id ? state.error : "";
  useEffect(() => {
    let active = true;
    if (id) api("/profile").then(value => { if (active) setState({ id, profile: value, error: "" }); })
      .catch(err => { if (active) setState({ id, profile: null, error: err.message }); });
    return () => { active = false; };
  }, [id, attempt]);
  useEffect(() => {
    const root = document.documentElement;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    function apply() {
      root.dataset.theme = profile?.theme === "system" ? (media.matches ? "dark" : "light") : (profile?.theme || "light");
      root.dataset.textSize = profile?.text_size || "standard";
      root.dataset.contrast = String(profile?.high_contrast || false);
      root.dataset.reduceMotion = String(profile?.reduced_motion || false);
    }
    apply();
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, [profile]);
  function onUpdate(value) {
    setState({ id, profile: value, error: "" });
    setUser(previous => previous?.id === id ? { ...previous, name: value.name, email: value.email } : previous);
  }
  return { profile, profileError: error, onUpdate, onRetry: () => setAttempt(x => x + 1) };
}

