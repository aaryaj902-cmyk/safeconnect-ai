/**
 * SafeConnect AI - shared frontend API client.
 * Include this on every page BEFORE any page-specific script:
 *   <script src="js/api.js"></script>
 */

const SafeConnectAPI = (() => {
  // Backend base URL. Override by setting window.SAFECONNECT_API_BASE before
  // this script loads, if you serve the backend on a different host/port.
  const BASE_URL = window.SAFECONNECT_API_BASE || "http://localhost:8000";

  const TOKEN_KEY = "safeconnect_token";
  const USER_KEY = "safeconnect_user";

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function setSession(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  function getUser() {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  }

  function isLoggedIn() {
    return !!getToken();
  }

  async function request(path, { method = "GET", body = null, auth = true } = {}) {
    const headers = { "Content-Type": "application/json" };
    const token = getToken();
    if (auth && token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    let response;
    try {
      response = await fetch(`${BASE_URL}${path}`, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
      });
    } catch (err) {
      throw new Error(
        "Could not reach the SafeConnect AI backend. Is it running at " +
          BASE_URL +
          "? (" +
          err.message +
          ")"
      );
    }

    let data = null;
    const text = await response.text();
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = text;
    }

    if (!response.ok) {
      const detail =
        (data && (data.detail || data.message)) || `Request failed (${response.status})`;
      const err = new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
      err.status = response.status;
      err.data = data;
      throw err;
    }

    return data;
  }

  // ---- Auth ----
  async function register(fullName, email, password) {
    const data = await request("/api/auth/register", {
      method: "POST",
      auth: false,
      body: { full_name: fullName, email, password },
    });
    setSession(data.access_token, data.user);
    return data;
  }

  async function login(email, password) {
    const data = await request("/api/auth/login", {
      method: "POST",
      auth: false,
      body: { email, password },
    });
    setSession(data.access_token, data.user);
    return data;
  }

  function logout() {
    clearSession();
  }

  // ---- Scans ----
  const scanProfile = (full_name, company_name, linkedin_url) =>
    request("/api/scan/profile", { method: "POST", body: { full_name, company_name, linkedin_url } });

  const scanMessage = (message_text, sender_email) =>
    request("/api/scan/message", { method: "POST", body: { message_text, sender_email } });

  const scanJob = (job_title, company_name, description, salary_range, location) =>
    request("/api/scan/job", {
      method: "POST",
      body: { job_title, company_name, description, salary_range, location },
    });

  const scanLink = (url) => request("/api/scan/link", { method: "POST", body: { url } });

  const scanHistory = (limit = 20) => request(`/api/scan/history?limit=${limit}`, { method: "GET" });

  const getScan = (id) => request(`/api/scan/${id}`, { method: "GET", auth: false });

  // ---- Companies ----
  const searchCompanies = (q, limit = 10) =>
    request(`/api/companies?q=${encodeURIComponent(q)}&limit=${limit}`, { method: "GET", auth: false });

  // ---- Reports / Ledger ----
  const listReports = (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/api/reports${qs ? "?" + qs : ""}`, { method: "GET", auth: false });
  };

  const createReport = (payload) =>
    request("/api/reports", { method: "POST", body: payload });

  const ledgerStats = () => request("/api/reports/stats", { method: "GET", auth: false });

  // ---- Dashboard ----
  const getDashboard = () => request("/api/dashboard", { method: "GET" });

  return {
    BASE_URL,
    getToken,
    getUser,
    isLoggedIn,
    setSession,
    clearSession,
    register,
    login,
    logout,
    scanProfile,
    scanMessage,
    scanJob,
    scanLink,
    scanHistory,
    getScan,
    searchCompanies,
    listReports,
    createReport,
    ledgerStats,
    getDashboard,
  };
})();
