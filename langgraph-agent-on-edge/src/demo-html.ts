export const BRAND_VERSION = "langgraph-agent-on-edge v0.1.0";

export function demoHtml(senderNumber: string): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LangGraph Agent on Edge — Demo</title>
<style>
  :root { --green: #00e3aa; --bg: #0a0a0a; --card: #161616; --border: #2a2a2a; --text: #e8e8e8; --muted: #888; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 24px; max-width: 900px; margin: 0 auto; }
  h1 { font-size: 1.5rem; margin-bottom: 8px; }
  h1 span { color: var(--green); }
  .subtitle { color: var(--muted); font-size: 0.9rem; margin-bottom: 24px; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  @media (max-width: 700px) { .grid { grid-template-columns: 1fr; } }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
  .card h2 { font-size: 1.1rem; margin-bottom: 12px; color: var(--green); }
  .chat-log { height: 320px; overflow-y: auto; border: 1px solid var(--border); border-radius: 8px; padding: 12px; margin-bottom: 12px; font-size: 0.85rem; line-height: 1.6; }
  .chat-log .user { color: #7ec8ff; }
  .chat-log .assistant { color: var(--green); }
  .chat-log .meta { color: var(--muted); font-size: 0.75rem; }
  .input-row { display: flex; gap: 8px; }
  .input-row input { flex: 1; padding: 10px 14px; background: var(--bg); border: 1px solid var(--border); border-radius: 8px; color: var(--text); font-size: 0.9rem; }
  .input-row button { padding: 10px 20px; background: var(--green); color: #000; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 0.9rem; }
  .input-row button:disabled { opacity: 0.5; cursor: not-allowed; }
  .state-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.8rem; }
  .state-grid div { padding: 6px 10px; background: var(--bg); border-radius: 6px; border: 1px solid var(--border); }
  .state-grid .label { color: var(--muted); }
  .state-grid .value { color: var(--green); font-family: monospace; }
  .process-log { height: 320px; overflow-y: auto; font-size: 0.75rem; font-family: monospace; line-height: 1.8; color: var(--muted); }
  .process-log .phase { color: var(--green); }
  .sender-info { font-size: 0.8rem; color: var(--muted); margin-bottom: 8px; }
</style>
</head>
<body>
<h1>LangGraph Agent on <span>Edge</span></h1>
<p class="subtitle">Intent → Action → Response StateGraph running inside the Telnyx Agent SDK with zero-credential inference.</p>
<div class="sender-info">Simulating SMS from: <code>${senderNumber}</code></div>
<div class="grid">
  <div class="card">
    <h2>Conversation</h2>
    <div class="chat-log" id="chatLog"></div>
    <div class="input-row">
      <input type="text" id="textInput" placeholder="Send a message... (try: where is order ORD-10042?)" autocomplete="off" />
      <button id="sendBtn" onclick="sendText()">Send</button>
    </div>
  </div>
  <div class="card">
    <h2>Turn State Machine</h2>
    <div class="state-grid" id="stateGrid">
      <div><span class="label">turn</span> <span class="value" id="s-turn">0</span></div>
      <div><span class="label">queuedTurn</span> <span class="value" id="s-queued">0</span></div>
      <div><span class="label">processing</span> <span class="value" id="s-processing">0</span></div>
      <div><span class="label">lastSent</span> <span class="value" id="s-lastsent">0</span></div>
    </div>
    <h2 style="margin-top:16px;">Process Log</h2>
    <div class="process-log" id="processLog"></div>
  </div>
</div>
<script>
const SENDER = ${JSON.stringify(senderNumber)};
async function sendText() {
  const input = document.getElementById('textInput');
  const btn = document.getElementById('sendBtn');
  const text = input.value.trim();
  if (!text) return;
  btn.disabled = true;
  input.value = '';
  try {
    await fetch('/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, from: SENDER }),
    });
  } catch (e) { console.error(e); }
  btn.disabled = false;
  input.focus();
  setTimeout(refresh, 500);
}
input.addEventListener('keydown', e => { if (e.key === 'Enter') sendText(); });
async function refresh() {
  try {
    const res = await fetch('/events?from=' + encodeURIComponent(SENDER) + '&limit=50');
    const data = await res.json();
    const log = document.getElementById('chatLog');
    log.innerHTML = (data.conversation || []).reverse().map(r =>
      '<div class="' + r.role + '">' + r.role + ': ' + escapeHtml(r.content) + '</div>'
    ).join('');
    document.getElementById('s-turn').textContent = data.turnState?.turn ?? 0;
    document.getElementById('s-queued').textContent = data.turnState?.queuedTurn ?? 0;
    document.getElementById('s-processing').textContent = data.turnState?.processingTurn ?? 0;
    document.getElementById('s-lastsent').textContent = data.turnState?.lastSentTurn ?? 0;
    const plog = document.getElementById('processLog');
    plog.innerHTML = (data.processLog || []).reverse().map(r =>
      '<div><span class="phase">' + escapeHtml(r.phase) + '</span> turn=' + r.turn + ' ' + escapeHtml(r.note || '') + '</div>'
    ).join('');
  } catch (e) { console.error(e); }
}
function escapeHtml(s) { return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
refresh();
setInterval(refresh, 2000);
</script>
</body>
</html>`;
}
