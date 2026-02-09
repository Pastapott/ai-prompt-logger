function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

async function fetchLogs() {
  const res = await fetch("/api/logs");
  const data = await res.json();
  // backend returns { logs: [...] }
  return data.logs || [];
}

function renderLogs(logs) {
  const logsEl = document.getElementById("logs");
  const emptyEl = document.getElementById("logs-empty");
  if (!logsEl) return;

  logsEl.innerHTML = "";
  const recent = (logs || []).slice().reverse().slice(0, 6);

  if (recent.length === 0) {
    if (emptyEl) emptyEl.style.display = "block";
    return;
  }
  if (emptyEl) emptyEl.style.display = "none";

  for (const item of recent) {
    const div = document.createElement("div");
    div.className = "log-row";

    const modeClass = (item.mode || "").includes("real") ? "ai" : "stub";

    div.innerHTML = `
      <div class="log-meta">
        <span class="pill ${modeClass}">${escapeHtml(item.mode || "unknown")}</span>
        <span class="pill ok">${escapeHtml(item.env || "")}</span>
        <span class="pill">${escapeHtml(item.version || "")}</span>
        <span>${escapeHtml(item.timestamp || "")}</span>
      </div>
      <div><strong>Q:</strong> ${escapeHtml(item.prompt || "")}</div>
      <div style="margin-top:6px;"><strong>A:</strong> ${escapeHtml((item.reply || "").slice(0, 220))}${(item.reply || "").length > 220 ? "…" : ""}</div>
    `;

    logsEl.appendChild(div);
  }
}

async function sendPrompt() {
  const btn = document.getElementById("send");
  const promptEl = document.getElementById("prompt");
  const replyEl = document.getElementById("reply");
  const modeEl = document.getElementById("mode");

  const prompt = (promptEl?.value || "").trim();
  if (!prompt) {
    if (replyEl) replyEl.textContent = "Please enter a prompt.";
    return;
  }

  if (btn) btn.disabled = true;
  if (replyEl) replyEl.textContent = "Generating…";
  if (modeEl) modeEl.textContent = "working…";

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt })
    });

    const data = await res.json();

    if (replyEl) replyEl.textContent = data.reply || "(no reply)";
    if (modeEl) modeEl.textContent = `mode: ${data.mode || "unknown"} • v ${data.version || "?"}`;

    const logs = await fetchLogs();
    renderLogs(logs);
  } catch (e) {
    if (replyEl) replyEl.textContent = "Error: could not reach server.";
    if (modeEl) modeEl.textContent = "error";
  } finally {
    if (btn) btn.disabled = false;
  }
}

document.getElementById("send")?.addEventListener("click", sendPrompt);

// initial load
(async () => {
  try {
    const logs = await fetchLogs();
    renderLogs(logs);
  } catch {
    // ignore
  }
})();