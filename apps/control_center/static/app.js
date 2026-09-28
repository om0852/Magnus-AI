// Magnas Next-Gen Autonomous Control Center Client JS
let socket = null;
let recognition = null;
let isListeningWakeWord = false;
let isTtsEnabled = true;
let isManualMicListening = false;

const WAKE_WORDS = ["hey magnas", "hey magnus", "hi magnas", "hi magnus", "magnas", "magnus", "ok magnas"];

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initCommandInput();
  initVoiceEngine();
  connectWebSocket();
  fetchStatus();
  fetchTasks();
  fetchApprovals();
  fetchTools();

  // Refresh interval
  setInterval(fetchStatus, 4000);
});

function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const tab = item.dataset.tab;
      switchTab(tab);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-view').forEach(el => el.classList.remove('active'));

  const navBtn = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
  const view = document.getElementById(`view-${tabId}`);
  if (navBtn) navBtn.classList.add('active');
  if (view) view.classList.add('active');

  if (tabId === 'history') fetchTasks();
  if (tabId === 'approvals') fetchApprovals();
  if (tabId === 'audit-logs') fetchAuditLogs();
  if (tabId === 'tools') fetchTools();
}

function initCommandInput() {
  const input = document.getElementById('cmd-input');
  const btn = document.getElementById('cmd-send-btn');

  const execute = async () => {
    const text = input.value.trim();
    if (!text) return;

    submitCommandText(text);
    input.value = '';
  };

  btn.addEventListener('click', execute);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') execute();
  });
}

async function submitCommandText(text) {
  appendStreamItem({
    raw_prompt: text,
    status: 'RECEIVED',
    intent: 'PARSING INTENT...',
    created_at: Date.now() / 1000
  });

  if (isTtsEnabled) {
    speakText(`Planning & executing task: ${text}`);
  }

  try {
    const res = await fetch('/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: text })
    });
    const data = await res.json();
    console.log('Task submitted:', data);
    fetchStatus();
    fetchTasks();
  } catch (e) {
    console.error('Task submission error:', e);
  }
}

function quickRun(promptText) {
  const input = document.getElementById('cmd-input');
  if (input) input.value = promptText;
  submitCommandText(promptText);
}

// ==========================================
// VOICE & "HEY MAGNAS" WAKE-WORD SYSTEM
// ==========================================

function initVoiceEngine() {
  const micBtn = document.getElementById('mic-btn');
  const wakeBtn = document.getElementById('wake-word-toggle-btn');
  const ttsBtn = document.getElementById('tts-toggle-btn');

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.warn('Web Speech Recognition API not supported in this browser.');
    showSpeechHint('Browser Speech API not supported. Web control fallback active.');
  } else {
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setVisualizerState(true);
      showSpeechHint('Listening for "Hey Magnas..." or speech command');
    };

    recognition.onresult = (event) => {
      const resultIndex = event.resultIndex;
      const transcript = event.results[resultIndex][0].transcript.toLowerCase().trim();
      console.log('[Voice Recognized]:', transcript);

      let wakeFound = false;
      let extractedCommand = '';

      for (const wake of WAKE_WORDS) {
        if (transcript.includes(wake)) {
          wakeFound = true;
          const idx = transcript.indexOf(wake);
          extractedCommand = transcript.substring(idx + wake.length).replace(/^[,\.\?\!\s]+/, '').trim();
          break;
        }
      }

      if (wakeFound) {
        showSpeechHint(`⚡ Wake Word Triggered! (${transcript})`);
        flashVoiceActive();

        if (extractedCommand.length > 0) {
          submitCommandText(extractedCommand);
        } else {
          speakText("Yes? How can I help you?");
          showSpeechHint('Say your command now...');
        }
      } else if (isManualMicListening) {
        showSpeechHint(`Direct Command: "${transcript}"`);
        submitCommandText(transcript);
        stopManualListening();
      }
    };

    recognition.onerror = (event) => {
      console.warn('[Speech Error]:', event.error);
      if (event.error === 'not-allowed') {
        showSpeechHint('Microphone permission denied.');
      }
    };

    recognition.onend = () => {
      setVisualizerState(false);
      if (isListeningWakeWord) {
        setTimeout(() => {
          try { recognition.start(); } catch (e) {}
        }, 500);
      }
    };
  }

  if (wakeBtn) wakeBtn.addEventListener('click', toggleWakeWordMode);
  if (micBtn) micBtn.addEventListener('click', toggleManualMic);

  if (ttsBtn) {
    ttsBtn.addEventListener('click', () => {
      isTtsEnabled = !isTtsEnabled;
      document.getElementById('tts-status').innerText = isTtsEnabled ? 'ON' : 'OFF';
      ttsBtn.style.borderColor = isTtsEnabled ? 'var(--accent-indigo)' : 'var(--panel-border)';
    });
  }

  startWakeWordMode();
}

function startWakeWordMode() {
  isListeningWakeWord = true;
  const btn = document.getElementById('wake-word-toggle-btn');
  const txt = document.getElementById('wake-toggle-text');
  const dot = document.getElementById('wake-dot');
  const card = document.getElementById('voice-status-card');

  if (btn) btn.classList.add('active');
  if (txt) txt.innerText = 'Wake Word: ON';
  if (dot) dot.classList.add('active');
  if (card) card.classList.add('active');

  if (recognition) {
    try { recognition.start(); } catch (e) {}
  }

  fetch('/api/voice/wakeword/toggle?active=true', { method: 'POST' }).catch(() => {});
}

function stopWakeWordMode() {
  isListeningWakeWord = false;
  const btn = document.getElementById('wake-word-toggle-btn');
  const txt = document.getElementById('wake-toggle-text');
  const dot = document.getElementById('wake-dot');
  const card = document.getElementById('voice-status-card');

  if (btn) btn.classList.remove('active');
  if (txt) txt.innerText = 'Wake Word: OFF';
  if (dot) dot.classList.remove('active');
  if (card) card.classList.remove('active');

  if (recognition) {
    try { recognition.stop(); } catch (e) {}
  }

  fetch('/api/voice/wakeword/toggle?active=false', { method: 'POST' }).catch(() => {});
}

function toggleWakeWordMode() {
  if (isListeningWakeWord) stopWakeWordMode();
  else startWakeWordMode();
}

function toggleManualMic() {
  const micBtn = document.getElementById('mic-btn');
  if (isManualMicListening) {
    stopManualListening();
  } else {
    isManualMicListening = true;
    micBtn.classList.add('listening');
    showSpeechHint('Speak now...');

    if (recognition) {
      try { recognition.start(); } catch (e) {}
    } else {
      fetch('/api/voice/listen', { method: 'POST' })
        .then(r => r.json())
        .then(res => {
          if (res.transcript) {
            document.getElementById('cmd-input').value = res.transcript;
            submitCommandText(res.transcript);
          }
        })
        .finally(() => stopManualListening());
    }
  }
}

function stopManualListening() {
  isManualMicListening = false;
  const micBtn = document.getElementById('mic-btn');
  if (micBtn) micBtn.classList.remove('listening');
}

function setVisualizerState(active) {
  const vis = document.getElementById('audio-wave');
  if (vis) {
    if (active) vis.classList.add('listening');
    else vis.classList.remove('listening');
  }
}

function flashVoiceActive() {
  const card = document.getElementById('voice-status-card');
  if (card) {
    card.style.boxShadow = '0 0 30px #ec4899';
    setTimeout(() => { card.style.boxShadow = ''; }, 1500);
  }
}

function showSpeechHint(msg) {
  const hint = document.getElementById('speech-hint');
  const txt = document.getElementById('speech-hint-text');
  if (hint && txt) {
    txt.innerText = msg;
    hint.classList.add('active');
    setTimeout(() => { hint.classList.remove('active'); }, 5000);
  }
}

function speakText(text) {
  if (!isTtsEnabled || !text) return;
  
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel(); // Cancel any lingering speech
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    // Pick natural English voice if available
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Samantha') || v.name.includes('Zira') || v.name.includes('David')) && v.lang.startsWith('en')) || voices.find(v => v.lang.startsWith('en'));
    if (preferredVoice) utterance.voice = preferredVoice;

    utterance.onstart = () => {
      setVisualizerState(true);
      // Temporarily pause recognition while speaking to prevent self-triggering
      if (recognition && isListeningWakeWord) {
        try { recognition.stop(); } catch (e) {}
      }
    };

    utterance.onend = () => {
      setVisualizerState(false);
      // Seamlessly resume continuous voice recognition after speaking
      if (isListeningWakeWord && recognition) {
        setTimeout(() => {
          try { recognition.start(); } catch (e) {}
        }, 300);
      }
    };

    utterance.onerror = () => {
      setVisualizerState(false);
    };

    window.speechSynthesis.speak(utterance);
  } else {
    fetch('/api/voice/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text })
    }).catch(() => {});
  }
}

// ==========================================
// WEBSOCKET & DASHBOARD LIFECYCLE
// ==========================================

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    const indicator = document.getElementById('ws-indicator');
    const text = document.getElementById('ws-text');
    indicator.classList.add('connected');
    text.innerText = 'Connected (Live Pipeline Stream)';
  };

  socket.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data);
      if (payload.type === 'event') {
        handleSystemEvent(payload.event);
      }
    } catch (e) {
      console.error('WS Parsing Error:', e);
    }
  };

  socket.onclose = () => {
    const indicator = document.getElementById('ws-indicator');
    const text = document.getElementById('ws-text');
    indicator.classList.remove('connected');
    text.innerText = 'Disconnected (Reconnecting...)';
    setTimeout(connectWebSocket, 3000);
  };
}

function handleSystemEvent(evt) {
  appendEventLog(evt);

  if (evt.event_type === 'approval_required') {
    fetchApprovals();
    fetchStatus();
    speakText("Action requires human approval in Magnas control center.");
  } else if (evt.event_type === 'task_completed') {
    fetchStatus();
    fetchTasks();
    speakText("Task completed and verified successfully.");
  } else if (evt.event_type === 'task_step_progress') {
    fetchStatus();
    fetchTasks();
    if (evt.data && evt.data.status === 'COMPLETED' && evt.data.result && evt.data.result.output) {
      const outMsg = String(evt.data.result.output);
      if (outMsg.includes('[Magnas Spoke]:')) {
        // Already spoken locally
      }
    }
  } else if (evt.event_type.startsWith('task_')) {
    fetchStatus();
    fetchTasks();
  }
}


async function fetchStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();

    document.getElementById('stat-system').innerText = data.status;
    document.getElementById('stat-approvals').innerText = data.pending_approvals;
    document.getElementById('stat-running').innerText = data.running_tasks;
    document.getElementById('stat-tools').innerText = data.total_tools;

    const badge = document.getElementById('approvals-badge');
    if (badge) {
      badge.innerText = data.pending_approvals;
      badge.style.display = data.pending_approvals > 0 ? 'inline-block' : 'none';
    }

    const banner = document.getElementById('approval-alert-banner');
    if (banner) {
      banner.style.display = data.pending_approvals > 0 ? 'block' : 'none';
    }
  } catch (e) {
    console.error('Failed to fetch status:', e);
  }
}

async function fetchTasks() {
  try {
    const res = await fetch('/api/tasks');
    const tasks = await res.json();
    renderTasksTable(tasks);
    renderTaskStream(tasks.slice(0, 8));
    if (tasks.length > 0) {
      updatePipelineStepper(tasks[0]);
    }
  } catch (e) {
    console.error('Failed to fetch tasks:', e);
  }
}

function updatePipelineStepper(task) {
  const phases = ['UNDERSTOOD', 'PLANNED', 'EXECUTING', 'VERIFYING', 'COMPLETED'];
  phases.forEach(p => {
    const el = document.getElementById(`phase-${p}`);
    if (el) el.classList.remove('active');
  });

  const currentStatus = task.status;
  if (currentStatus === 'RECEIVED' || currentStatus === 'UNDERSTOOD') {
    document.getElementById('phase-UNDERSTOOD')?.classList.add('active');
  } else if (currentStatus === 'PLANNED' || currentStatus === 'POLICY_CHECK' || currentStatus === 'APPROVED') {
    document.getElementById('phase-PLANNED')?.classList.add('active');
  } else if (currentStatus === 'EXECUTING') {
    document.getElementById('phase-EXECUTING')?.classList.add('active');
  } else if (currentStatus === 'VERIFYING') {
    document.getElementById('phase-VERIFYING')?.classList.add('active');
  } else if (currentStatus === 'COMPLETED') {
    document.getElementById('phase-COMPLETED')?.classList.add('active');
  }
}

function renderTaskStream(tasks) {
  const stream = document.getElementById('task-stream');
  if (!stream) return;

  if (!tasks.length) {
    stream.innerHTML = '<div class="empty-state">No commands executed yet. Enter a prompt above to start.</div>';
    return;
  }

  stream.innerHTML = tasks.map(t => {
    const verificationText = t.output && t.output.verification_summary ? t.output.verification_summary : null;
    const stepsList = t.steps || [];

    return `
      <div class="stream-item">
        <div style="display:flex; justify-content:space-between; align-items:center">
          <strong style="color:var(--text-main); font-size:0.95rem">Task: "${t.raw_prompt}"</strong>
          <span class="badge" style="background:${getStatusColor(t.status)}">${t.status}</span>
        </div>
        
        <div style="font-size:0.8rem; color:var(--text-muted)">
          Intent: <span style="color:var(--accent-cyan); font-weight:700">${t.intent || 'PROCESSING'}</span> | 
          Confidence: ${(t.confidence ? (t.confidence * 100).toFixed(0) : 100)}% |
          Risk: <span style="color:${t.highest_risk === 'HIGH' ? '#ef4444' : '#10b981'}">${t.highest_risk}</span>
        </div>

        ${stepsList.length ? `
          <div class="plan-step-box">
            <div style="font-weight:700; font-size:0.78rem; color:var(--accent-indigo); margin-bottom:0.2rem">
              📋 MULTI-STEP EXECUTION PLAN (${stepsList.length} Steps)
            </div>
            ${stepsList.map(s => `
              <div class="plan-step-item">
                <span>${s.description} <code>(${s.tool_name})</code></span>
                <span class="step-status-tag" style="background:${getStepStatusStyle(s.status)}">${s.status}</span>
              </div>
            `).join('')}
          </div>
        ` : ''}

        ${verificationText ? `
          <div class="verification-box">
            🔍 ${verificationText}
          </div>
        ` : ''}
      </div>
    `;
  }).join('');
}

function getStepStatusStyle(status) {
  switch (status) {
    case 'COMPLETED': return 'rgba(16,185,129,0.25); color:#10b981';
    case 'RUNNING': return 'rgba(99,102,241,0.25); color:#6366f1';
    case 'FAILED': return 'rgba(239,68,68,0.25); color:#ef4444';
    default: return 'rgba(255,255,255,0.08); color:var(--text-muted)';
  }
}

function getStatusColor(status) {
  switch (status) {
    case 'COMPLETED': return 'rgba(16,185,129,0.2); color:#10b981';
    case 'FAILED': return 'rgba(239,68,68,0.2); color:#ef4444';
    case 'WAITING_APPROVAL': return 'rgba(245,158,11,0.2); color:#f59e0b';
    case 'EXECUTING': return 'rgba(99,102,241,0.2); color:#6366f1';
    case 'VERIFYING': return 'rgba(236,72,153,0.2); color:#ec4899';
    default: return 'rgba(6,182,212,0.2); color:#06b6d4';
  }
}

function renderTasksTable(tasks) {
  const tbody = document.getElementById('history-table-body');
  if (!tbody) return;

  if (!tasks.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No execution history available.</td></tr>';
    return;
  }

  tbody.innerHTML = tasks.map(t => `
    <tr>
      <td><code style="color:var(--accent-cyan)">${t.task_id}</code></td>
      <td><strong>${t.raw_prompt}</strong></td>
      <td><span class="badge">${t.intent || 'UNKNOWN'}</span></td>
      <td><span class="badge" style="background:${t.highest_risk === 'HIGH' ? 'rgba(239,68,68,0.2); color:#ef4444' : 'rgba(16,185,129,0.2); color:#10b981'}">${t.highest_risk}</span></td>
      <td><strong style="color:${t.status === 'COMPLETED' ? '#10b981' : (t.status === 'FAILED' ? '#ef4444' : '#f59e0b')}">${t.status}</strong></td>
      <td>${new Date(t.created_at * 1000).toLocaleTimeString()}</td>
    </tr>
  `).join('');
}

async function fetchApprovals() {
  try {
    const res = await fetch('/api/approvals');
    const tickets = await res.json();
    renderTickets(tickets);
  } catch (e) {
    console.error('Failed to fetch approvals:', e);
  }
}

function renderTickets(tickets) {
  const container = document.getElementById('tickets-container');
  if (!container) return;

  if (!tickets.length) {
    container.innerHTML = '<div class="empty-state">No pending human approval requests.</div>';
    return;
  }

  container.innerHTML = tickets.map(ticket => `
    <div class="ticket-card">
      <div class="ticket-header">
        <h4>${ticket.action_type}</h4>
        <span class="risk-badge">${ticket.risk_level} RISK</span>
      </div>
      <p style="font-size:0.9rem; color:var(--text-muted)">${ticket.reason}</p>
      <div style="background:rgba(0,0,0,0.4); padding:0.6rem; border-radius:8px; font-family:var(--font-mono); font-size:0.8rem; border:1px solid var(--panel-border)">
        Target: ${ticket.target_summary}
      </div>
      <div class="ticket-actions">
        <button class="btn btn-success" onclick="approveTicket('${ticket.ticket_id}')">✓ Approve & Execute</button>
        <button class="btn btn-danger" onclick="rejectTicket('${ticket.ticket_id}')">✕ Reject Action</button>
      </div>
    </div>
  `).join('');
}

async function approveTicket(ticketId) {
  try {
    await fetch(`/api/approvals/${ticketId}/approve`, { method: 'POST' });
    speakText("Approval granted. Action executed.");
    fetchApprovals();
    fetchStatus();
  } catch (e) {
    console.error('Approve failed:', e);
  }
}

async function rejectTicket(ticketId) {
  try {
    await fetch(`/api/approvals/${ticketId}/reject`, { method: 'POST' });
    speakText("Action rejected.");
    fetchApprovals();
    fetchStatus();
  } catch (e) {
    console.error('Reject failed:', e);
  }
}

async function fetchTools() {
  try {
    const res = await fetch('/api/tools');
    const tools = await res.json();
    renderTools(tools);
  } catch (e) {
    console.error('Failed to fetch tools:', e);
  }
}

function renderTools(tools) {
  const container = document.getElementById('tools-container');
  if (!container) return;

  container.innerHTML = tools.map(t => `
    <div class="tool-card">
      <div style="display:flex; justify-content:space-between; align-items:center">
        <h4 style="color:var(--accent-cyan)">${t.name}</h4>
        <span class="badge" style="background:${t.risk_level === 'HIGH' ? 'rgba(239,68,68,0.2); color:#ef4444' : 'rgba(16,185,129,0.2); color:#10b981'}">${t.risk_level}</span>
      </div>
      <p style="font-size:0.85rem; color:var(--text-muted)">${t.description}</p>
    </div>
  `).join('');
}

function appendStreamItem(task) {
  const stream = document.getElementById('task-stream');
  if (!stream) return;

  const item = document.createElement('div');
  item.className = 'stream-item';
  item.innerHTML = `
    <div><strong>[${new Date().toLocaleTimeString()}] Prompt:</strong> "${task.raw_prompt}"</div>
    <div style="color:var(--accent-cyan)">Status: ${task.status} | Intent: ${task.intent || 'UNDERSTANDING INTENT...'}</div>
  `;
  stream.prepend(item);
}

function appendEventLog(evt) {
  const log = document.getElementById('event-log');
  if (!log) return;

  const item = document.createElement('div');
  item.style.borderBottom = '1px solid var(--panel-border)';
  item.style.padding = '0.45rem 0';
  item.innerHTML = `<span style="color:var(--text-muted)">[${new Date(evt.timestamp * 1000).toLocaleTimeString()}]</span> <strong style="color:var(--accent-magenta)">${evt.event_type}</strong> ${evt.task_id ? `(${evt.task_id})` : ''}`;
  log.prepend(item);
}

async function fetchAuditLogs() {
  try {
    const res = await fetch('/api/audit-logs');
    const logs = await res.json();
    renderAuditLogs(logs);
  } catch (e) {
    console.error('Failed to fetch audit logs:', e);
  }
}

function renderAuditLogs(logs) {
  const tbody = document.getElementById('audit-table-body');
  if (!tbody) return;

  if (!logs.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No security or activity audit logs recorded yet.</td></tr>';
    return;
  }

  tbody.innerHTML = logs.map(l => `
    <tr>
      <td>${new Date(l.timestamp * 1000).toLocaleTimeString()}</td>
      <td><code style="color:var(--accent-cyan)">${l.action}</code></td>
      <td><span class="badge" style="background:rgba(99,102,241,0.18); color:var(--accent-indigo)">${l.resource_service}</span></td>
      <td><span class="badge" style="background:rgba(6,182,212,0.15); color:var(--accent-cyan)">${l.permission_used}</span></td>
      <td><span class="badge" style="background:${l.risk_level === 'HIGH' ? 'rgba(239,68,68,0.2); color:#ef4444' : 'rgba(16,185,129,0.2); color:#10b981'}">${l.risk_level}</span></td>
      <td><strong style="color:${l.status === 'COMPLETED' ? '#10b981' : (l.status === 'FAILED' ? '#ef4444' : '#f59e0b')}">${l.status}</strong></td>
      <td><code>${l.task_id || 'N/A'}</code></td>
    </tr>
  `).join('');
}
