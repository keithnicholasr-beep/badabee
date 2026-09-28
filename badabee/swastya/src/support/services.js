import { api, post, patch } from "../api";

export const supportApi = {
  me: () => api("/portal/me"),
  profile: (id) => api(`/portal/victims/${id}`),
  caseload: () => api("/portal/caseload"),
  checkin: (data) => post("/portal/checkins", data),
  action: (id, data) => post(`/portal/victims/${id}/actions`, data),
  resolve: (id) => post(`/portal/actions/${id}/resolve`, {}),
  schedule: (data) => post("/followups", data),
  updateFollowup: (id, status) => patch(`/followups/${id}`, { status }),
  note: (id, note) => post(`/portal/followups/${id}/note`, { note }),
  chatHistory: () => api("/portal/chat"),
  chat: (data) => post("/portal/chat", data),
  ngos: (id) => api(`/ngos/match?victim_id=${encodeURIComponent(id)}`),
  schemes: (id) => api(`/victims/${id}/eligible-schemes`),
  alerts: () => api("/alerts?limit=200"),
  acknowledge: (id) => post(`/alerts/${id}/acknowledge`, {}),
  notifications: () => api("/notifications"),
  read: (id) => post(`/notifications/${id}/read`, {}),
};
