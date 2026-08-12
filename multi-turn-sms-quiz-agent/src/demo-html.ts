export const BRAND_VERSION = "quiz-agent-2026-08-11-07";

export function demoHtml(defaultSender: string): string {
  const sender = escapeHtml(defaultSender);

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Telnyx SMS Quiz Agent</title>
  <style>
    :root {
      --page: #080b0d;
      --surface: #f7faf8;
      --surface-2: #eef4f1;
      --ink: #111817;
      --muted: #62706b;
      --line: #d7e2dd;
      --green: #00e3aa;
      --green-dark: #00a77d;
      --blue: #1d7afc;
      --amber: #b7791f;
      --red: #d83a34;
      --dark: #101716;
      --dark-2: #182321;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: var(--page);
      color: var(--surface);
      font: 15px/1.45 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    main {
      width: min(460px, calc(100vw - 28px));
      min-height: 100vh;
      margin: 0 auto;
      padding: 22px 0;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .phone {
      width: min(100%, 420px);
      border: 1px solid #2a3431;
      border-radius: 34px;
      background: #050706;
      padding: 12px;
      box-shadow: 0 24px 70px rgba(0, 0, 0, .42);
    }
    .screen {
      height: min(780px, calc(100vh - 70px));
      min-height: 620px;
      border-radius: 24px;
      overflow: hidden;
      background: var(--surface);
      color: var(--ink);
      display: grid;
      grid-template-rows: auto auto 1fr auto;
    }
    .topbar {
      background: var(--dark);
      color: var(--surface);
      padding: 16px 18px 14px;
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      align-items: center;
    }
    .brand { color: var(--green); font-weight: 900; font-size: 12px; letter-spacing: 0; text-transform: uppercase; }
    h1 { margin: 2px 0 0; font-size: 20px; letter-spacing: 0; line-height: 1.1; }
    .live {
      border: 1px solid rgba(0, 227, 170, .35);
      color: var(--green);
      border-radius: 999px;
      padding: 5px 9px;
      font-size: 12px;
      font-weight: 800;
      white-space: nowrap;
    }
    .stats {
      background: var(--dark-2);
      color: var(--surface);
      display: grid;
      grid-template-columns: minmax(86px, 1.35fr) minmax(52px, .75fr) minmax(66px, 1fr) minmax(52px, .75fr);
      gap: 1px;
      border-top: 1px solid #263531;
    }
    .stat {
      min-width: 0;
      padding: 11px 9px;
      background: #111b19;
    }
    .stat span {
      display: block;
      color: #99aaa4;
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .stat strong {
      display: block;
      margin-top: 2px;
      font-size: 15px;
      line-height: 1.15;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .messages {
      min-height: 0;
      padding: 18px 14px;
      overflow: auto;
      display: flex;
      flex-direction: column-reverse;
      gap: 10px;
      background:
        linear-gradient(180deg, rgba(247, 250, 248, .88), rgba(247, 250, 248, .98)),
        repeating-linear-gradient(0deg, #eef4f1 0, #eef4f1 1px, transparent 1px, transparent 28px);
    }
    .empty {
      margin: auto;
      width: min(260px, 100%);
      border: 1px dashed var(--line);
      border-radius: 12px;
      padding: 20px;
      color: var(--muted);
      text-align: center;
      background: rgba(255, 255, 255, .68);
    }
    .bubble {
      max-width: 84%;
      border-radius: 18px;
      padding: 10px 12px;
      box-shadow: 0 1px 2px rgba(20, 30, 28, .08);
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font-weight: 600;
    }
    .bubble.agent {
      align-self: flex-start;
      background: #ffffff;
      border: 1px solid var(--line);
      border-bottom-left-radius: 5px;
    }
    .bubble.user {
      align-self: flex-end;
      background: var(--green);
      color: #00120d;
      border-bottom-right-radius: 5px;
    }
    .bubble.system {
      align-self: center;
      max-width: 92%;
      color: var(--muted);
      background: var(--surface-2);
      border: 1px solid var(--line);
      text-align: center;
      font-size: 13px;
      font-weight: 700;
    }
    .bubble.final {
      border-color: rgba(0, 227, 170, .55);
      box-shadow: 0 0 0 3px rgba(0, 227, 170, .13);
    }
    .question-body {
      display: grid;
      gap: 10px;
    }
    .question-title {
      font-weight: 850;
      line-height: 1.35;
    }
    .choices {
      display: grid;
      gap: 8px;
    }
    .choice-line {
      display: grid;
      grid-template-columns: 30px 1fr;
      gap: 8px;
      align-items: start;
      padding: 8px 9px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: var(--surface-2);
      line-height: 1.3;
    }
    .choice-label {
      display: inline-grid;
      place-items: center;
      width: 25px;
      height: 25px;
      border-radius: 7px;
      background: var(--dark);
      color: var(--green);
      font-size: 13px;
      font-weight: 900;
    }
    .meta {
      display: flex;
      gap: 7px;
      align-items: center;
      margin-top: 7px;
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
    }
    .bubble.user .meta { color: rgba(0, 18, 13, .68); justify-content: flex-end; }
    .chip {
      border-radius: 999px;
      padding: 2px 7px;
      color: #ffffff;
      background: var(--blue);
      text-transform: uppercase;
      font-size: 10px;
      letter-spacing: 0;
    }
    .chip.grade { background: var(--amber); }
    .chip.wrong { background: var(--red); }
    .chip.final { background: var(--green-dark); }
    .composer {
      border-top: 1px solid var(--line);
      background: #ffffff;
      padding: 12px;
      display: grid;
      gap: 10px;
    }
    .quick {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
    }
    button {
      border: 0;
      border-radius: 8px;
      padding: 10px;
      font: inherit;
      font-weight: 850;
      cursor: pointer;
      background: var(--green);
      color: #00120d;
    }
    button:hover { background: #20efbc; }
    button.secondary {
      color: var(--ink);
      background: var(--surface-2);
      border: 1px solid var(--line);
    }
    button.secondary:hover { border-color: var(--green-dark); background: #e4f2ed; }
    button:disabled { opacity: .55; cursor: not-allowed; }
    form {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      align-items: center;
    }
    input {
      min-width: 0;
      width: 100%;
      height: 42px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 0 14px;
      font: inherit;
      color: var(--ink);
      background: var(--surface-2);
    }
    input:focus {
      outline: 3px solid rgba(0, 227, 170, .24);
      border-color: var(--green-dark);
      background: #ffffff;
    }
    .visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
    @media (max-width: 900px) {
      main {
        min-height: auto;
        align-items: start;
        justify-content: center;
      }
      .screen { min-height: 620px; height: auto; }
    }
    @media (max-width: 430px) {
      main { width: min(100vw - 16px, 1180px); padding: 8px 0; gap: 12px; }
      .phone { padding: 8px; border-radius: 28px; }
      .screen { min-height: calc(100vh - 32px); border-radius: 21px; }
      .stats { grid-template-columns: repeat(2, 1fr); }
      .quick { grid-template-columns: repeat(2, 1fr); }
      .answer-grid button { min-height: 60px; }
    }
  </style>
</head>
<body>
  <main>
    <section class="phone" aria-label="SMS quiz simulator">
      <div class="screen">
        <div class="topbar">
          <div>
            <div class="brand">Telnyx</div>
            <h1>Edge Quiz</h1>
          </div>
          <div class="live" id="live">Live</div>
        </div>

        <div class="stats">
          <div class="stat"><span>Phase</span><strong id="phase">idle</strong></div>
          <div class="stat"><span>Score</span><strong id="score">0</strong></div>
          <div class="stat"><span>Level</span><strong id="difficulty">easy</strong></div>
          <div class="stat"><span>Turn</span><strong id="turn">0</strong></div>
        </div>

        <div id="messages" class="messages">
          <div class="empty">Start a quiz to see the SMS conversation.</div>
        </div>

        <div class="composer">
          <div class="quick">
            <button class="secondary" type="button" data-message="start">Start</button>
            <button class="secondary" type="button" data-message="A">A</button>
            <button class="secondary" type="button" data-message="B">B</button>
            <button class="secondary" type="button" data-message="C">C</button>
          </div>
          <form id="form">
            <input id="message" name="message" value="start" autocomplete="off" />
            <button id="send" type="submit">Send</button>
          </form>
        </div>
      </div>
    </section>
    <input class="visually-hidden" id="from" value="${sender}" aria-hidden="true" tabindex="-1" />
  </main>

  <script>
    const form = document.getElementById("form");
    const message = document.getElementById("message");
    const from = document.getElementById("from");
    const send = document.getElementById("send");
    const messages = document.getElementById("messages");

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, (char) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      })[char]);
    }

    function roleForBubble(event) {
      if (event.role === "answer") return "user";
      if (event.role === "system") return "system";
      if (event.role === "final") return "agent final";
      return "agent";
    }

    function chipClass(event) {
      if (event.role === "grade" && !event.correct) return "chip wrong";
      return "chip " + event.role;
    }

    function formatQuestionText(text) {
      const normalized = String(text)
        .replace(/\\s+([abc])\\)\\s*/gi, (_, letter) => "\\n" + letter.toUpperCase() + ") ")
        .replace(/^([abc])\\)/gim, (_, letter) => letter.toUpperCase() + ")");
      const lines = normalized.split(/\\n+/).map((line) => line.trim()).filter(Boolean);
      const choices = [];
      const prompt = [];
      for (const line of lines) {
        const match = line.match(/^([ABC])\\)\\s*(.+)$/i);
        if (match) {
          choices.push({ label: match[1].toUpperCase(), text: match[2] });
        } else {
          prompt.push(line);
        }
      }
      if (!choices.length) return escapeHtml(text);
      return '<div class="question-body">' +
        '<div class="question-title">' + escapeHtml(prompt.join("\\n")) + '</div>' +
        '<div class="choices">' + choices.map((choice) =>
          '<div class="choice-line"><span class="choice-label">' + escapeHtml(choice.label) + '</span><span>' + escapeHtml(choice.text) + '</span></div>'
        ).join("") + '</div>' +
      '</div>';
    }

    function eventHtml(event) {
      if (event.role === "question") return formatQuestionText(event.text);
      return escapeHtml(event.text);
    }

    function renderStatus(status) {
      const turn = Number(status.turn || 0);
      const max = 5;
      document.getElementById("phase").textContent = status.phase || "idle";
      document.getElementById("score").textContent = String(status.score || 0);
      document.getElementById("difficulty").textContent = status.difficulty || "easy";
      document.getElementById("turn").textContent = String(turn);
      document.getElementById("live").textContent = status.phase === "asking" ? "Thinking" : "Live";
    }

    function renderMessages(events) {
      if (!events.length) {
        messages.innerHTML = '<div class="empty">Start a quiz to see the SMS conversation.</div>';
        return;
      }
      const chronological = [...events].reverse();
      messages.innerHTML = chronological.map((event) => {
        const when = new Date(event.at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        return '<div class="bubble ' + roleForBubble(event) + '">' +
          eventHtml(event) +
          '<div class="meta"><span class="' + chipClass(event) + '">' + escapeHtml(event.role) + '</span><span>' + when + '</span></div>' +
        '</div>';
      }).reverse().join("");
    }

    async function load() {
      const sender = encodeURIComponent(from.value.trim());
      const [eventsRes, statusRes] = await Promise.all([
        fetch('/events?from=' + sender),
        fetch('/status?from=' + sender)
      ]);
      if (!eventsRes.ok || !statusRes.ok) throw new Error("Unable to load quiz state.");
      const eventsPayload = await eventsRes.json();
      const statusPayload = await statusRes.json();
      const events = eventsPayload.events || [];
      renderMessages(events);
      renderStatus(statusPayload.status || {});
    }

    async function submitText(text) {
      const trimmed = String(text || "").trim();
      if (!trimmed) return;
      send.disabled = true;
      try {
        const res = await fetch("/send", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ from: from.value.trim(), text: trimmed })
        });
        if (!res.ok) throw new Error("Unable to send message.");
        message.value = "";
        setTimeout(load, 600);
      } catch (error) {
        console.error(error);
      } finally {
        send.disabled = false;
      }
    }

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      submitText(message.value);
    });

    document.querySelectorAll("[data-message]").forEach((button) => {
      button.addEventListener("click", () => submitText(button.dataset.message));
    });

    load().catch((error) => console.error(error));
    setInterval(() => load().catch(() => {}), 1500);
  </script>
</body>
</html>`;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char] || char);
}
