/* ═══════════════════════════════════════════════
   TCOE ID Generation — Nokia PWA
   Frontend Logic
═══════════════════════════════════════════════ */

"use strict";

// ── STATE ─────────────────────────────────────
let lastIds = [];
let deferredInstallPrompt = null;

// Use cases that use the conference (multi-participant) UI
const CONFERENCE_USE_CASES = ["CONFE"];

// ── SERVICE WORKER ────────────────────────────
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js")
      .then(reg => console.log("[SW] Registered:", reg.scope))
      .catch(err => console.warn("[SW] Registration failed:", err));
  });
}

// ── PWA INSTALL BANNER ────────────────────────
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
  const installBtn = document.getElementById("installBtn");
  const dismissBtn = document.getElementById("dismissInstall");
  const banner     = document.getElementById("installBanner");

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

// ── USE CASE CHANGE: swap basic ↔ conference UI ──
function onUseCaseChange(value) {
  const isConf = CONFERENCE_USE_CASES.includes(value.toUpperCase());

  document.getElementById("networkBasic").style.display      = isConf ? "none"  : "";
  document.getElementById("networkConference").style.display = isConf ? ""      : "none";

  if (isConf && document.querySelectorAll(".participant-row").length === 0) {
    addParticipant();
    addParticipant();
    addParticipant();
  }

  hideError();
  hideResult();
  syncHistory();
}

// ── CONFERENCE: ADD PARTICIPANT ───────────────
function addParticipant() {
  const list  = document.getElementById("participantList");
  const idx   = list.querySelectorAll(".participant-row").length + 1;

  const tmpl    = document.getElementById("participantTemplate");
  const options = tmpl.innerHTML;

  const row = document.createElement("div");
  row.className = "participant-row field-row";
  row.innerHTML = `
    <div class="participant-label">
      <span class="field-label">Participant ${idx}</span>
    </div>
    <div class="field participant-select">
      <div class="select-wrap">
        <select class="participant-net" aria-label="Participant ${idx} network" onchange="syncHistory()">
          <option value="">— Select —</option>
          ${options}
        </select>
        <span class="select-arrow" aria-hidden="true">▾</span>
      </div>
    </div>
    <button type="button" class="btn-remove-participant"
            onclick="removeParticipant(this)"
            aria-label="Remove participant ${idx}">✕</button>
  `;

  list.appendChild(row);
  _renumberParticipants();
}

// ── CONFERENCE: REMOVE PARTICIPANT ───────────
function removeParticipant(btn) {
  const list = document.getElementById("participantList");
  if (list.querySelectorAll(".participant-row").length <= 2) {
    showToast("Conference needs at least 2 participants", true);
    return;
  }
  btn.closest(".participant-row").remove();
  _renumberParticipants();
  syncHistory();
}

function _renumberParticipants() {
  document.querySelectorAll(".participant-row").forEach((row, i) => {
    const lbl = row.querySelector(".field-label");
    const sel = row.querySelector(".participant-net");
    const rmv = row.querySelector(".btn-remove-participant");
    if (lbl) lbl.textContent = `Participant ${i + 1}`;
    if (sel) sel.setAttribute("aria-label", `Participant ${i + 1} network`);
    if (rmv) rmv.setAttribute("aria-label", `Remove participant ${i + 1}`);
  });
}

// ── GENERATE ID ──────────────────────────────
async function generateID() {
  const uc    = document.getElementById("useCase").value.trim();
  const count  = 1;
  const rsv    = true;

  if (!uc) { showToast("Select a use case first", true); return; }

  const isConf = CONFERENCE_USE_CASES.includes(uc.toUpperCase());
  let body;

  if (isConf) {
    const selects = [...document.querySelectorAll(".participant-net")];
    const participants = selects.map(s => s.value.trim().toUpperCase());

    if (participants.length < 2) {
      showToast("Add at least 2 participants", true); return;
    }
    if (participants.some(p => !p)) {
      showToast("Select a network for every participant", true); return;
    }

    body = { use_case: uc, participants, count, reserve: rsv,
             description: document.getElementById("description").value.trim() };

  } else {
    const caller   = document.getElementById("callerNet").value.trim();
    const receiver = document.getElementById("receiverNet").value.trim();

    if (!caller || !receiver) {
      showToast("Select both Caller and Receiver networks", true); return;
    }

    body = { use_case: uc, caller_network: caller,
             receiver_network: receiver, count, reserve: rsv,
             description: document.getElementById("description").value.trim() };
  }

  const btn = document.getElementById("genBtn");
  btn.disabled = true;
  btn.textContent = "Generating…";
  hideError();
  hideResult();

  try {
    const res  = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();

    if (!res.ok || data.error) {
      showError(data.error || "Unknown server error");
    } else {
      showResult(data, isConf);
      syncHistory();
    }
  } catch (err) {
    showError("Network error — " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Generate";
  }
}

// ── DISPLAY RESULT ────────────────────────────
function showResult(data, isConference = false) {
  const ids     = data.ids || [];
  lastIds       = ids;

  const box     = document.getElementById("resultBox");
  const rid     = document.getElementById("resultId");
  const extra   = document.getElementById("resultExtra");
  const netInfo = document.getElementById("resultNetwork");

  if (isConference) {
    rid.textContent = "";
    extra.innerHTML = ids
      .map(id => `<span class="conf-id">${id}</span>`)
      .join("");
  } else {
    rid.textContent = ids[0] || "";
    if (ids.length > 1) {
      extra.innerHTML = ids.slice(1).map(id => `<span>${id}</span>`).join("<br>");
    } else {
      extra.textContent = "";
    }
  }

  if (isConference && data.participants) {
    const p = data.participants;
    netInfo.textContent = `${p[0]} → ${p[p.length - 1]}  ·  code ${data.network_code}  ·  via: ${p.join(" → ")}`;
  } else if (data.caller_network && data.receiver_network && data.network_code) {
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
function currentPair() {
  const uc = document.getElementById("useCase").value.trim();
  if (uc.toUpperCase() === "CONFE") {
    const sel = document.querySelectorAll(".participant-net");
    return {
      caller: sel.length > 0 ? sel[0].value.trim() : "",
      receiver: sel.length > 0 ? sel[sel.length - 1].value.trim() : "",
    };
  }
  return {
    caller: document.getElementById("callerNet").value.trim(),
    receiver: document.getElementById("receiverNet").value.trim(),
  };
}

function syncHistory() {
  const uc = document.getElementById("useCase").value.trim();
  const hc = document.getElementById("histCase");
  if (uc && hc) hc.value = uc;
  loadHistory();
}

let historyReq = 0;

async function loadHistory() {
  const myReq = ++historyReq;
  const uc = document.getElementById("histCase").value;
  const { caller, receiver } = currentPair();
  const tbody = document.getElementById("histBody");

  if (!uc || !caller || !receiver) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty-row">Select a use case, caller and receiver network to see its history</td></tr>`;
    return;
  }

  tbody.innerHTML = `<tr><td colspan="4" class="empty-row">Loading…</td></tr>`;

  try {
    const res = await fetch(
      `/api/history?use_case=${encodeURIComponent(uc)}` +
      `&caller=${encodeURIComponent(caller)}&receiver=${encodeURIComponent(receiver)}&limit=500`);
    const rows = await res.json();
    if (myReq !== historyReq) return;

    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="4" class="empty-row">No IDs yet for ${uc} · ${caller} → ${receiver}</td></tr>`;
      return;
    }

    const head = `
      <tr>
        <td colspan="4" style="background:#eef3fb;color:#2f6fed;font-weight:600;padding:10px 12px">
          ${uc} · ${caller} → ${receiver} — ${rows.length} ID${rows.length > 1 ? "s" : ""}
        </td>
      </tr>`;
    tbody.innerHTML = head + rows.map(r => `
      <tr>
        <td>${r.tcoe_id || "—"}</td>
        <td>${r.network_label || r.network || "—"}</td>
        <td>${padSeq(r.sequence)}</td>
        <td>${r.description || "—"}</td>
      </tr>
    `).join("");
  } catch {
    tbody.innerHTML = `<tr><td colspan="4" class="empty-row">Error loading history</td></tr>`;
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

// ── KEYBOARD SHORTCUT ─────────────────────────
document.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") openGenerateConfirm();
});

// ── INIT ──────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
  setupInstallHandlers();
  loadHistory();
  const btnGen   = document.getElementById("confirmGenerate");
  const btnRes   = document.getElementById("confirmReset");
  const btnClose = document.getElementById("confirmClose");
  if (btnGen)   btnGen.addEventListener("click",   () => { closeGenerateConfirm(); generateID(); });
  if (btnRes)   btnRes.addEventListener("click",   () => { closeGenerateConfirm(); resetForm(); });
  if (btnClose) btnClose.addEventListener("click", () => { closeGenerateConfirm(); });
});

// ── CONFIRMATION MODAL ───────────────────────
function openGenerateConfirm() {
  const modal = document.getElementById("confirmModal");
  if (!modal) { generateID(); return; }
  modal.style.display = "flex";
}

function closeGenerateConfirm() {
  const modal = document.getElementById("confirmModal");
  if (!modal) return;
  modal.style.display = "none";
}

// ── FORM RESET ──────────────────────────────
// Only clears the result/error output so the user can adjust selections and re-generate.
function resetForm() {
  hideError();
  hideResult();
}