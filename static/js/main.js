/* ═══════════════════════════════════════════════
   TCOE ID Generation — Nokia PWA
   Frontend Logic
═══════════════════════════════════════════════ */

"use strict";

// ── STATE ─────────────────────────────────────
let lastIds = [];
let deferredInstallPrompt = null;

// ── SERVICE WORKER REGISTRATION ───────────────
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js")
      .then(reg => console.log("[SW] Registered:", reg.scope))
      .catch(err => console.warn("[SW] Registration failed:", err));
  });
}

// ── PWA INSTALL BANNER ─────────────────────────
window.addEventListener("beforeinstallprompt", e => {
  e.preventDefault();
  deferredInstallPrompt = e;
  const banner = document.getElementById("installBanner");
  if (banner) banner.classList.add("show");
});

window.addEventListener("appinstalled", () => {
  const banner = document.getElementById("installBanner");
  if (banner) banner.classList.remove("show");
  deferredInstallPrompt = null;
  showToast("App installed successfully!");
});

function setupInstallHandlers() {
  const installBtn  = document.getElementById("installBtn");
  const dismissBtn  = document.getElementById("dismissInstall");
  const banner      = document.getElementById("installBanner");

  if (installBtn) {
    installBtn.addEventListener("click", async () => {
      if (!deferredInstallPrompt) return;
      deferredInstallPrompt.prompt();
      const { outcome } = await deferredInstallPrompt.userChoice;
      if (outcome === "accepted") {
        banner && banner.classList.remove("show");
        deferredInstallPrompt = null;
      }
    });
  }

  if (dismissBtn) {
    dismissBtn.addEventListener("click", () => {
      banner && banner.classList.remove("show");
    });
  }
}

// ── GENERATE ID ───────────────────────────────
async function generateID() {
  const uc       = document.getElementById("useCase").value.trim();
  const caller   = document.getElementById("callerNet").value.trim();
  const receiver = document.getElementById("receiverNet").value.trim();
  const count    = parseInt(document.getElementById("count").value) || 1;
  const rsv      = document.getElementById("reserve").checked;

  if (!uc) {
    showToast("Select a use case first", true);
    return;
  }
  if (!caller || !receiver) {
    showToast("Select both Caller and Receiver networks", true);
    return;
  }

  const btn = document.getElementById("genBtn");
  btn.disabled = true;
  btn.textContent = "Generating…";

  hideError();
  hideResult();

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        use_case:         uc,
        caller_network:   caller,
        receiver_network: receiver,
        count,
        reserve: rsv,
      }),
    });

    const data = await res.json();

    if (!res.ok || data.error) {
      showError(data.error || "Unknown server error");
    } else {
      showResult(data);
      const hc = document.getElementById("histCase");
      if (hc) { hc.value = uc; loadHistory(); }
    }
  } catch (err) {
    showError("Network error — " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Generate";
  }
}

// ── DISPLAY RESULT ────────────────────────────
function showResult(data) {
  const ids   = data.ids || [];
  lastIds     = ids;

  const box     = document.getElementById("resultBox");
  const rid     = document.getElementById("resultId");
  const extra   = document.getElementById("resultExtra");
  const netInfo = document.getElementById("resultNetwork");

  rid.textContent = ids[0] || "";

  if (ids.length > 1) {
    extra.innerHTML = ids.slice(1)
      .map(id => `<span>${id}</span>`)
      .join("<br>");
  } else {
    extra.textContent = "";
  }

  // Show caller → receiver + resolved code
  if (data.caller_network && data.receiver_network && data.network_code) {
    netInfo.textContent =
      `${data.caller_network} → ${data.receiver_network}  ·  code ${data.network_code}`;
  } else {
    netInfo.textContent = "";
  }

  box.classList.add("show");
  if (data.reserved) showToast("IDs reserved in database");
}

function hideResult() {
  document.getElementById("resultBox").classList.remove("show");
}

// ── COPY ──────────────────────────────────────
function copyID() {
  if (!lastIds.length) return;
  const text = lastIds.join("\n");

  if (navigator.clipboard) {
    navigator.clipboard.writeText(text)
      .then(() => showToast("Copied to clipboard"))
      .catch(() => fallbackCopy(text));
  } else {
    fallbackCopy(text);
  }
}

function fallbackCopy(text) {
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.cssText = "position:fixed;opacity:0;pointer-events:none";
  document.body.appendChild(ta);
  ta.select();
  document.execCommand("copy");
  document.body.removeChild(ta);
  showToast("Copied to clipboard");
}

// ── HISTORY ───────────────────────────────────
async function loadHistory() {
  const uc    = document.getElementById("histCase").value;
  const tbody = document.getElementById("histBody");

  tbody.innerHTML = `<tr><td colspan="3" class="empty-row">Loading…</td></tr>`;

  try {
    const res  = await fetch(`/api/history?use_case=${encodeURIComponent(uc)}&limit=10`);
    const rows = await res.json();

    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="3" class="empty-row">No records for ${uc}</td></tr>`;
      return;
    }

    tbody.innerHTML = rows.map(r => `
      <tr>
        <td>${r.tcoe_id || "—"}</td>
        <td>${r.network || "—"}</td>
        <td>${padSeq(r.sequence)}</td>
      </tr>
    `).join("");
  } catch {
    tbody.innerHTML = `<tr><td colspan="3" class="empty-row">Error loading history</td></tr>`;
  }
}

// ── ERROR HELPERS ─────────────────────────────
function showError(msg) {
  const box = document.getElementById("errorBox");
  document.getElementById("errorMsg").textContent = "⚠ " + msg;
  box.classList.add("show");
}

function hideError() {
  document.getElementById("errorBox").classList.remove("show");
}

// ── TOAST ─────────────────────────────────────
function showToast(msg, isErr = false) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.toggle("err", isErr);
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2600);
}

// ── UTILS ─────────────────────────────────────
function padSeq(n) {
  return n != null ? String(n).padStart(9, "0") : "—";
}

// ── KEYBOARD SHORTCUT (Ctrl/Cmd + Enter) ──────
document.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") generateID();
});

// ── INIT ──────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
  setupInstallHandlers();
  const hc = document.getElementById("histCase");
  if (hc && hc.value) loadHistory();
});
