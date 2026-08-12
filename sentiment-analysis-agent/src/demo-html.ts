export const BRAND_VERSION = "telnyx-brand-2026-08-11-02";

export const DEMO_HTML = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Telnyx Sentiment Analysis Agent</title>
  <style>
    :root {
      color-scheme: light;
      --telnyx-black: #000000;
      --telnyx-green: #00e3aa;
      --telnyx-green-dark: #00b989;
      --bg: #050606;
      --ink: #f7fff9;
      --muted: #aab7b2;
      --line: #20322d;
      --panel: #0d1110;
      --panel-strong: #111917;
      --positive: #00e3aa;
      --neutral: #c8d2cf;
      --negative: #ff5a52;
      --accent: #00e3aa;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--telnyx-black);
      color: var(--ink);
      font: 15px/1.45 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    main {
      width: min(1120px, calc(100vw - 32px));
      margin: 24px auto;
      display: grid;
      grid-template-columns: 360px 1fr;
      gap: 18px;
      align-items: start;
    }
    header {
      grid-column: 1 / -1;
      text-align: center;
      border-bottom: 1px solid var(--line);
      padding: 8px 0 18px;
    }
    .brand {
      color: var(--telnyx-green);
      font-weight: 900;
      font-size: 13px;
      letter-spacing: 0;
      text-transform: uppercase;
      margin-bottom: 8px;
    }
    h1 { margin: 0; font-size: 34px; line-height: 1.1; letter-spacing: 0; color: var(--telnyx-green); }
    h2 { margin: 0 0 14px; font-size: 16px; letter-spacing: 0; }
    .sub { color: var(--muted); margin: 8px auto 0; max-width: 720px; }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      box-shadow: 0 18px 44px rgba(0, 227, 170, 0.08);
    }
    label { display: block; font-weight: 650; margin: 14px 0 6px; }
    input, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px 11px;
      font: inherit;
      color: var(--ink);
      background: var(--telnyx-black);
    }
    input:focus, textarea:focus {
      outline: 2px solid rgba(0, 227, 170, 0.42);
      border-color: var(--telnyx-green);
    }
    .masked-phone {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px 11px;
      color: var(--muted);
      background: var(--telnyx-black);
      font-weight: 700;
    }
    textarea { min-height: 116px; resize: vertical; }
    .actions { display: flex; gap: 8px; margin-top: 12px; }
    button {
      border: 0;
      border-radius: 6px;
      padding: 10px 12px;
      font-weight: 700;
      cursor: pointer;
      background: var(--accent);
      color: var(--telnyx-black);
    }
    button:hover { background: var(--telnyx-green-dark); }
    button.secondary { background: var(--panel-strong); color: var(--telnyx-green); border: 1px solid var(--line); }
    button:disabled { opacity: .55; cursor: not-allowed; }
    .examples {
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
      margin-top: 16px;
    }
    .example {
      background: var(--panel-strong);
      color: var(--ink);
      text-align: left;
      font-weight: 600;
      border: 1px solid var(--line);
    }
    .example:hover { border-color: var(--telnyx-green); color: var(--telnyx-green); background: #0b1714; }
    .log { display: grid; gap: 10px; }
    .row {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 13px;
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px 12px;
      background: var(--panel-strong);
    }
    .message { font-weight: 700; }
    .meta, .reply { color: var(--muted); font-size: 13px; }
    .reply {
      grid-column: 1 / -1;
      border-top: 1px solid var(--line);
      padding-top: 9px;
    }
    .badges { display: flex; gap: 6px; align-items: start; flex-wrap: wrap; justify-content: end; }
    .badge {
      border-radius: 999px;
      padding: 4px 8px;
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0;
    }
    .positive { color: var(--telnyx-black); background: var(--positive); }
    .neutral { color: var(--telnyx-black); background: var(--neutral); }
    .negative { color: #ffffff; background: var(--negative); }
    .escalated { color: var(--telnyx-black); background: var(--telnyx-green); text-transform: none; }
    .empty {
      color: var(--muted);
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 22px;
      text-align: center;
    }
    @media (max-width: 780px) {
      main { grid-template-columns: 1fr; margin: 16px auto; }
      h1 { font-size: 28px; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div class="brand">Telnyx</div>
      <h1>Sentiment Analysis Agent</h1>
      <p class="sub">Browser simulator for inbound SMS. The agent, LLM classification, SQL log, and escalation decision run on the deployed Edge function.</p>
    </header>

    <section>
      <h2>Send Simulated SMS</h2>
      <form id="form">
        <label for="from">Sender</label>
        <input id="from" name="from" value="+15551234567" type="hidden" />
        <div class="masked-phone" aria-hidden="true">Demo sender · +1555••••4567</div>
        <label for="message">Message</label>
        <textarea id="message" name="message">this is broken and nobody is helping me</textarea>
        <div class="actions">
          <button id="send" type="submit">Send</button>
          <button class="secondary" type="button" id="refresh">Refresh</button>
        </div>
      </form>
      <div class="examples">
        <button class="example" type="button" data-message="I love this app, just paid for a year">Positive example</button>
        <button class="example" type="button" data-message="What are your hours?">Neutral example</button>
        <button class="example" type="button" data-message="this is broken and nobody is helping me, I want a refund">Negative example</button>
      </div>
    </section>

    <section>
      <h2>Live Sentiment Log</h2>
      <div id="log" class="log">
        <div class="empty">No messages yet.</div>
      </div>
    </section>
  </main>

  <script>
    const form = document.getElementById("form");
    const message = document.getElementById("message");
    const from = document.getElementById("from");
    const send = document.getElementById("send");
    const refresh = document.getElementById("refresh");
    const log = document.getElementById("log");

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, (char) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      })[char]);
    }

    function maskPhone(value) {
      const digits = String(value).replace(/\\D/g, "");
      if (digits.length < 8) return "Demo sender";
      return "+" + digits.slice(0, 4) + "••••" + digits.slice(-4);
    }

    function render(events) {
      if (!events.length) {
        log.innerHTML = '<div class="empty">No messages yet.</div>';
        return;
      }
      log.innerHTML = events.map((event) => {
        const label = escapeHtml(event.label);
        const when = new Date(event.at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
        return '<article class="row">' +
          '<div><div class="message">' + escapeHtml(event.message) + '</div>' +
          '<div class="meta">' + escapeHtml(maskPhone(event.sender)) + ' · ' + when + '</div></div>' +
          '<div class="badges"><span class="badge ' + label + '">' + label + ' ' + Number(event.score).toFixed(2) + '</span>' +
          (event.escalated ? '<span class="badge escalated">Human escalation triggered</span>' : '') + '</div>' +
          '<div class="reply"><strong>Agent reply:</strong> ' + escapeHtml(event.reply) + '</div>' +
        '</article>';
      }).join("");
    }

    async function loadEvents() {
      const sender = encodeURIComponent(from.value.trim());
      const res = await fetch('/events?from=' + sender);
      if (!res.ok) throw new Error("Unable to load events.");
      const payload = await res.json();
      render(payload.events || []);
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      send.disabled = true;
      try {
        const res = await fetch("/send", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ from: from.value.trim(), text: message.value.trim() })
        });
        if (!res.ok) throw new Error("Unable to send message.");
        setTimeout(loadEvents, 750);
      } catch (error) {
        console.error(error);
      } finally {
        send.disabled = false;
      }
    });

    refresh.addEventListener("click", loadEvents);
    document.querySelectorAll("[data-message]").forEach((button) => {
      button.addEventListener("click", () => { message.value = button.dataset.message; });
    });

    loadEvents().catch((error) => {
      console.error(error);
    });
    setInterval(() => loadEvents().catch(() => {}), 1500);
  </script>
</body>
</html>`;
