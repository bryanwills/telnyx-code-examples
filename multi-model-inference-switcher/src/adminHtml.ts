export const ADMIN_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Multi-Model Inference Switcher — Telnyx</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --telnyx-cream: #FEFDF5;
    --telnyx-black: #000000;
    --telnyx-green: #00E3AA;
    --telnyx-tan: #E6E3D3;
    --inference-blue: #3434EF;
    --bright-20: #CCF9EE;
    --inference-bright-20: #AED3F9;
    --inference-bright-10: #D6EFFC;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Inter', sans-serif;
    background: var(--telnyx-cream);
    color: var(--telnyx-black);
    min-height: 100vh;
    padding: 0;
  }
  .header {
    background: var(--telnyx-black);
    color: var(--telnyx-cream);
    padding: 24px 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .header h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 24px;
    letter-spacing: -0.5px;
  }
  .header .logo {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .header .logo-mark {
    width: 28px;
    height: 28px;
    background: var(--telnyx-green);
    clip-path: polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%);
  }
  .header .logo-text {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 22px;
    letter-spacing: -1px;
    text-transform: lowercase;
  }
  .container {
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 24px;
  }
  .model-bar {
    background: var(--inference-bright-10);
    border: 2px solid var(--inference-bright-20);
    border-radius: 16px;
    padding: 20px 28px;
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 32px;
  }
  .model-bar .label {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 15px;
    color: var(--telnyx-black);
    white-space: nowrap;
  }
  .model-bar .label .dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--telnyx-green);
    margin-right: 8px;
    vertical-align: middle;
    box-shadow: 0 0 8px var(--telnyx-green);
  }
  .model-select {
    flex: 1;
    padding: 10px 16px;
    border: 2px solid var(--telnyx-black);
    border-radius: 10px;
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    font-weight: 500;
    background: white;
    color: var(--telnyx-black);
    cursor: pointer;
    outline: none;
  }
  .model-select:focus { border-color: var(--inference-blue); }
  .switch-btn {
    padding: 10px 24px;
    background: var(--telnyx-black);
    color: var(--telnyx-green);
    border: none;
    border-radius: 10px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 15px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .switch-btn:hover { background: var(--inference-blue); color: white; }
  .switch-btn:disabled { opacity: 0.5; cursor: wait; }
  .chat-container {
    background: white;
    border: 2px solid var(--telnyx-tan);
    border-radius: 16px;
    overflow: hidden;
    margin-bottom: 16px;
  }
  .chat-header {
    background: var(--telnyx-black);
    color: var(--telnyx-cream);
    padding: 14px 24px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .chat-header .badge {
    background: var(--telnyx-green);
    color: var(--telnyx-black);
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
  }
  .chat-messages {
    padding: 24px;
    max-height: 420px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .msg {
    max-width: 75%;
    padding: 12px 18px;
    border-radius: 14px;
    font-size: 15px;
    line-height: 1.5;
  }
  .msg.user {
    align-self: flex-end;
    background: var(--inference-blue);
    color: white;
    border-bottom-right-radius: 4px;
  }
  .msg.assistant {
    align-self: flex-start;
    background: var(--bright-20);
    color: var(--telnyx-black);
    border-bottom-left-radius: 4px;
  }
  .msg.assistant .model-tag {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    color: var(--inference-blue);
    margin-bottom: 4px;
    font-family: 'Space Grotesk', sans-serif;
  }
  .chat-input {
    display: flex;
    gap: 12px;
    padding: 16px 24px;
    background: var(--telnyx-cream);
    border-top: 1px solid var(--telnyx-tan);
  }
  .chat-input input {
    flex: 1;
    padding: 12px 18px;
    border: 2px solid var(--telnyx-tan);
    border-radius: 10px;
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    outline: none;
    background: white;
  }
  .chat-input input:focus { border-color: var(--inference-blue); }
  .chat-input button {
    padding: 12px 28px;
    background: var(--telnyx-green);
    color: var(--telnyx-black);
    border: none;
    border-radius: 10px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 15px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .chat-input button:hover { transform: scale(1.02); }
  .chat-input button:disabled { opacity: 0.5; cursor: wait; }
  .stats {
    display: flex;
    gap: 16px;
    margin-bottom: 32px;
  }
  .stat-card {
    flex: 1;
    background: white;
    border: 2px solid var(--telnyx-tan);
    border-radius: 12px;
    padding: 16px 20px;
  }
  .stat-card .stat-label {
    font-size: 12px;
    font-weight: 600;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
  }
  .stat-card .stat-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 24px;
    font-weight: 700;
    color: var(--telnyx-black);
  }
  .stat-card .stat-value .unit { font-size: 14px; color: #888; }
  .clear-btn {
    background: transparent;
    border: 1px solid var(--telnyx-tan);
    color: #888;
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 13px;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
  }
  .clear-btn:hover { border-color: var(--telnyx-black); color: var(--telnyx-black); }
  .loading { opacity: 0.5; }
  .empty-state {
    text-align: center;
    padding: 40px;
    color: #888;
    font-size: 15px;
  }
</style>
</head>
<body>
<div class="header">
  <div class="logo">
    <div class="logo-mark"></div>
    <div class="logo-text">telnyx</div>
  </div>
  <h1>Multi-Model Inference Switcher</h1>
</div>

<div class="container">
  <div class="model-bar">
    <div class="label"><span class="dot"></span>Active Model</div>
    <select class="model-select" id="modelSelect"></select>
    <button class="switch-btn" id="switchBtn" onclick="switchModel()">Switch</button>
  </div>

  <div class="stats">
    <div class="stat-card">
      <div class="stat-label">Total Requests</div>
      <div class="stat-value" id="totalRequests">0</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Models Used</div>
      <div class="stat-value" id="modelsUsed">0</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Current Model</div>
      <div class="stat-value" id="currentModel" style="font-size:16px;">—</div>
    </div>
  </div>

  <div class="chat-container">
    <div class="chat-header">
      <span>Chat</span>
      <button class="clear-btn" onclick="clearChat()">Clear</button>
    </div>
    <div class="chat-messages" id="chatMessages">
      <div class="empty-state">Send a message to start chatting. Each reply is tagged with the model that generated it — switch the model above to see the difference live.</div>
    </div>
    <div class="chat-input">
      <input type="text" id="chatInput" placeholder="Type a message..." onkeydown="if(event.key==='Enter') sendMessage()">
      <button id="sendBtn" onclick="sendMessage()">Send</button>
    </div>
  </div>
</div>

<script>
const MODELS = __MODELS_JSON__;
const ACTIVE_MODEL = "__ACTIVE_MODEL__";

async function init() {
  const sel = document.getElementById('modelSelect');
  MODELS.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m.id;
    opt.textContent = m.name + ' (' + m.vendor + ')';
    if (m.id === ACTIVE_MODEL) opt.selected = true;
    sel.appendChild(opt);
  });
  document.getElementById('currentModel').textContent = modelName(ACTIVE_MODEL);
  await loadStats();
  await loadHistory();
}

function modelName(id) {
  const m = MODELS.find(x => x.id === id);
  return m ? m.name : id;
}

async function switchModel() {
  const sel = document.getElementById('modelSelect');
  const btn = document.getElementById('switchBtn');
  btn.disabled = true;
  btn.textContent = 'Switching...';
  try {
    const resp = await fetch('/model', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: sel.value }),
    });
    const data = await resp.json();
    if (resp.ok) {
      document.getElementById('currentModel').textContent = modelName(data.model);
    } else {
      alert(data.error || 'Failed to switch model');
    }
  } catch (e) {
    alert('Network error: ' + e.message);
  }
  btn.disabled = false;
  btn.textContent = 'Switch';
}

async function sendMessage() {
  const input = document.getElementById('chatInput');
  const btn = document.getElementById('sendBtn');
  const text = input.value.trim();
  if (!text) return;
  btn.disabled = true;
  input.value = '';
  appendMessage('user', text);
  appendLoading();
  try {
    const resp = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    const data = await resp.json();
    removeLoading();
    if (resp.ok) {
      appendMessage('assistant', data.reply, data.model);
    } else {
      appendMessage('assistant', 'Error: ' + (data.error || 'unknown'), 'error');
    }
  } catch (e) {
    removeLoading();
    appendMessage('assistant', 'Network error: ' + e.message, 'error');
  }
  btn.disabled = false;
  input.focus();
  await loadStats();
}

function appendMessage(role, content, model) {
  const container = document.getElementById('chatMessages');
  const empty = container.querySelector('.empty-state');
  if (empty) empty.remove();
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  if (role === 'assistant' && model) {
    const tag = document.createElement('div');
    tag.className = 'model-tag';
    tag.textContent = '⚡ ' + modelName(model);
    div.appendChild(tag);
  }
  div.appendChild(document.createTextNode(content));
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function appendLoading() {
  const container = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = 'msg assistant loading';
  div.id = 'loadingMsg';
  div.textContent = 'Thinking...';
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function removeLoading() {
  const el = document.getElementById('loadingMsg');
  if (el) el.remove();
}

async function loadStats() {
  try {
    const resp = await fetch('/history');
    const data = await resp.json();
    document.getElementById('totalRequests').textContent = data.totalRequests || 0;
    const modelCount = Object.keys(data.modelUsage || {}).length;
    document.getElementById('modelsUsed').textContent = modelCount;
  } catch (e) {}
}

async function loadHistory() {
  try {
    const resp = await fetch('/history');
    const data = await resp.json();
    if (data.messages && data.messages.length > 0) {
      const container = document.getElementById('chatMessages');
      const empty = container.querySelector('.empty-state');
      if (empty) empty.remove();
      // We don't have per-message model tags from history, so just show role + content
      data.messages.forEach(m => {
        appendMessage(m.role, m.content, m.model !== 'varies' ? m.model : undefined);
      });
    }
  } catch (e) {}
}

async function clearChat() {
  try {
    await fetch('/clear', { method: 'POST' });
    const container = document.getElementById('chatMessages');
    container.innerHTML = '<div class="empty-state">Chat cleared. Send a new message to start.</div>';
    await loadStats();
  } catch (e) {}
}

init();
</script>
</body>
</html>`;
