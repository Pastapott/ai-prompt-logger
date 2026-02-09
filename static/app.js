async function loadLogs() {
  const res = await fetch("/api/logs");
  const data = await res.json();
  const logsEl = document.getElementById("logs");
  logsEl.innerHTML = "";

  const logs = (data.logs || []).slice().reverse();
  if (logs.length === 0) {
    logsEl.innerHTML = "<p class='muted'>No logs yet.</p>";
    return;
  }

  for (const item of logs) {
    const div = document.createElement("div");
    div.className = "log";
    div.innerHTML = `
      <div class="muted">
        <span class="pill">${item.mode}</span>
        <span class="pill">${item.env || "dev"}</span>
        <span>${item.ts}</span>
      </div>
      <div><strong>Prompt:</strong> ${escapeHtml(item.prompt || "")}</div>
      <div><strong>Reply:</strong> ${escapeHtml(item.reply || "")}</div>
    `;
    logsEl.appendChild(div);
  }
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

async function sendPrompt() {
  const prompt = document.getElementById("prompt").value;
  const replyEl = document.getElementById("reply");
  const modeEl = document.getElementById("mode");

  replyEl.textContent = "Loading...";
  modeEl.textContent = "";

  const res = await fetch("/api/generate", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ prompt })
  });

  const data = await res.json();
  replyEl.textContent = data.reply || "(no reply)";
  modeEl.textContent = `Mode: ${data.mode || "unknown"}`;

  await loadLogs();
}

document.getElementById("send").addEventListener("click", sendPrompt);
loadLogs();