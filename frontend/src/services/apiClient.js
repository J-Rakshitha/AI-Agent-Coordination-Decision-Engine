import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
export const WS_URL = API_BASE_URL.replace("http", "ws") + "/ws/live";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("coordination_engine_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---------- Auth (Phase C) ----------
export const login = (payload) => apiClient.post("/api/auth/login", payload);
export const register = (payload) => apiClient.post("/api/auth/register", payload);
export const getMe = () => apiClient.get("/api/auth/me");
export const listUsers = () => apiClient.get("/api/auth/users");

// ---------- Monitoring (Phase B — API only, no UI change) ----------
export const getMonitoringStatus = () => apiClient.get("/api/monitoring/status");

// ---------- Dev-Collaboration ----------
export const startEditSession = (payload) => apiClient.post("/api/dev-collab/edit-session/start", payload);
export const endEditSession = (sessionId) => apiClient.post(`/api/dev-collab/edit-session/${sessionId}/end`);
export const getActiveSessions = () => apiClient.get("/api/dev-collab/active-sessions");
export const checkConflicts = () => apiClient.post("/api/dev-collab/check-conflicts");
export const listConflicts = () => apiClient.get("/api/dev-collab/conflicts");
export const suggestResolution = (conflictId) =>
  apiClient.post(`/api/dev-collab/conflicts/${conflictId}/suggest-resolution`);
export const simulateDemoConflict = () => apiClient.post("/api/dev-collab/simulate-demo-conflict");
export const listCommits = () => apiClient.get("/api/dev-collab/commits");
export const githubStatus = () => apiClient.get("/api/dev-collab/github/status");
export const githubSync = () => apiClient.post("/api/dev-collab/github/sync", null, { timeout: 45000 });

// ---------- AIOps ----------
export const ingestMetrics = (payload) => apiClient.post("/api/incidents/ingest-metrics", payload);
export const simulateIncident = () => apiClient.post("/api/incidents/simulate");
export const listIncidents = () => apiClient.get("/api/incidents/");

// ---------- System ----------
export const healthCheck = () => apiClient.get("/api/system/health");
export const getStats = () => apiClient.get("/api/system/stats");
export const getKnowledgeBase = () => apiClient.get("/api/system/knowledge-base");
export const toggleLlmFailure = (enabled) => apiClient.post(`/api/system/toggle-llm-failure?enabled=${enabled}`);
export const getLlmFailureStatus = () => apiClient.get("/api/system/llm-failure-status");
export const getDecisionLog = () => apiClient.get("/api/system/decision-log");
export const getNotifications = () => apiClient.get("/api/system/notifications");

// ---------- Tool Integration (Milestone 2) ----------
export const listTools = () => apiClient.get("/api/tools/");
export const selectAndExecuteTool = (payload) => apiClient.post("/api/tools/select-and-execute", payload);
export const getToolAccuracy = () => apiClient.get("/api/tools/accuracy");

export default apiClient;
