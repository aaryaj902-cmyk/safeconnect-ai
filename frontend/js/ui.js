/**
 * SafeConnect AI - shared UI rendering helpers.
 * Include after js/api.js.
 */

const SafeConnectUI = (() => {
  const RISK_META = {
    safe: { badgeClass: "bg-green-100 text-green-800", ring: "#16a34a", icon: "verified" },
    verify: { badgeClass: "bg-yellow-100 text-yellow-800", ring: "#d97706", icon: "info" },
    high_risk: { badgeClass: "bg-error-container text-on-error-container", ring: "#ba1a1a", icon: "warning" },
  };

  const SIGNAL_STATUS_ICON = {
    positive: "check_circle",
    negative: "cancel",
    neutral: "remove_circle",
  };

  const SIGNAL_STATUS_COLOR = {
    positive: "text-green-600",
    negative: "text-error",
    neutral: "text-on-surface-variant",
  };

  function riskMeta(riskLevel) {
    return RISK_META[riskLevel] || RISK_META.verify;
  }

  /** Updates a circular SVG gauge (expects the markup pattern used across the
   * scanner screens: a background circle + a `.risk-gauge` stroke circle with
   * r=88, circumference ~553, plus #score-value text). */
  function updateGauge({ gaugeEl, scoreEl, badgeEl, score, riskLevel, verdictLabel }) {
    const circumference = 2 * Math.PI * 88; // ~553
    const offset = circumference * (1 - score / 100);
    const meta = riskMeta(riskLevel);

    if (gaugeEl) {
      gaugeEl.style.stroke = meta.ring;
      gaugeEl.style.strokeDashoffset = offset.toFixed(1);
    }
    if (scoreEl) {
      scoreEl.textContent = `${Math.round(score)}`;
    }
    if (badgeEl) {
      badgeEl.className = `inline-flex items-center gap-2 px-4 py-1.5 rounded-full mb-4 ${meta.badgeClass}`;
      badgeEl.innerHTML = `<span class="material-symbols-outlined text-[18px]" style="font-variation-settings: 'FILL' 1;">${meta.icon}</span><span class="font-label-md text-label-md">${verdictLabel}</span>`;
    }
  }

  function renderSignals(container, signals) {
    if (!container) return;
    if (!signals || signals.length === 0) {
      container.innerHTML = `<p class="text-on-surface-variant text-sm">No signals available.</p>`;
      return;
    }
    container.innerHTML = signals
      .map(
        (s) => `
      <div class="flex items-start gap-3 p-3 border border-outline-variant rounded-xl">
        <span class="material-symbols-outlined ${SIGNAL_STATUS_COLOR[s.status] || ""}">${SIGNAL_STATUS_ICON[s.status] || "info"}</span>
        <div>
          <p class="font-label-md text-label-md">${escapeHtml(s.label)}</p>
          <p class="text-sm text-on-surface-variant">${escapeHtml(s.detail)}</p>
        </div>
      </div>`
      )
      .join("");
  }

  function renderReasoning(container, reasoning) {
    if (!container) return;
    if (!reasoning || reasoning.length === 0) {
      container.innerHTML = `<p class="text-on-primary-container text-sm">No additional reasoning available.</p>`;
      return;
    }
    container.innerHTML = reasoning
      .map(
        (r) => `
      <div class="p-4 bg-primary-container/50 border border-on-primary-fixed-variant/20 rounded-xl">
        <h5 class="font-label-md text-label-md text-on-primary mb-2">${escapeHtml(r.title)}</h5>
        <p class="font-body-md text-body-md text-on-primary-container text-sm">${escapeHtml(r.detail)}</p>
      </div>`
      )
      .join("");
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function showToast(message, type = "info") {
    let el = document.getElementById("sc-toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "sc-toast";
      el.style.position = "fixed";
      el.style.bottom = "24px";
      el.style.right = "24px";
      el.style.zIndex = "9999";
      el.style.padding = "12px 20px";
      el.style.borderRadius = "8px";
      el.style.fontFamily = "Inter, sans-serif";
      el.style.fontSize = "14px";
      el.style.fontWeight = "500";
      el.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
      el.style.transition = "opacity 0.3s ease";
      document.body.appendChild(el);
    }
    const colors = {
      info: { bg: "#0f172a", color: "#fff" },
      success: { bg: "#16a34a", color: "#fff" },
      error: { bg: "#ba1a1a", color: "#fff" },
    };
    const c = colors[type] || colors.info;
    el.style.background = c.bg;
    el.style.color = c.color;
    el.textContent = message;
    el.style.opacity = "1";
    clearTimeout(el._hideTimeout);
    el._hideTimeout = setTimeout(() => {
      el.style.opacity = "0";
    }, 3500);
  }

  function timeAgo(isoString) {
    const date = new Date(isoString);
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
    if (seconds < 60) return "just now";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} min${minutes > 1 ? "s" : ""} ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours > 1 ? "s" : ""} ago`;
    const days = Math.floor(hours / 24);
    return `${days} day${days > 1 ? "s" : ""} ago`;
  }

  function riskBadgeHtml(riskLevel, label) {
    const meta = riskMeta(riskLevel);
    return `<span class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold ${meta.badgeClass}">
      <span class="material-symbols-outlined text-[14px]">${meta.icon}</span>${escapeHtml(label)}
    </span>`;
  }

  /** Renders the standard top-nav auth state: shows "Login" link if logged
   * out, or the user's name + a logout button if logged in. Call on every
   * page that has an element with id="auth-slot". */
  function mountAuthSlot() {
    const slot = document.getElementById("auth-slot");
    if (!slot) return;
    const user = SafeConnectAPI.getUser();
    if (user) {
      slot.innerHTML = `
        <div class="flex items-center gap-3">
          <span class="font-label-md text-label-md hidden sm:inline">${escapeHtml(user.full_name)}</span>
          <button id="logout-btn" class="material-symbols-outlined text-on-surface-variant hover:text-error transition-all" title="Log out">logout</button>
        </div>`;
      document.getElementById("logout-btn").addEventListener("click", () => {
        SafeConnectAPI.logout();
        window.location.href = "login.html";
      });
    } else {
      slot.innerHTML = `<a href="login.html" class="font-label-md text-label-md px-4 py-2 bg-primary text-on-primary rounded-lg hover:opacity-90 transition-all">Log In</a>`;
    }
  }

  return {
    riskMeta,
    updateGauge,
    renderSignals,
    renderReasoning,
    escapeHtml,
    showToast,
    timeAgo,
    riskBadgeHtml,
    mountAuthSlot,
  };
})();
