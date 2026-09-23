// ─────────────────────────────────────────────────────────────────────────
// dashboardHtml.ts — the visual centerpiece. Served directly by the Edge
// function (no separate hosting): GET / returns this HTML, which then polls
// the JSON endpoints on the same origin (/api/summary, /api/eval).
//
// WHY server-rendered-nothing: everything renders client-side from a couple
// of cheap JSON calls, so the dashboard updates live while loadgen fires —
// that's the on-camera moment: type reports, watch the dashboard move.
// ─────────────────────────────────────────────────────────────────────────

export const DEMO_REGIONS = ["415", "212"];

const BUCKET_LABELS = ["Low", "Normal", "High", "Critical"];
const BUCKET_COLORS = ["#22c55e", "#3b82f6", "#f59e0b", "#ef4444"];
const ISSUE_LABELS: Record<string, string> = {
  no_service: "No service",
  degraded: "Degraded",
  billing: "Billing",
  other: "Other",
};

export const DASHBOARD_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Outage Hotline — Incident Dashboard</title>
<style>
  :root {
    --bg: #0d1220; --panel: #141b2e; --panel2: #101728; --border: #232c45;
    --text: #f5f7fa; --muted: #8a94ad; --accent: #f0142f; --accent2: #d11228;
    --green: #22c55e; --blue: #3b82f6; --orange: #f59e0b; --red: #ef4444;
  }
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: var(--bg); color: var(--text); margin: 0; padding: 28px 20px 60px; }
  .wrap { max-width: 1060px; margin: 0 auto; }
  header { display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; margin-bottom: 6px; }
  h1 { font-size: 24px; margin: 0; letter-spacing: -0.5px; }
  h1 .dot { color: var(--accent); }
  .sub { color: var(--muted); font-size: 13px; }
  .chiprow { display: flex; gap: 8px; align-items: center; margin: 18px 0 22px; flex-wrap: wrap; }
  .chip { background: var(--panel); border: 1px solid var(--border); color: var(--muted);
          padding: 7px 16px; border-radius: 999px; font-size: 14px; cursor: pointer; font-weight: 600; }
  .chip.on { background: var(--accent); border-color: var(--accent); color: #fff; }
  .spacer { flex: 1; }
  .meta { color: var(--muted); font-size: 12px; }
  .search { width: 100%; padding: 8px 12px; border: 1px solid var(--border); border-radius: 6px;
            background: var(--panel2); color: var(--text); font-size: 13px; margin-bottom: 10px; font-family: inherit; }
  .search::placeholder { color: var(--muted); }
  .showall { color: var(--muted); font-size: 12px; margin-top: 8px; cursor: pointer; }
  .showall:hover { color: var(--accent); }
  .label { background: var(--panel); border: 1px solid var(--border); color: var(--muted);
           padding: 5px 10px; border-radius: 6px; font-size: 12px; cursor: pointer; }
  .label.live { color: #22c55e; border-color: #1f4d33; }

  .banner { border: 1px solid var(--border); background: linear-gradient(90deg, rgba(240,20,47,0.14), rgba(240,20,47,0.03));
            border-left: 4px solid var(--accent); padding: 14px 18px; border-radius: 10px; margin-bottom: 20px; }
  .banner .t { font-size: 12px; text-transform: uppercase; letter-spacing: 1.2px; color: #ff8293; font-weight: 700; }
  .banner .v { font-size: 17px; margin-top: 4px; font-weight: 600; }
  .banner .v small { color: var(--muted); font-weight: 400; }

  .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }
  .stat { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; }
  .stat .n { font-size: 26px; font-weight: 700; letter-spacing: -0.5px; }
  .stat .l { color: var(--muted); font-size: 12px; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.8px; }

  .card { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 18px 20px; margin-bottom: 20px; }
  .card h2 { font-size: 13px; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); margin: 0 0 14px; font-weight: 700; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }
  th { color: var(--muted); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; }
  tr:last-child td { border-bottom: none; }
  .muted { color: var(--muted); }
  .mono { font-family: 'SF Mono', Monaco, monospace; font-size: 12px; }

  .bar { display: flex; height: 26px; border-radius: 6px; overflow: hidden; border: 1px solid var(--border); }
  .bar div { height: 100%; display: flex; align-items: center; justify-content: center;
             font-size: 11px; font-weight: 700; color: #fff; min-width: 0; }
  .legend { display: flex; gap: 14px; margin-top: 8px; font-size: 11px; color: var(--muted); }
  .legend i { display: inline-block; width: 9px; height: 9px; border-radius: 2px; margin-right: 5px; }

  .esc { border-left: 4px solid var(--red); }
  .esc .who { font-weight: 700; }
  .pill { display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: 11px; font-weight: 700; }
  .pill.crit { background: rgba(239,68,68,.18); color: #ff6b6b; }
  .pill.high { background: rgba(245,158,11,.18); color: #fbbf24; }

  .kpi { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 14px; }
  .kpi .box { flex: 1; min-width: 130px; background: var(--panel2); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; }
  .kpi .box .n { font-size: 22px; font-weight: 700; }
  .kpi .box .l { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.7px; margin-top: 2px; }
  .kpi .box .n.good { color: var(--green); }
  .kpi .box .n.warn { color: var(--orange); }
  footer { color: var(--muted); font-size: 12px; margin-top: 8px; }
  footer a { color: var(--accent); text-decoration: none; }
  .empty { color: var(--muted); font-style: italic; padding: 8px 0; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Outage Hotline <span class="dot">●</span></h1>
    <div class="sub">Incident dashboard — Telnyx Edge Compute · Stateful Actors · Durable KV · SQLDB · Decision Model</div>
  </header>

  <div class="chiprow">
    <div id="chips" class="chiprow" style="margin:0; gap:8px;"></div>
    <span class="spacer"></span>
    <span class="meta" id="updated">—</span>
    <button class="label" id="refreshBtn">↻ refresh</button>
    <button class="label live" id="liveBtn">● live 4s</button>
  </div>

  <div class="banner" id="banner">loading…</div>

  <div class="grid">
    <div class="stat"><div class="n" id="st-total">–</div><div class="l">reports</div></div>
    <div class="stat"><div class="n" id="st-hour">–</div><div class="l">last hour</div></div>
    <div class="stat"><div class="n" id="st-esc">–</div><div class="l">escalations</div></div>
    <div class="stat"><div class="n" id="st-dup">–</div><div class="l">dupes flagged</div></div>
  </div>

  <div class="card">
    <h2>Region-wise classification</h2>
    <input class="search" id="regionSearch" placeholder="Find a region… (e.g. 415)">
    <table id="regionTable"><thead></thead><tbody></tbody></table>
    <div class="showall" id="showAllRegions" style="display:none"></div>
  </div>

  <div class="card">
    <h2>Severity breakdown</h2>
    <div class="bar" id="sevbar"></div>
    <div class="legend" id="sevlegend"></div>
  </div>

  <div class="card">
    <h2>Distinct known issues (deduplicated — not a raw log)</h2>
    <table id="issues"><thead><tr><th>Issue</th><th>Reports</th><th>First seen</th><th>Last seen</th></tr></thead><tbody></tbody></table>
  </div>

  <div class="card">
    <h2>Needs human review</h2>
    <div id="escList"></div>
  </div>

  <div class="card" id="evalCard" style="display:none">
    <h2>Model report card — measured against ground truth (not assumed)</h2>
    <div class="kpi" id="evalKpis"></div>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:18px;">
      <div>
        <h2 style="margin-top:0">Issue-type confusion</h2>
        <table id="confTable"><thead><tr><th>Expected</th><th>Model said</th><th>Count</th></tr></thead><tbody></tbody></table>
      </div>
      <div>
        <h2 style="margin-top:0">Duplicate threshold sweep &amp; confidence calibration</h2>
        <table id="dupTable"><thead><tr><th>Dup threshold</th><th>Accuracy</th><th>n</th></tr></thead><tbody></tbody></table>
        <table id="confBinTable" style="margin-top:12px"><thead><tr><th>Confidence bin</th><th>Correct</th><th>n</th></tr></thead><tbody></tbody></table>
      </div>
    </div>
  </div>

  <footer>Built on <a href="https://telnyx.com" target="_blank" rel="noopener">Telnyx</a> AI Communications Infrastructure — region-keyed Stateful Actors, one decision-model call per report.</footer>
</div>

<script>
const REGIONS = ${JSON.stringify(DEMO_REGIONS)};
const BUCKET_LABELS = ${JSON.stringify(BUCKET_LABELS)};
const BUCKET_COLORS = ${JSON.stringify(BUCKET_COLORS)};
const ISSUE_LABELS = ${JSON.stringify(ISSUE_LABELS)};
// Landing page = ALL regions aggregated; clicking a chip drills into one
// region. 'all' is the focused default so the first paint is the big picture.
let focused = 'all';
let live = true;
// Regions the fan-out discovered (registered in HotlineIndex + demo defaults).
let knownRegions = REGIONS.slice();
// The active taxonomy (HotlineConfig actor) — labels, rubric, and the
// region-table's classification columns all derive from this. Falls back to
// the build-time defaults until the first fetch lands.
let cfg = null;
// Region navigation state: the region-wise TABLE is the scalable surface
// (ranked, capped, searchable); chips are reserved for hot regions only.
let searchQ = '';
let showAllRegions = false;
let hotChips = [];
let lastSumm = null, lastEvals = null;
const MAX_CHIP_REGIONS = 5;
const MAX_TABLE_ROWS = 10;

function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function timeAgo(iso){ if(!iso) return '—'; const s = Math.max(0, (Date.now() - new Date(iso).getTime())/1000);
  if (s < 90) return Math.round(s)+'s ago';
  if (s < 3600) return Math.round(s/60)+'m ago';
  if (s < 86400) return (s/3600).toFixed(1).replace(/\.0$/,'')+'h ago';
  return (s/86400).toFixed(1).replace(/\.0$/,'')+'d ago'; }
function clock(ms){ return new Date(ms).toLocaleTimeString([], {hour12:false}); }

function renderChips(){
  // Chips are deliberately EXCLUSIVE: only regions with live activity
  // (reports in the last hour) or open escalations earn a chip, capped at 5.
  // Everything else is reachable through the ranked, searchable table —
  // a national hotline would otherwise grow an unusable chip row.
  const chips = ['all'];
  for (const r of hotChips) if (!chips.includes(r)) chips.push(r);
  if (focused !== 'all' && !chips.includes(focused)) chips.push(focused);
  document.getElementById('chips').innerHTML = chips.map(r =>
    '<button class="chip' + (r===focused?' on':'') + '" data-r="' + r + '">' +
    (r==='all' ? 'All regions' : 'Region ' + r) + '</button>').join('');
  document.querySelectorAll('.chip').forEach(b => b.addEventListener('click', () => {
    focused = b.dataset.r; renderChips(); tick();
  }));
}

async function tick(){
  try {
    const regions = knownRegions.join(',');
    const [sumRes, cfgRes] = await Promise.all([
      fetch('/api/summary?regions=' + regions),
      fetch('/api/config'),
    ]);
    const summ = await sumRes.json();
    // The model report card is per-region (labeled rows live in that region's
    // actor), so it's only fetched when a specific region is focused.
    let evals = null;
    if (focused !== 'all') {
      try { evals = await (await fetch('/api/eval?region=' + encodeURIComponent(focused))).json(); } catch (e) {}
    }
    try { const c = await cfgRes.json(); if (c && c.config) cfg = c.config; } catch (e) {}
    render(summ, evals);
    document.getElementById('updated').textContent = 'updated ' + new Date().toLocaleTimeString([], {hour12:false});
  } catch (e) {
    document.getElementById('updated').textContent = 'refresh failed';
  }
}

// Taxonomy helpers — everything derives from the fetched config when present.
function labelFor(key){
  const t = (cfg && cfg.issue_types || []).find(t => t.key === key);
  return t ? t.label : (ISSUE_LABELS[key] || key);
}
function bucketLabel(i){
  const rubric = (cfg && cfg.severity_rubric) || BUCKET_LABELS;
  return rubric[i] !== undefined ? rubric[i] : ('bucket-' + i);
}
function bucketColor(i){
  // stable palette; falls back to a muted tone for rubrics longer than it
  return BUCKET_COLORS[i] || '#8a94ad';
}

function render(summ, evals){
  lastSumm = summ; lastEvals = evals;
  // Dynamic region discovery (registered in HotlineIndex — no redeploy needed).
  const fetched = (summ.regions || []).map(r => r.region).filter(r => r && r.length <= 8);
  const next = [...new Set([...REGIONS, ...fetched])];
  knownRegions = next;
  if (focused !== 'all' && !knownRegions.includes(focused)) focused = 'all';

  // The focused view: 'all' aggregates every region's summary client-side
  // (per-actor SQL is private — the fan-out already brought each region's
  // numbers here); a specific region shows just its own data.
  const allMode = focused === 'all';
  const withData = (summ.regions || []).filter(r => r.summary);

  // Hot chips: rank by last-hour activity, then total; keep only regions
  // with something happening right now (or open escalations).
  hotChips = withData
    .filter(r => (r.summary.last_hour_count || 0) > 0 || (r.summary.escalations || []).length > 0)
    .sort((a,b) => ((b.summary.last_hour_count||0) - (a.summary.last_hour_count||0)) || ((b.summary.report_count||0) - (a.summary.report_count||0)))
    .slice(0, MAX_CHIP_REGIONS)
    .map(r => r.region);
  renderChips();
  let s;
  if (allMode) {
    const agg = { report_count: 0, last_hour_count: 0, escalations: [], distinct_issues: [], severity_breakdown: [], recent_reports: [], active_issue: null };
    const byType = {}; const byBucket = {};
    const escRows = []; const recent = [];
    for (const r of withData) {
      const x = r.summary;
      agg.report_count += x.report_count || 0;
      agg.last_hour_count += x.last_hour_count || 0;
      for (const d of (x.distinct_issues || [])) {
        const k = d.issue_type;
        if (!byType[k]) byType[k] = { issue_type: k, count: 0, first_seen: d.first_seen, last_seen: d.last_seen };
        byType[k].count += d.count;
        if (d.first_seen < byType[k].first_seen) byType[k].first_seen = d.first_seen;
        if (d.last_seen > byType[k].last_seen) byType[k].last_seen = d.last_seen;
      }
      for (const b of (x.severity_breakdown || [])) byBucket[b.severity_bucket] = (byBucket[b.severity_bucket] || 0) + b.count;
      escRows.push(...(x.escalations || []));
      recent.push(...(x.recent_reports || []));
    }
    agg.distinct_issues = Object.values(byType).sort((a,b)=>b.count-a.count);
    agg.severity_breakdown = Object.entries(byBucket).map(([k,v])=>({severity_bucket:+k, count:v})).sort((a,b)=>a.severity_bucket-b.severity_bucket);
    agg.escalations = escRows.sort((a,b)=>String(b.received_at).localeCompare(String(a.received_at))).slice(0,20);
    agg.recent_reports = recent.sort((a,b)=>String(b.received_at).localeCompare(String(a.received_at))).slice(0,20);
    s = agg;
  } else {
    s = (withData.find(r => r.region === focused) || {}).summary || {};
  }
  const dupesFlagged = (s.recent_reports || []).filter(r => r.is_duplicate_flag === 1).length;

  // Region-wise classification: one row per region, one column per category.
  // Columns derive from the ACTIVE config taxonomy; categories that appear in
  // history but are no longer active show up as "(retired)" — nothing is
  // hidden when the taxonomy evolves.
  const activeKeys = (cfg && cfg.issue_types ? cfg.issue_types.map(t => t.key) : Object.keys(ISSUE_LABELS));
  const colKeys = activeKeys.slice();
  const retired = new Set();
  for (const x of (summ.regions || [])) {
    for (const d of ((x.summary || {}).distinct_issues || [])) {
      if (!activeKeys.includes(d.issue_type)) retired.add(d.issue_type);
    }
  }
  for (const k of retired) colKeys.push(k);
  const colHead = '<tr><th>Region</th><th>Reports</th><th>Last hr</th>'
    + colKeys.map(k => '<th>' + esc(labelFor(k)) + (retired.has(k) ? ' <span class="muted">(retired)</span>' : '') + '</th>').join('')
    + '<th>Escalations</th></tr>';
  document.querySelector('#regionTable thead').innerHTML = colHead;

  const regionRows = (summ.regions || []).filter(r => r.summary).map(r => {
    const byType = {};
    for (const d of (r.summary.distinct_issues || [])) byType[d.issue_type] = (byType[d.issue_type] || 0) + d.count;
    return { region: r.region, s: r.summary, byType };
  });
  // The table is the primary region navigation: rank by live activity,
  // hide empty regions (unless explicitly searched), cap at 10 with a
  // show-all toggle — this is what keeps a many-region hotline usable.
  let rows = regionRows.filter(x => (x.s.report_count || 0) > 0 || searchQ);
  rows.sort((a,b) => ((b.s.last_hour_count||0) - (a.s.last_hour_count||0)) || ((b.s.report_count||0) - (a.s.report_count||0)));
  const totalMatching = rows.length;
  if (!showAllRegions && !searchQ) rows = rows.slice(0, MAX_TABLE_ROWS);
  const toggleEl = document.getElementById('showAllRegions');
  if (totalMatching > MAX_TABLE_ROWS && !searchQ) {
    toggleEl.style.display = 'block';
    toggleEl.textContent = showAllRegions
      ? '← show top ' + MAX_TABLE_ROWS + ' regions'
      : 'show all ' + totalMatching + ' regions';
  } else {
    toggleEl.style.display = 'none';
  }
  document.querySelector('#regionTable tbody').innerHTML = rows.length === 0
    ? '<tr><td colspan="' + (3 + colKeys.length + 1) + '" class="empty">' + (searchQ ? 'No region matches "' + esc(searchQ) + '".' : 'No reports yet.') + '</td></tr>'
    : rows.map(x =>
      '<tr' + (x.region === focused ? ' style="background:rgba(240,20,47,0.06)"' : '') + ' data-r="' + x.region + '" style="cursor:pointer">' +
      '<td><b>' + esc(x.region) + '</b></td>' +
      '<td>' + (x.s.report_count ?? 0) + '</td>' +
      '<td>' + (x.s.last_hour_count ?? 0) + '</td>' +
      colKeys.map(k => '<td>' + (x.byType[k] || 0) + '</td>').join('') +
      '<td>' + (x.s.escalations || []).length + '</td></tr>').join('');
  document.querySelectorAll('#regionTable tbody tr').forEach(tr =>
    tr.addEventListener('click', () => { focused = tr.dataset.r; renderChips(); tick(); }));

  // Active-issue banner: per-region KV slot when drilled in; a compact
  // "who has a known issue" line on the all-regions landing page.
  const banner = document.getElementById('banner');
  if (allMode) {
    const actives = withData
      .filter(r => r.summary.active_issue && r.summary.active_issue.issue_type)
      .map(r => r.region + ': ' + labelFor(r.summary.active_issue.issue_type));
    banner.innerHTML = '<div class="t">All regions · live picture</div>' +
      '<div class="v">' + (actives.length ? esc(actives.join(' · ')) : '<span class="muted">No known active issues anywhere yet</span>') +
      " <small>— each region's KV known-issue slot</small></div>";
  } else {
    const ai = s.active_issue;
    if (ai && ai.issue_type) {
      banner.innerHTML = '<div class="t">Known active issue · region ' + esc(focused) + '</div>' +
        '<div class="v">' + esc(labelFor(ai.issue_type)) +
        ' <small>— first seen ' + clock(ai.first_seen) + ' · last report ' + clock(ai.last_seen) +
        ' · this KV blob is the decision model\\'s dedupe context</small></div>';
    } else {
      banner.innerHTML = '<div class="t">Region ' + esc(focused) + '</div>' +
        '<div class="v" style="color:var(--muted)">No known active issue <small>— new reports will be judged as genuinely new</small></div>';
    }
  }

  document.getElementById('st-total').textContent = s.report_count ?? '–';
  document.getElementById('st-hour').textContent = s.last_hour_count ?? '–';
  document.getElementById('st-esc').textContent = (s.escalations || []).length;
  document.getElementById('st-dup').textContent = dupesFlagged;

  // Severity bar (GROUP BY severity_bucket)
  const sb = s.severity_breakdown || [];
  const totalSev = sb.reduce((a,b)=>a+b.count, 0);
  const bar = document.getElementById('sevbar');
  bar.innerHTML = totalSev === 0 ? '<div style="width:100%;color:var(--muted);font-size:11px">no classified reports yet</div>' :
    sb.map(b => {
      const pct = (100*b.count/totalSev);
      return '<div style="width:'+pct+'%;background:'+bucketColor(b.severity_bucket)+';min-width:26px" title="'+bucketLabel(b.severity_bucket)+': '+b.count+'">'+bucketLabel(b.severity_bucket)+' '+b.count+'</div>';
    }).join('');
  const rubricLen = (cfg && cfg.severity_rubric ? cfg.severity_rubric.length : BUCKET_LABELS.length);
  document.getElementById('sevlegend').innerHTML = Array.from({length: rubricLen}, (_,i) =>
    '<span><i style="background:'+bucketColor(i)+'"></i>'+bucketLabel(i)+'</span>').join('');

  // Distinct issues (SQL GROUP BY — the deduplicated picture)
  const tb = document.querySelector('#issues tbody');
  tb.innerHTML = (s.distinct_issues || []).length === 0
    ? '<tr><td colspan="4" class="empty">No classified reports yet.</td></tr>'
    : (s.distinct_issues || []).map(d =>
      '<tr><td><b>' + esc(labelFor(d.issue_type)) + '</b></td>' +
      '<td>' + d.count + '</td><td class="muted">' + timeAgo(d.first_seen) + '</td><td class="muted">' + timeAgo(d.last_seen) + '</td></tr>').join('');

  // Escalations
  const escBox = document.getElementById('escList');
  escBox.innerHTML = (s.escalations || []).length === 0
    ? '<div class="empty">Nothing needs human review right now.</div>'
    : (s.escalations || []).map(e =>
      '<div class="esc" style="border:1px solid var(--border);border-left:4px solid var(--red);border-radius:8px;padding:10px 14px;margin-bottom:10px">' +
      '<div class="who">' + esc(e.reporter || 'caller') + ' <span class="pill ' + (e.severity_bucket>=((cfg && cfg.escalation && cfg.escalation.min_severity_bucket) || 2)?'crit':'high') + '">' +
      (bucketLabel(e.severity_bucket) || '?') + '</span> <span class="muted mono">report #' + e.id + '</span></div>' +
      '<div style="margin-top:4px">' + esc(e.raw_report) + '</div></div>').join('');

  // Model report card — per-region (labeled rows live in that region's actor);
  // hidden entirely on the all-regions landing page.
  const evalCardEl = document.getElementById('evalCard');
  if (evalCardEl) evalCardEl.style.display = allMode ? 'none' : 'block';
  const ev = (evals && evals.eval) || null;
  const kpis = document.getElementById('evalKpis');
  if (allMode) {
    kpis.innerHTML = '<div class="empty">Select a region above to see its model report card — labeled reports live in each region actor.</div>';
    document.querySelector('#confTable tbody').innerHTML = '';
    document.querySelector('#dupTable tbody').innerHTML = '';
    document.querySelector('#confBinTable tbody').innerHTML = '';
    return;
  }
  const itAcc = ev.labeled_issue_type ? (100*ev.issue_type_correct/ev.labeled_issue_type).toFixed(0)+'%' : '–';
  const svAcc = ev.labeled_severity ? (100*ev.severity_exact/ev.labeled_severity).toFixed(0)+'%' : '–';
  kpis.innerHTML =
    '<div class="box"><div class="n ' + (parseFloat(itAcc)>=90?'good':'warn') + '">' + itAcc + '</div><div class="l">issue-type accuracy</div></div>' +
    '<div class="box"><div class="n">' + (ev.labeled_severity ? ev.severity_mae.toFixed(2) : '–') + '</div><div class="l">severity MAE (0-3)</div></div>' +
    '<div class="box"><div class="n">' + (ev.labeled_duplicate ? (100*ev.duplicate_accuracy.find(d=>d.threshold===0.35).correct/ev.labeled_duplicate).toFixed(0)+'%' : '–') + '</div><div class="l">dup accuracy @ 0.35</div></div>' +
    '<div class="box"><div class="n muted" style="font-size:15px;padding-top:6px">' + ev.labeled_issue_type + ' labeled</div><div class="l">ground-truth rows</div></div>';

  document.querySelector('#confTable tbody').innerHTML =
    (ev.issue_type_confusion || []).length === 0 ? '<tr><td colspan="3" class="empty">—</td></tr>' :
    ev.issue_type_confusion.map(c =>
      '<tr><td>' + esc(labelFor(c.expected)) + '</td>' +
      '<td>' + esc(labelFor(c.actual)) + (c.expected===c.actual?' <span class="muted">✓</span>':' <span style="color:var(--red)">✗</span>') + '</td>' +
      '<td>' + c.count + '</td></tr>').join('');

  document.querySelector('#dupTable tbody').innerHTML =
    ev.duplicate_accuracy.map(d =>
      '<tr><td class="mono">' + d.threshold.toFixed(2) + '</td><td>' + (ev.labeled_duplicate ? (100*d.correct/ev.labeled_duplicate).toFixed(0)+'%' : '–') + '</td><td>' + ev.labeled_duplicate + '</td></tr>').join('');

  document.querySelector('#confBinTable tbody').innerHTML =
    ev.confidence_bins.map(b =>
      '<tr><td class="mono">' + esc(b.range) + '</td><td>' + (b.total ? (100*b.correct/b.total).toFixed(0)+'%' : '—') + '</td><td>' + b.total + '</td></tr>').join('');
}

document.getElementById('refreshBtn').addEventListener('click', tick);
document.getElementById('liveBtn').addEventListener('click', (e) => {
  live = !live;
  e.target.classList.toggle('live', live);
  e.target.textContent = live ? '● live 4s' : '○ paused';
});
// Region search + show-all toggle re-render the cached summary without
// refetching (the next live tick refreshes the data anyway).
document.getElementById('regionSearch').addEventListener('input', (e) => {
  searchQ = e.target.value.trim();
  showAllRegions = false;
  if (lastSumm) render(lastSumm, lastEvals);
});
document.getElementById('showAllRegions').addEventListener('click', () => {
  showAllRegions = !showAllRegions;
  if (lastSumm) render(lastSumm, lastEvals);
});
setInterval(() => { if (live) tick(); }, 4000);
renderChips();
tick();
</script>
</body>
</html>`;
