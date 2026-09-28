import { useEffect, useState } from "react";
import { api } from "./api";
import { readPreferences, savePreferences } from "./preferences";

export function useProfile(user, setUser) {
  const [guestPreferences, setGuestPreferences] = useState(readPreferences);
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
    const preferences = profile || guestPreferences;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    function apply() {
      root.dataset.theme = preferences.theme === "system" ? (media.matches ? "dark" : "light") : preferences.theme;
      root.dataset.textSize = preferences.text_size || "standard";
      root.dataset.contrast = String(preferences.high_contrast || false);
      root.dataset.reduceMotion = String(preferences.reduced_motion || false);
    }
    apply();
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, [profile, guestPreferences]);
  function onUpdate(value) {
    setState({ id, profile: value, error: "" });
    setUser(previous => previous?.id === id ? { ...previous, name: value.name, email: value.email } : previous);
  }
  function onGuestPreferencesChange(value) {
    setGuestPreferences(value);
    return savePreferences(value);
  }
  return { guestPreferences, onGuestPreferencesChange, profile, profileError: error, onUpdate, onRetry: () => setAttempt(x => x + 1) };
}

