/* === Project Slug === */
const PATH_PARTS = window.location.pathname.split('/');
const PROJECT_SLUG = PATH_PARTS[1] === 'project' ? PATH_PARTS[2] : null;
const QS = PROJECT_SLUG ? '?project=' + PROJECT_SLUG : '';

/* === State === */
let state = null;
let allTasks = null;
let firstLoad = true;

/* === Tabs === */
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
    if (tab.dataset.tab === 'activity') loadActivity();
    if (tab.dataset.tab === 'meetings') loadMeetings();
    if (tab.dataset.tab === 'docs') loadDocs();
  });
});

/* === Clock === */
function updateClock() {
  document.getElementById('clock').textContent = new Date().toLocaleTimeString('en-US', { hour12: false });
}
setInterval(updateClock, 1000);
updateClock();

/* === Time Helpers === */
function formatElapsed(isoStr) {
  if (!isoStr) return '—';
  const diff = Math.max(0, Math.floor((Date.now() - new Date(isoStr).getTime()) / 1000));
  const h = Math.floor(diff / 3600), m = Math.floor((diff % 3600) / 60);
  if (h > 0) return h + 'h ' + m + 'm';
  if (m > 0) return m + 'm';
  return '<1m';
}

function formatDuration(dur) {
  if (!dur) return '—';
  if (typeof dur === 'number') {
    const h = Math.floor(dur / 3600), m = Math.floor((dur % 3600) / 60);
    if (h > 0) return h + 'h ' + m + 'm';
    if (m > 0) return m + 'm';
    return '<1m';
  }
  return String(dur);
}

function formatTimestamp(iso) {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false });
  } catch { return iso; }
}

function updateElapsed() {
  if (!state || !state.agents) return;
  Object.entries(state.agents).forEach(([key, agent]) => {
    const el = document.getElementById('elapsed-' + key);
    if (el) {
      const isActive = agent.status && agent.status !== 'idle';
      el.textContent = isActive ? formatElapsed(agent.startedAt) : '—';
    }
  });
}
setInterval(updateElapsed, 1000);

/* === Fetch === */
async function fetchJSON(url) {
  try { const r = await fetch(url); if (!r.ok) return null; return await r.json(); }
  catch { return null; }
}

/* === Loading Skeleton === */
function showSkeleton() {
  const sk = document.getElementById('loadingSkeleton');
  if (sk) sk.classList.add('visible');
}
function hideSkeleton() {
  const sk = document.getElementById('loadingSkeleton');
  if (sk) sk.classList.remove('visible');
}

/* === Render State === */
async function loadState() {
  if (firstLoad) showSkeleton();
  const data = await fetchJSON('/api/state' + QS);
  if (!data) return;
  state = data;
  const p = data.project || {};

  document.getElementById('projectName').textContent = p.name || '—';
  document.getElementById('sprintBadge').textContent = 'Sprint ' + (p.sprint || '—');
  document.getElementById('phaseBadge').textContent = p.phase || '—';
  document.getElementById('progressText').textContent = Math.round((p.progress || 0) * 100) + '%';
  document.getElementById('progressCircle').style.strokeDashoffset = 100 - (p.progress || 0) * 100;

  renderAgents(data.agents || {});
  renderMetrics(data.metrics || {});
  renderBurndown(data.metrics || {});
  updateElapsed();
  if (firstLoad) { hideSkeleton(); firstLoad = false; }
}

function renderAgents(agents) {
  const row = document.getElementById('agentsRow');
  row.innerHTML = '';
  Object.entries(agents).forEach(([key, a]) => {
    const isActive = a.status === 'active' || a.status === 'working';
    const statusClass = isActive ? 'active' : a.status === 'blocked' ? 'blocked' : 'idle';
    const card = document.createElement('div');
    card.className = 'agent-card glass-card' + (isActive ? ' agent-active' : '');
    card.innerHTML = `
      <div class="agent-top">
        <span class="agent-emoji">${a.emoji || '🤖'}</span>
        <span class="agent-name">${a.name || key}</span>
      </div>
      <div class="agent-role">${a.role || '—'}</div>
      <div class="agent-status"><span class="status-dot ${statusClass}"></span><span>${a.status || 'idle'}</span></div>
      <div class="agent-task" title="${a.task || ''}">${a.task || '—'}</div>
      <div class="agent-time" id="elapsed-${key}">${statusClass !== 'idle' ? formatElapsed(a.startedAt) : '—'}</div>
    `;
    row.appendChild(card);
  });
}

/* === Tasks / Kanban === */
const EMPTY_MESSAGES = {
  backlog: 'No tasks in backlog',
  in_dev: 'No tasks in development',
  in_qa: 'No tasks in QA',
  done: 'No completed tasks yet'
};

async function loadTasks() {
  const data = await fetchJSON('/api/tasks' + QS);
  if (!data) return;
  allTasks = data;
  ['backlog', 'in_dev', 'in_qa', 'done'].forEach(col => {
    const items = data[col] || [];
    document.getElementById('count-' + col).textContent = items.length;
    const container = document.getElementById('col-' + col);
    container.innerHTML = '';
    if (items.length === 0) {
      container.innerHTML = `<div class="kanban-empty">${EMPTY_MESSAGES[col]}</div>`;
      return;
    }
    items.forEach(t => {
      const priority = t.priority === 'high' ? '🔴' : t.priority === 'medium' ? '🟡' : t.priority === 'low' ? '🟢' : '⚪';
      const card = document.createElement('div');
      card.className = 'kanban-card';
      card.innerHTML = `
        <div class="card-id">${t.id || ''}</div>
        <div class="card-title">${t.title || '—'}</div>
        <div class="card-meta"><span>${t.assignee || ''}</span><span class="card-priority">${priority}</span></div>
      `;
      card.addEventListener('click', () => openTaskModal(t, col));
      container.appendChild(card);
    });
  });
  renderLeaderboard(data);
  renderTimeline(data);
  renderVelocity(data);
}

/* === Task Modal === */
const AGENT_MAP = {
  architect: { emoji: '🏗️', name: 'Alex' },
  frontend: { emoji: '🎨', name: 'Frankie' },
  backend: { emoji: '⚙️', name: 'Blake' },
  qa: { emoji: '🔍', name: 'Quinn' },
  bugfix: { emoji: '🐛', name: 'Bug Fixer' },
};

function openTaskModal(task, column) {
  const overlay = document.getElementById('taskModal');
  const body = document.getElementById('modalBody');
  const agentKey = task.agent || task.assignee || '';
  const agentInfo = AGENT_MAP[agentKey.toLowerCase()] || { emoji: '🤖', name: agentKey || 'Unassigned' };
  const prioClass = task.priority === 'high' ? 'priority-high' : task.priority === 'medium' ? 'priority-medium' : 'priority-low';
  const statusLabel = { backlog: 'Backlog', in_dev: 'In Development', in_qa: 'In QA', done: 'Done' }[column] || column;

  body.innerHTML = `
    <div class="modal-id">${task.id || ''}</div>
    <div class="modal-title">${task.title || '—'}</div>
    ${task.description ? `<div class="modal-desc">${task.description}</div>` : ''}
    <div class="modal-row"><span class="modal-label">Assignee</span><span class="modal-val">${agentInfo.emoji} ${agentInfo.name}</span></div>
    <div class="modal-row"><span class="modal-label">Priority</span><span class="priority-badge ${prioClass}">${(task.priority || 'normal').toUpperCase()}</span></div>
    <div class="modal-row"><span class="modal-label">Status</span><span class="status-indicator status-${column}"><span class="dot"></span>${statusLabel}</span></div>
    <div class="modal-row"><span class="modal-label">Started</span><span class="modal-val">${formatTimestamp(task.startedAt)}</span></div>
    <div class="modal-row"><span class="modal-label">Completed</span><span class="modal-val">${formatTimestamp(task.completedAt)}</span></div>
    <div class="modal-row"><span class="modal-label">Duration</span><span class="modal-val">${formatDuration(task.duration)}</span></div>
    <div class="modal-row"><span class="modal-label">Files Created</span><span class="modal-val">${task.filesCreated != null ? task.filesCreated : '—'}</span></div>
  `;
  overlay.classList.add('open');
}

document.getElementById('modalClose').addEventListener('click', () => {
  document.getElementById('taskModal').classList.remove('open');
});
document.getElementById('taskModal').addEventListener('click', (e) => {
  if (e.target === e.currentTarget) e.currentTarget.classList.remove('open');
});

/* === Metrics === */
function renderMetrics(m) {
  const defs = [
    { label: 'TASKS DONE', value: (m.tasks_completed || 0) + '/' + (m.tasks_total || 0), pct: m.tasks_total ? m.tasks_completed / m.tasks_total : 0, color: 'var(--primary)' },
    { label: 'BUGS FIXED', value: (m.bugs_fixed || 0) + '/' + (m.bugs_found || 0), pct: m.bugs_found ? m.bugs_fixed / m.bugs_found : 0, color: 'var(--success)' },
    { label: 'TESTS', value: (m.tests_passing || 0) + ' passing', pct: (m.tests_passing + m.tests_failing) ? m.tests_passing / (m.tests_passing + m.tests_failing) : 0, color: 'var(--warning)' },
    { label: 'LINES OF CODE', value: (m.lines_of_code || 0).toLocaleString(), pct: Math.min(1, (m.lines_of_code || 0) / 5000), color: 'var(--danger)' },
  ];
  const row = document.getElementById('metricsRow');
  row.innerHTML = '';
  defs.forEach(d => {
    const card = document.createElement('div');
    card.className = 'metric-card glass-card';
    card.innerHTML = `
      <div class="metric-label">${d.label}</div>
      <div class="metric-value">${d.value}</div>
      <div class="metric-bar"><div class="metric-bar-fill" style="width:${Math.round(d.pct * 100)}%;background:${d.color}"></div></div>
    `;
    row.appendChild(card);
  });
}

/* === Burndown (compact) === */
function renderBurndown(m) {
  const total = m.tasks_total || 10;
  const done = m.tasks_completed || 0;
  const svg = document.getElementById('burndownChart');
  const w = 400, h = 140, pad = 30;
  const days = 10;
  const remaining = total - done;
  const points = [];
  for (let i = 0; i <= days; i++) {
    if (i <= Math.floor(days * (done / total))) {
      points.push(total - (done * i / Math.floor(days * (done / total) || 1)));
    } else {
      points.push(remaining);
    }
  }
  const xS = (i) => pad + (i / days) * (w - pad * 2);
  const yS = (v) => pad + ((total - v) / total) * (h - pad * 2);
  const pathD = points.map((v, i) => `${i === 0 ? 'M' : 'L'}${xS(i)},${yS(v)}`).join(' ');
  const areaD = pathD + ` L${xS(days)},${yS(0)} L${xS(0)},${yS(0)} Z`;
  const idealD = `M${xS(0)},${yS(total)} L${xS(days)},${yS(0)}`;
  let grid = '', labels = '';
  for (let i = 0; i <= 3; i++) {
    const y = pad + (i / 3) * (h - pad * 2);
    grid += `<line x1="${pad}" y1="${y}" x2="${w - pad}" y2="${y}" class="burndown-grid"/>`;
  }
  for (let i = 0; i <= days; i += 2) {
    labels += `<text x="${xS(i)}" y="${h - 5}" text-anchor="middle" class="burndown-label">D${i}</text>`;
  }
  svg.innerHTML = `
    <defs><linearGradient id="burnGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="var(--primary)"/><stop offset="100%" stop-color="transparent"/>
    </linearGradient></defs>
    ${grid}<path d="${idealD}" class="burndown-ideal"/>
    <path d="${areaD}" class="burndown-area"/><path d="${pathD}" class="burndown-line"/>${labels}
  `;
}

/* === Agent Leaderboard === */
function renderLeaderboard(data) {
  const counts = {};
  (data.done || []).forEach(t => {
    const a = t.agent || t.assignee || 'unknown';
    counts[a] = (counts[a] || 0) + 1;
  });
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const max = sorted.length ? sorted[0][1] : 1;
  const el = document.getElementById('agentLeaderboard');
  if (!sorted.length) { el.innerHTML = '<div class="kanban-empty">No completed tasks yet</div>'; return; }
  const colors = ['var(--primary)', 'var(--success)', 'var(--warning)', 'var(--danger)', '#a855f7'];
  el.innerHTML = sorted.map(([key, count], i) => {
    const info = AGENT_MAP[key.toLowerCase()] || { emoji: '🤖', name: key };
    const pct = Math.round((count / max) * 100);
    return `<div class="lb-row">
      <span class="lb-emoji">${info.emoji}</span>
      <span class="lb-name">${info.name}</span>
      <div class="lb-bar-wrap"><div class="lb-bar" style="width:${pct}%;background:${colors[i % colors.length]}"></div></div>
      <span class="lb-count">${count}</span>
    </div>`;
  }).join('');
}

/* === Completion Timeline === */
function renderTimeline(data) {
  const el = document.getElementById('completionTimeline');
  const done = (data.done || []).filter(t => t.completedAt);
  if (!done.length) { el.innerHTML = '<div class="timeline-empty">No completion data yet</div>'; return; }
  const times = done.map(t => new Date(t.completedAt).getTime());
  const minT = Math.min(...times), maxT = Math.max(...times);
  const range = maxT - minT || 1;
  el.innerHTML = `<div class="timeline-track"><div class="timeline-line"></div>${done.map(t => {
    const ts = new Date(t.completedAt).getTime();
    const pct = 5 + ((ts - minT) / range) * 90;
    const label = new Date(t.completedAt).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
    return `<div class="timeline-dot" style="left:${pct}%" title="${t.title || t.id}"><span class="timeline-dot-label">${label}</span></div>`;
  }).join('')}</div>`;
}

/* === Sprint Velocity === */
function renderVelocity(data) {
  const el = document.getElementById('sprintVelocity');
  const done = (data.done || []).filter(t => t.duration);
  if (!done.length) {
    el.innerHTML = `
      <div class="velocity-stat"><span class="velocity-label">Tasks Completed</span><span class="velocity-value primary">${(data.done || []).length}</span></div>
      <div class="velocity-stat"><span class="velocity-label">Avg Time/Task</span><span class="velocity-value">—</span></div>
      <div class="velocity-stat"><span class="velocity-label">Fastest Task</span><span class="velocity-value">—</span></div>
      <div class="velocity-stat"><span class="velocity-label">Slowest Task</span><span class="velocity-value">—</span></div>
    `;
    return;
  }
  const durations = done.map(t => typeof t.duration === 'number' ? t.duration : 0).filter(d => d > 0);
  const avg = durations.length ? durations.reduce((a, b) => a + b, 0) / durations.length : 0;
  const fastest = durations.length ? Math.min(...durations) : 0;
  const slowest = durations.length ? Math.max(...durations) : 0;
  el.innerHTML = `
    <div class="velocity-stat"><span class="velocity-label">Tasks Completed</span><span class="velocity-value primary">${(data.done || []).length}</span></div>
    <div class="velocity-stat"><span class="velocity-label">Avg Time/Task</span><span class="velocity-value warning">${formatDuration(Math.round(avg))}</span></div>
    <div class="velocity-stat"><span class="velocity-label">Fastest Task</span><span class="velocity-value success">${formatDuration(fastest)}</span></div>
    <div class="velocity-stat"><span class="velocity-label">Slowest Task</span><span class="velocity-value danger">${formatDuration(slowest)}</span></div>
  `;
}

/* === Activity === */
async function loadActivity() {
  const data = await fetchJSON('/api/log' + QS);
  if (!data) return;
  const container = document.getElementById('activityFull');
  container.innerHTML = '';
  (Array.isArray(data) ? data : []).reverse().forEach(e => {
    const div = document.createElement('div');
    div.className = 'activity-entry';
    const ts = e.timestamp ? new Date(e.timestamp).toLocaleTimeString('en-US', { hour12: false }) : '—';
    div.innerHTML = `<span class="activity-ts">${ts}</span><span class="activity-agent">${e.agent || 'system'}</span><span class="activity-action">${e.action || ''}</span>`;
    container.appendChild(div);
  });
}

/* === Meetings === */
async function loadMeetings() {
  const data = await fetchJSON('/api/meetings' + QS);
  if (!data || !data.meetings) return;
  const list = document.getElementById('meetingsList');
  list.innerHTML = '';
  data.meetings.forEach(m => {
    const displayName = cleanMeetingName(m.name, m.path);
    const item = document.createElement('div');
    item.className = 'split-list-item';
    item.innerHTML = `<div class="item-name">${m.type || '📝'} ${displayName}</div>
      <div class="item-meta">${m.modified ? new Date(m.modified).toLocaleDateString() : ''}</div>`;
    item.addEventListener('click', () => {
      list.querySelectorAll('.split-list-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      loadMeetingContent(m.path);
    });
    list.appendChild(item);
  });
}

function cleanMeetingName(name, path) {
  // Strip sprint prefix paths, clean up
  let clean = name || '';
  if (path) {
    const parts = path.replace(/\.md$/i, '').split('/');
    clean = parts[parts.length - 1].replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }
  return clean;
}

async function loadMeetingContent(path) {
  const data = await fetchJSON('/api/meeting/' + encodeURIComponent(path) + QS);
  if (!data) return;
  document.getElementById('meetingsContent').innerHTML = renderMarkdown(data.content || '');
}

/* === Docs === */
async function loadDocs() {
  const data = await fetchJSON('/api/docs' + QS);
  if (!data || !data.docs) return;
  const list = document.getElementById('docsList');
  list.innerHTML = '';
  data.docs.forEach(d => {
    const item = document.createElement('div');
    item.className = 'split-list-item';
    item.innerHTML = `<div class="item-name">📄 ${d.name}</div>
      <div class="item-meta">${d.modified ? new Date(d.modified).toLocaleDateString() : ''}</div>`;
    item.addEventListener('click', () => {
      list.querySelectorAll('.split-list-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      loadDocContent(d.filename);
    });
    list.appendChild(item);
  });
}

async function loadDocContent(filename) {
  const data = await fetchJSON('/api/doc/' + encodeURIComponent(filename) + QS);
  if (!data) return;
  document.getElementById('docsContent').innerHTML = renderMarkdown(data.content || '');
}

/* === Markdown Renderer === */
function renderMarkdown(md) {
  // Escape HTML
  let html = md.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  // Fenced code blocks
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    return `<pre><code class="lang-${lang}">${code.trim()}</code></pre>`;
  });

  // Tables
  html = html.replace(/^(\|.+\|)\n(\|[-| :]+\|)\n((?:\|.+\|\n?)+)/gm, (_, header, sep, body) => {
    const ths = header.split('|').filter(c => c.trim()).map(c => `<th>${c.trim()}</th>`).join('');
    const rows = body.trim().split('\n').map(row => {
      const tds = row.split('|').filter(c => c.trim()).map(c => `<td>${c.trim()}</td>`).join('');
      return `<tr>${tds}</tr>`;
    }).join('');
    return `<table><thead><tr>${ths}</tr></thead><tbody>${rows}</tbody></table>`;
  });

  // Blockquotes
  html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');
  html = html.replace(/<\/blockquote>\n<blockquote>/g, '\n');

  // Headers
  html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Horizontal rule
  html = html.replace(/^---$/gm, '<hr>');

  // Bold & italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Inline code (but not inside pre)
  html = html.replace(/`([^`\n]+)`/g, '<code>$1</code>');

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

  // Unordered lists
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
  html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');

  // Ordered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<oli>$1</oli>');
  html = html.replace(/((?:<oli>.*<\/oli>\n?)+)/g, (m) => {
    return '<ol>' + m.replace(/<\/?oli>/g, (t) => t.replace('oli', 'li')) + '</ol>';
  });

  // Paragraphs: double newlines
  html = html.replace(/\n{2,}/g, '</p><p>');
  // Single newlines to <br> (but not inside pre/table)
  html = html.replace(/\n/g, '<br>');

  // Wrap in paragraph
  html = '<p>' + html + '</p>';

  // Clean up empty paragraphs
  html = html.replace(/<p>\s*<\/p>/g, '');
  html = html.replace(/<p>(<h[1-4]>)/g, '$1');
  html = html.replace(/(<\/h[1-4]>)<\/p>/g, '$1');
  html = html.replace(/<p>(<pre>)/g, '$1');
  html = html.replace(/(<\/pre>)<\/p>/g, '$1');
  html = html.replace(/<p>(<table>)/g, '$1');
  html = html.replace(/(<\/table>)<\/p>/g, '$1');
  html = html.replace(/<p>(<ul>)/g, '$1');
  html = html.replace(/(<\/ul>)<\/p>/g, '$1');
  html = html.replace(/<p>(<ol>)/g, '$1');
  html = html.replace(/(<\/ol>)<\/p>/g, '$1');
  html = html.replace(/<p>(<blockquote>)/g, '$1');
  html = html.replace(/(<\/blockquote>)<\/p>/g, '$1');
  html = html.replace(/<p>(<hr>)/g, '$1');

  return html;
}

/* === Meeting Spy === */
let spyEventSource = null;
let spyActive = false;
let spyMeetingStarted = null;
let spyMessageCount = 0;
let spyParticipants = new Set();

function connectLiveStream() {
  if (spyEventSource) { spyEventSource.close(); spyEventSource = null; }
  spyEventSource = new EventSource('/api/meeting/stream' + QS);
  spyEventSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.event === 'done') {
        onMeetingEnded();
        return;
      }
      appendSpyMessage(data);
    } catch {}
  };
  spyEventSource.onerror = () => {
    if (spyEventSource) { spyEventSource.close(); spyEventSource = null; }
  };
}

function appendSpyMessage(data) {
  const container = document.getElementById('spyMessages');
  const empty = document.getElementById('spyEmpty');
  if (empty) empty.style.display = 'none';
  spyMessageCount++;
  spyParticipants.add(data.speaker || data.agent);

  const msg = document.createElement('div');
  msg.className = 'spy-message';
  const agentClass = 'agent-' + (data.agent || '').toLowerCase();
  let ts = '';
  try { ts = new Date(data.ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }); } catch { ts = data.ts || ''; }
  msg.innerHTML = `
    <div class="spy-avatar">${data.emoji || '🤖'}</div>
    <div class="spy-body">
      <div class="spy-header">
        <span class="spy-agent-name ${agentClass}">${data.speaker || data.agent}</span>
        <span class="spy-ts">${ts}</span>
      </div>
      <div class="spy-text">${(data.text || '').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
    </div>
  `;
  container.appendChild(msg);
  container.scrollTop = container.scrollHeight;
}

function onMeetingEnded() {
  if (spyEventSource) { spyEventSource.close(); spyEventSource = null; }
  const statusBar = document.getElementById('spyStatusBar');
  statusBar.classList.remove('is-live');
  document.getElementById('spyStatusText').textContent = 'MEETING ENDED';
  document.getElementById('liveTabDot').classList.remove('active');

  const summary = document.getElementById('spySummary');
  let duration = '—';
  if (spyMeetingStarted) {
    const secs = Math.floor((Date.now() - new Date(spyMeetingStarted).getTime()) / 1000);
    const m = Math.floor(secs / 60), s = secs % 60;
    duration = m + 'm ' + s + 's';
  }
  summary.style.display = 'block';
  summary.innerHTML = `<h3>MEETING COMPLETE</h3><div class="spy-summary-stats">
    <span>⏱ <strong>${duration}</strong></span>
    <span>💬 <strong>${spyMessageCount}</strong> messages</span>
    <span>👥 <strong>${spyParticipants.size}</strong> participants</span>
  </div>`;
  spyActive = false;
  spyMessageCount = 0;
  spyParticipants.clear();
  spyMeetingStarted = null;
}

async function pollMeetingActive() {
  const data = await fetchJSON('/api/meeting/active' + QS);
  if (!data) return;
  const dot = document.getElementById('liveTabDot');
  const statusBar = document.getElementById('spyStatusBar');
  if (data.active && !spyActive) {
    spyActive = true;
    spyMeetingStarted = data.started;
    dot.classList.add('active');
    statusBar.classList.add('is-live');
    document.getElementById('spyStatusText').textContent = '● LIVE — ' + data.lines + ' messages';
    document.getElementById('spySummary').style.display = 'none';
    // Reset messages area
    const container = document.getElementById('spyMessages');
    container.innerHTML = '';
    const empty = document.getElementById('spyEmpty');
    if (empty) container.appendChild(empty);
    spyMessageCount = 0;
    spyParticipants.clear();
    connectLiveStream();
    // Auto-switch to live tab
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    document.querySelector('[data-tab="live"]').classList.add('active');
    document.getElementById('tab-live').classList.add('active');
  } else if (data.active && spyActive) {
    document.getElementById('spyStatusText').textContent = '● LIVE — ' + data.lines + ' messages';
  } else if (!data.active) {
    dot.classList.remove('active');
    if (spyActive) onMeetingEnded();
  }
}
setInterval(pollMeetingActive, 3000);
pollMeetingActive();

/* === Sprint and Meeting Control === */
async function startSprint() {
  const goals = prompt("Enter sprint goals (comma-separated):");
  if (!goals) return;
  
  const btn = document.getElementById('startSprintBtn');
  btn.disabled = true;
  btn.textContent = "🔄 Starting...";
  
  try {
    const response = await fetch('/api/sprint/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        goals: goals.split(',').map(g => g.trim()),
        sprint_number: (state?.project?.sprint || 0) + 1
      })
    });
    
    const result = await response.json();
    
    if (response.ok) {
      alert(`Sprint ${result.sprint_number} started successfully!`);
      await poll(); // Refresh state
    } else {
      alert(`Failed to start sprint: ${result.detail || 'Unknown error'}`);
    }
  } catch (error) {
    alert('Error starting sprint. Please try again.');
    console.error('Sprint start error:', error);
  } finally {
    btn.disabled = false;
    btn.textContent = "🚀 Start Sprint";
  }
}

async function startMeeting() {
  const topic = prompt("Enter meeting topic:");
  if (!topic) return;
  
  const btn = document.getElementById('newMeetingBtn');
  btn.disabled = true;
  btn.textContent = "🔄 Starting...";
  
  try {
    const response = await fetch('/api/meeting/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        topic: topic,
        participants: ["architect", "frontend", "backend", "qa"]
      })
    });
    
    const result = await response.json();
    
    if (response.ok) {
      alert(`Meeting "${topic}" started successfully!`);
      // Auto-switch to live tab to watch
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      document.querySelector('[data-tab="live"]').classList.add('active');
      document.getElementById('tab-live').classList.add('active');
    } else {
      alert(`Failed to start meeting: ${result.detail || 'Unknown error'}`);
    }
  } catch (error) {
    alert('Error starting meeting. Please try again.');
    console.error('Meeting start error:', error);
  } finally {
    btn.disabled = false;
    btn.textContent = "📋 New Meeting";
  }
}

async function logout() {
  try {
    const response = await fetch('/auth/logout', { method: 'POST' });
    if (response.ok) {
      window.location.href = '/';
    }
  } catch (error) {
    console.error('Logout error:', error);
    // Force redirect even if request fails
    window.location.href = '/';
  }
}

/* === Authentication Check === */
async function checkAuth() {
  try {
    const response = await fetch('/api/auth/status');
    const result = await response.json();
    
    if (!result.authenticated) {
      window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
    }
  } catch (error) {
    // If auth check fails, assume not authenticated
    window.location.href = '/login';
  }
}

// Check auth on load
checkAuth();

/* === Sprint Status Monitoring === */
async function checkSprintStatus() {
  try {
    const response = await fetch('/api/sprint/status');
    const result = await response.json();
    
    const startBtn = document.getElementById('startSprintBtn');
    if (result.running) {
      startBtn.disabled = true;
      startBtn.textContent = "🔄 Sprint Running";
    } else {
      startBtn.disabled = false;
      startBtn.textContent = "🚀 Start Sprint";
    }
  } catch (error) {
    // Ignore errors in status check
  }
}

// Check sprint status periodically
setInterval(checkSprintStatus, 10000);

/* === Polling === */
async function poll() {
  await Promise.all([loadState(), loadTasks()]);
}
poll();
setInterval(poll, 5000);
