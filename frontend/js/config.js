/**
 * SafeConnect AI - environment config.
 * Must be loaded BEFORE js/api.js on every page.
 *
 * Auto-detects whether the site is running locally (localhost/127.0.0.1) or
 * deployed, and points the frontend at the right backend URL accordingly.
 *
 * After you deploy the backend on Render, replace the placeholder URL below
 * with your real Render backend URL (it will look like
 * "https://safeconnect-api-xxxx.onrender.com" -- check your Render
 * dashboard for the exact one).
 */
(function () {
  const PRODUCTION_API_BASE = "https://safeconnect-api-2vtv.onrender.com";

  const isLocal =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === "";

  window.SAFECONNECT_API_BASE = isLocal ? "http://localhost:8000" : PRODUCTION_API_BASE;
})();
