export const defaultPreferences = { theme: 'light', text_size: 'standard', high_contrast: false, reduced_motion: false };
const key = 'swastya-display-preferences';

export function readPreferences() {
  try {
    const value = JSON.parse(localStorage.getItem(key) || '{}');
    return {
      theme: ['system', 'light', 'dark'].includes(value.theme) ? value.theme : 'light',
      text_size: ['standard', 'large', 'extra-large'].includes(value.text_size) ? value.text_size : 'standard',
      high_contrast: value.high_contrast === true,
      reduced_motion: value.reduced_motion === true,
    };
  } catch { return { ...defaultPreferences }; }
}

export function savePreferences(value) {
  try { localStorage.setItem(key, JSON.stringify(value)); return true; }
  catch { return false; }
}
