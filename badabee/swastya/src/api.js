let token = null;
export function setToken(value) {
  token = value;
}
export async function api(path, options = {}) {
  const response = await fetch(
    `${import.meta.env.VITE_API_URL || "/api"}${path}`,
    {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    },
  );
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401)
      window.dispatchEvent(new Event("session-expired"));
    const message =
      typeof data.detail === "string"
        ? data.detail
        : data.detail?.map((x) => `${x.loc.at(-1)}: ${x.msg}`).join("; ");
    throw new Error(message || `Request failed (${response.status})`);
  }
  return data;
}
export const post = (path, data) =>
  api(path, { method: "POST", body: JSON.stringify(data) });
export const patch = (path, data) =>
  api(path, { method: "PATCH", body: JSON.stringify(data) });
