export const BRAND_VERSION = "agent-tools-edge-v1";

export function demoHtml(defaultSender: string): string {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Telnyx Agent Tool Calling</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fb;
      --ink: #070707;
      --muted: #5d6370;
      --panel: #ffffff;
      --panel-soft: #f1f3f7;
      --line: #d8dde8;
      --line-strong: #b8c0cf;
      --green: #00e19a;
      --green-dark: #00b67d;
      --purple: #6715f9;
      --red: #c83232;
      --amber: #a86600;
      --shadow: 0 12px 32px rgba(7, 7, 7, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }
    button, input, textarea { font: inherit; }
    .topbar {
      background: #070707;
      color: #ffffff;
      border-bottom: 4px solid var(--green);
    }
    .topbar-inner {
      width: min(1220px, calc(100% - 32px));
      min-height: 72px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 14px;
      min-width: 0;
    }
    .mark {
      width: 34px;
      height: 34px;
      border-radius: 7px;
      background: var(--green);
      color: #070707;
      display: grid;
      place-items: center;
      font-weight: 900;
      font-size: 20px;
      line-height: 1;
    }
    h1 {
      margin: 0;
      font-size: 21px;
      line-height: 1.15;
      letter-spacing: 0;
    }
    .subtitle {
      margin: 4px 0 0;
      color: #cfd5df;
      font-size: 13px;
    }
    .version {
      border: 1px solid rgba(255,255,255,0.22);
      border-radius: 7px;
      padding: 7px 10px;
      color: #dce2ea;
      font-size: 12px;
      white-space: nowrap;
    }
    main {
      width: min(1220px, calc(100% - 32px));
      margin: 0 auto;
      padding: 22px 0 40px;
    }
    .status-strip {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 16px;
    }
    .metric {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px 14px;
      min-width: 0;
    }
    .metric span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 4px;
    }
    .metric strong {
      font-size: 15px;
      overflow-wrap: anywhere;
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(320px, 410px) 1fr;
      gap: 16px;
      align-items: start;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }
    .composer {
      padding: 16px;
      position: sticky;
      top: 16px;
    }
    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
    }
    .panel-header h2 {
      margin: 0;
      font-size: 15px;
      letter-spacing: 0;
    }
    .panel-body { padding: 14px 16px 16px; }
    label {
      display: block;
      margin-bottom: 6px;
      font-size: 12px;
      font-weight: 750;
      color: #222833;
    }
    input, textarea {
      width: 100%;
      border: 1px solid var(--line-strong);
      border-radius: 7px;
      background: #ffffff;
      color: var(--ink);
      padding: 10px 11px;
      outline: none;
    }
    input:focus, textarea:focus {
      border-color: var(--purple);
      box-shadow: 0 0 0 3px rgba(103, 21, 249, 0.12);
    }
    textarea {
      min-height: 118px;
      resize: vertical;
    }
    .field { margin-bottom: 13px; }
    .quick-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-bottom: 13px;
    }
    .ghost {
      border: 1px solid var(--line-strong);
      background: #ffffff;
      color: var(--ink);
      border-radius: 7px;
      min-height: 38px;
      padding: 8px 10px;
      cursor: pointer;
      font-weight: 750;
    }
    .ghost:hover { border-color: var(--purple); }
    .actions {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .primary {
      appearance: none;
      border: 0;
      background: var(--green);
      color: #070707;
      border-radius: 7px;
      min-height: 42px;
      padding: 10px 16px;
      font-weight: 850;
      cursor: pointer;
    }
    .primary:hover { background: var(--green-dark); }
    button:disabled { opacity: 0.62; cursor: wait; }
    .status {
      min-height: 20px;
      color: var(--muted);
      font-size: 13px;
      overflow-wrap: anywhere;
    }
    .status.error { color: var(--red); }
    .status.ok { color: #087a57; }
    .stack {
      display: grid;
      gap: 16px;
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .icon-btn {
      border: 1px solid var(--line-strong);
      background: #ffffff;
      color: var(--ink);
      border-radius: 7px;
      width: 36px;
      height: 34px;
      display: grid;
      place-items: center;
      cursor: pointer;
      font-weight: 850;
    }
    .icon-btn:hover { border-color: var(--purple); }
    .items {
      display: grid;
      gap: 10px;
    }
    .item {
      border: 1px solid #e4e8f0;
      border-radius: 8px;
      background: #fbfcfe;
      padding: 12px;
    }
    .item-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 8px;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      border-radius: 999px;
      padding: 3px 8px;
      background: #e8fff6;
      color: #075f45;
      font-size: 12px;
      font-weight: 800;
    }
    .badge.sms { background: #f1eaff; color: #4b10bd; }
    .badge.error { background: #ffecec; color: #9b1c1c; }
    .badge.neutral { background: #edf1f7; color: #404856; }
    .message-text {
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      line-height: 1.42;
    }
    code, pre {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size: 12px;
    }
    code {
      color: #28313f;
      overflow-wrap: anywhere;
    }
    pre {
      color: #141b24;
      background: var(--panel-soft);
      border: 1px solid #e1e5ed;
      border-radius: 7px;
      margin: 8px 0 0;
      padding: 10px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      max-height: 260px;
      overflow: auto;
    }
    .empty {
      color: var(--muted);
      border: 1px dashed var(--line-strong);
      border-radius: 8px;
      padding: 16px;
      text-align: center;
      background: #fbfcfe;
    }
    .hint {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
      margin-top: 10px;
    }
    @media (max-width: 860px) {
      .topbar-inner, main { width: min(100% - 20px, 1220px); }
      .topbar-inner { align-items: flex-start; flex-direction: column; padding: 16px 0; gap: 12px; }
      .status-strip, .layout { grid-template-columns: 1fr; }
      .composer { position: static; }
    }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand">
        <div class="mark" aria-hidden="true">T</div>
        <div>
          <h1>Agent with Tool Calling</h1>
          <p class="subtitle">Telnyx Edge agent using GLM-5.2, tool calls, Call Control, and demo SMS.</p>
        </div>
      </div>
      <div class="version">${BRAND_VERSION}</div>
    </div>
  </header>

  <main>
    <div class="status-strip">
      <div class="metric"><span>Voice</span><strong id="voice-state">Checking...</strong></div>
      <div class="metric"><span>SMS Transport</span><strong id="sms-state">Checking...</strong></div>
      <div class="metric"><span>Active Sender</span><strong id="sender-state">${escapeHtml(defaultSender)}</strong></div>
    </div>

    <div class="layout">
      <form id="composer" class="panel composer">
        <div class="panel-header" style="padding: 0 0 14px; border-bottom: 0;">
          <h2>Run a Tool Call</h2>
        </div>
        <div class="field">
          <label for="from">Conversation sender</label>
          <input id="from" name="from" value="${escapeHtml(defaultSender)}" inputmode="tel" autocomplete="tel">
        </div>
        <div class="quick-actions">
          <button class="ghost" type="button" data-template="Call me at +15551234567">Call demo</button>
          <button class="ghost" type="button" data-template="Text +13125550001 hi from the Telnyx agent">SMS demo</button>
        </div>
        <div class="field">
          <label for="text">User message</label>
          <textarea id="text" name="text">Call me at +15551234567</textarea>
        </div>
        <div class="actions">
          <button id="send" class="primary" type="submit">Run</button>
          <span id="status" class="status"></span>
        </div>
        <p class="hint">Call Control is live when voice is configured. SMS remains in demo mode unless the Edge env is changed to production.</p>
      </form>

      <div class="stack">
        <section class="panel">
          <div class="panel-header">
            <h2>Conversation</h2>
            <div class="toolbar">
              <button id="refresh" class="icon-btn" type="button" title="Refresh">↻</button>
            </div>
          </div>
          <div class="panel-body">
            <div id="conversation" class="items"></div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h2>Tool Ledger</h2>
            <span class="badge neutral" id="tool-count">0 calls</span>
          </div>
          <div class="panel-body">
            <div id="events" class="items"></div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h2>Process Log</h2>
            <span class="badge neutral" id="loop-state">Idle</span>
          </div>
          <div class="panel-body">
            <div id="process" class="items"></div>
          </div>
        </section>
      </div>
    </div>
  </main>

  <script>
    const form = document.querySelector("#composer");
    const from = document.querySelector("#from");
    const text = document.querySelector("#text");
    const status = document.querySelector("#status");
    const send = document.querySelector("#send");
    const refresh = document.querySelector("#refresh");
    const events = document.querySelector("#events");
    const conversation = document.querySelector("#conversation");
    const process = document.querySelector("#process");
    const voiceState = document.querySelector("#voice-state");
    const smsState = document.querySelector("#sms-state");
    const senderState = document.querySelector("#sender-state");
    const toolCount = document.querySelector("#tool-count");
    const loopState = document.querySelector("#loop-state");
    let pollTimer = null;

    function time(ts) {
      return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    }

    function pretty(value) {
      return JSON.stringify(value, null, 2);
    }

    function setStatus(message, tone) {
      status.className = "status" + (tone ? " " + tone : "");
      status.textContent = message || "";
    }

    function badgeForTool(row) {
      if (row.result && row.result.ok === false) return "badge error";
      if (row.tool === "send_sms") return "badge sms";
      if (row.tool === "make_call") return "badge";
      return "badge neutral";
    }

    function render(data) {
      conversation.innerHTML = "";
      const messages = [...(data.conversation || [])].reverse();
      if (!messages.length) {
        conversation.innerHTML = '<div class="empty">No conversation yet.</div>';
      } else {
        for (const item of messages) {
          const div = document.createElement("div");
          div.className = "item";
          div.innerHTML = '<div class="item-head"><strong></strong><span></span></div><div class="message-text"></div>';
          div.querySelector("strong").textContent = item.role;
          div.querySelector("span").textContent = time(item.at);
          div.querySelector(".message-text").textContent = item.content;
          conversation.appendChild(div);
        }
      }

      events.innerHTML = "";
      const rows = [...(data.toolEvents || [])].reverse();
      toolCount.textContent = rows.length === 1 ? "1 call" : rows.length + " calls";
      if (!rows.length) {
        events.innerHTML = '<div class="empty">No tool calls yet.</div>';
      } else {
        for (const row of rows) {
          const div = document.createElement("div");
          div.className = "item";
          div.innerHTML = '<div class="item-head"><span class="badge"></span><span></span></div><code></code><pre></pre>';
          const badge = div.querySelector(".badge");
          badge.className = badgeForTool(row);
          badge.textContent = row.tool;
          div.querySelector(".item-head span:last-child").textContent = time(row.at);
          div.querySelector("code").textContent = row.tool_call_id;
          div.querySelector("pre").textContent = pretty({ args: row.args, result: row.result, status: row.status });
          events.appendChild(div);
        }
      }

      process.innerHTML = "";
      const logs = [...(data.processLog || [])].reverse();
      const latest = logs[logs.length - 1];
      loopState.textContent = latest ? latest.finish_reason || latest.phase : "Idle";
      if (!logs.length) {
        process.innerHTML = '<div class="empty">No process log yet.</div>';
      } else {
        for (const row of logs) {
          const div = document.createElement("div");
          div.className = "item";
          div.innerHTML = '<div class="item-head"><strong></strong><span></span></div><code></code><pre></pre>';
          div.querySelector("strong").textContent = row.phase + " #" + row.iteration;
          div.querySelector("span").textContent = time(row.at);
          div.querySelector("code").textContent = "tool_choice=" + row.tool_choice;
          div.querySelector("pre").textContent = pretty({ finish_reason: row.finish_reason, tool_calls: row.tool_calls, note: row.note });
          process.appendChild(div);
        }
      }
    }

    async function load() {
      senderState.textContent = from.value;
      const res = await fetch('/events?from=' + encodeURIComponent(from.value) + '&limit=60');
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      render(data);
      return data;
    }

    async function loadHealth() {
      const res = await fetch('/health');
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      voiceState.textContent = data.voiceConfigured ? "Configured" : "Not configured";
      smsState.textContent = data.smsTransport === "production" ? "Production" : "Demo";
    }

    function finalResponseVisible(data, baselineAssistantCount) {
      const assistantCount = (data.conversation || []).filter((item) => item.role === "assistant").length;
      const latestLog = (data.processLog || [])[0];
      return assistantCount > baselineAssistantCount || Boolean(latestLog && latestLog.note === "model returned final assistant message");
    }

    async function pollForResult(baselineAssistantCount) {
      let attempts = 0;
      clearInterval(pollTimer);
      pollTimer = setInterval(async () => {
        attempts += 1;
        try {
          const data = await load();
          if (finalResponseVisible(data, baselineAssistantCount)) {
            clearInterval(pollTimer);
            setStatus("Complete", "ok");
            send.disabled = false;
          } else if (attempts >= 18) {
            clearInterval(pollTimer);
            setStatus("Still processing. Use refresh to check again.");
            send.disabled = false;
          }
        } catch (error) {
          clearInterval(pollTimer);
          setStatus(error instanceof Error ? error.message : "Refresh failed", "error");
          send.disabled = false;
        }
      }, 1200);
    }

    document.querySelectorAll("[data-template]").forEach((button) => {
      button.addEventListener("click", () => {
        text.value = button.getAttribute("data-template") || "";
        text.focus();
      });
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearInterval(pollTimer);
      setStatus("Starting tool loop...");
      send.disabled = true;
      try {
        const before = await load().catch(() => ({ conversation: [] }));
        const baselineAssistantCount = (before.conversation || []).filter((item) => item.role === "assistant").length;
        const res = await fetch("/send", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ from: from.value, text: text.value }),
        });
        if (!res.ok) throw new Error(await res.text());
        setStatus("Queued. Waiting for the model and tool result...");
        await pollForResult(baselineAssistantCount);
      } catch (error) {
        setStatus(error instanceof Error ? error.message : "Request failed", "error");
        send.disabled = false;
      }
    });

    refresh.addEventListener("click", () => {
      setStatus("Refreshing...");
      Promise.all([loadHealth(), load()])
        .then(() => setStatus(""))
        .catch((error) => setStatus(error instanceof Error ? error.message : "Refresh failed", "error"));
    });

    from.addEventListener("change", () => {
      senderState.textContent = from.value;
      load().catch(() => {});
    });

    Promise.all([loadHealth(), load()]).catch(() => {});
  </script>
</body>
</html>`;
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
