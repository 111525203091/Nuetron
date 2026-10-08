/* ════════════════════════════════════════
   JARVIS Web App — JavaScript
   ════════════════════════════════════════ */

'use strict';

// ─── State ────────────────────────────────────────────────────
const state = {
  socket: null,
  isThinking: false,
  voiceOutputEnabled: true,
  voiceInputActive: false,
  recognition: null,
  theme: 'dark',
  msgHistory: [],
};

// ─── DOM Refs ─────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);
const chatMessages = $('chat-messages');
const userInput    = $('user-input');
const sendBtn      = $('send-btn');
const micBtn       = $('mic-btn');
const thinkingEl   = $('thinking');
const connDot      = $('conn-dot');
const connStatus   = $('conn-status');
const toastEl      = $('toast');
const clockEl      = $('clock');

// ─── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initSocket();
  initVoice();
  initParticles();
  initClock();
  initSystemStats();
  initQuickActions();
  initControls();
  initInputHandlers();
  initPWA();
  initTerminal();
  initLocation();
});

// ─── Socket.IO ────────────────────────────────────────────────
function initSocket() {
  state.socket = io();

  state.socket.on('connect', () => {
    connDot.className = 'status-dot online';
    connStatus.textContent = 'ONLINE';
    showToast('Connected to ULTRON');
  });

  state.socket.on('disconnect', () => {
    connDot.className = 'status-dot';
    connStatus.textContent = 'OFFLINE';
    showToast('Connection lost — attempting to reconnect...', 'warn');
  });

  state.socket.on('status', (data) => {
    if (data.connected) {
      connDot.className = 'status-dot online';
      connStatus.textContent = 'ONLINE';
    }
  });

  state.socket.on('thinking', (data) => {
    setThinking(data.status);
  });

  state.socket.on('response', (data) => {
    setThinking(false);
    appendMessage('jarvis', data.message);
    if (state.voiceOutputEnabled) {
      speakText(data.message);
    }
    addHistory(data.message.substring(0, 60) + '...');
  });

  state.socket.on('error', (data) => {
    setThinking(false);
    appendMessage('jarvis', `⚠ ${data.message}`, true);
  });
}

// ─── Thinking watchdog ────────────────────────────────────────
let _thinkingTimer = null;

// ─── Thinking Indicator ───────────────────────────────────────
function setThinking(active) {
  state.isThinking = active;
  thinkingEl.style.display = active ? 'flex' : 'none';
  sendBtn.disabled = active;
  if (active) chatMessages.scrollTop = chatMessages.scrollHeight;

  // Clear any existing watchdog
  if (_thinkingTimer) { clearTimeout(_thinkingTimer); _thinkingTimer = null; }

  // Safety: auto-reset after 12s so UI never gets permanently stuck
  if (active) {
    _thinkingTimer = setTimeout(() => {
      setThinking(false);
      appendMessage('jarvis', '⚠ Request timed out. Please try again, Sir.');
    }, 25000);
  }
}

// ─── Send Message ─────────────────────────────────────────────
function sendMessage(text) {
  text = text.trim();
  if (!text) return;
  // If stuck in thinking state, force-reset instead of dropping the message
  if (state.isThinking) setThinking(false);

  appendMessage('user', text);
  state.msgHistory.push(text);
  userInput.value = '';
  autoResize(userInput);
  setThinking(true);

  if (state.socket && state.socket.connected) {
    state.socket.emit('message', { message: text });
  } else {
    // Socket disconnected: instant HTTP fallback so user is never ignored
    fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    })
    .then(r => r.json())
    .then(data => {
      setThinking(false);
      appendMessage('jarvis', data.response || data.error);
      if (state.voiceOutputEnabled && data.response) {
        speakText(data.response);
      }
    })
    .catch(err => {
      setThinking(false);
      appendMessage('jarvis', 'Connection error: ' + err.message, true);
    });
  }
}
function appendMessage(role, text, isError = false) {
  // Hide welcome message
  const welcome = chatMessages.querySelector('.welcome-msg');
  if (welcome) welcome.style.display = 'none';

  const now = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  const isJarvis = role === 'jarvis';

  const msgEl = document.createElement('div');
  msgEl.className = `msg ${role}`;

  const avatar = isJarvis ? 'U' : '⬡';
  const name   = isJarvis ? 'ULTRON' : 'YOU';
  let parsedText = isJarvis
    ? (typeof marked !== 'undefined' ? marked.parse(text) : escapeHtml(text))
    : `<p>${escapeHtml(text)}</p>`;

  // Check if message references screenshot and inject preview
  if (isJarvis && text.includes('/static/screenshots/latest.png')) {
    const timestamp = Date.now();
    parsedText += `
      <div class="screenshot-preview-card" style="margin-top:12px; border:1px solid rgba(255,23,68,0.4); border-radius:6px; overflow:hidden; max-width:480px; background:#0c0c12;">
        <a href="/static/screenshots/latest.png?t=${timestamp}" target="_blank">
          <img src="/static/screenshots/latest.png?t=${timestamp}" alt="ULTRON Screenshot" style="width:100%; display:block; cursor:pointer;" title="Click to view full size" />
        </a>
        <div style="padding:6px 10px; font-size:0.75rem; color:rgba(255,255,255,0.6); display:flex; justify-content:space-between; align-items:center;">
          <span>🖥️ Captured Display</span>
          <a href="/static/screenshots/latest.png?t=${timestamp}" download="ultron_screenshot.png" style="color:#ff1744; text-decoration:none; font-weight:600;">Download 💾</a>
        </div>
      </div>
    `;
  }

  msgEl.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-content">
      <div class="msg-meta">${name} · ${now}</div>
      <div class="msg-bubble${isError ? ' error' : ''}">${parsedText}</div>
    </div>
  `;

  chatMessages.appendChild(msgEl);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>');
}

// ─── Clock ────────────────────────────────────────────────────
function initClock() {
  function updateClock() {
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString('en-US', {
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    });
  }
  updateClock();
  setInterval(updateClock, 1000);
}

// ─── System Stats ─────────────────────────────────────────────
function initSystemStats() {
  function fetchStats() {
    fetch('/api/status')
      .then(r => r.json())
      .then(data => {
        const m = data.metrics;
        if (!m) return;

        // CPU — from background sampler, always smooth and accurate
        const cpu = m.cpu_percent ?? 0;
        $('cpu-bar').style.width = cpu + '%';
        $('cpu-val').textContent = cpu.toFixed(1) + '%';

        // RAM
        const ram = m.ram_percent ?? 0;
        $('ram-bar').style.width = ram + '%';
        $('ram-val').textContent = ram.toFixed(1) + '%';

        // Disk
        const disk = m.disk_percent ?? 0;
        $('disk-bar').style.width = disk + '%';
        $('disk-val').textContent = disk.toFixed(1) + '%';

        // Battery (if present)
        if (m.battery_percent !== undefined) {
          const batEl = $('battery-val');
          if (batEl) batEl.textContent = m.battery_percent.toFixed(0) + '% ' + (m.battery_status === 'Charging' ? '⚡' : '🔋');
        }
      })
      .catch(() => {});
  }
  fetchStats();
  setInterval(fetchStats, 5000); // Poll every 5s for smooth live readings
}

// ─── Voice ────────────────────────────────────────────────────
function initVoice() {
  // TTS
  state.speechSynth = window.speechSynthesis;

  // STT
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    state.recognition = new SpeechRecognition();
    state.recognition.continuous = false;
    state.recognition.interimResults = false;
    state.recognition.lang = 'en-US';

    state.recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      userInput.value = transcript;
      stopVoiceInput();
      sendMessage(transcript);
    };

    state.recognition.onerror = () => stopVoiceInput();
    state.recognition.onend  = () => stopVoiceInput();
  }
}

function speakText(text) {
  if (!state.speechSynth) return;

  // Clean text of markdown, code blocks, raw URLs, and formatting for natural speech
  let clean = text
    .replace(/```[\s\S]*?```/g, 'Code block omitted.')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/https?:\/\/\S+/g, 'link')
    .replace(/#{1,6}\s+/g, '')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[•\-\*]\s+/g, '')
    .trim();

  if (!clean) return;

  // Cap speech length to avoid drone-on, but keep full thought
  if (clean.length > 400) {
    clean = clean.substring(0, 397) + '...';
  }

  state.speechSynth.cancel();
  const utt = new SpeechSynthesisUtterance(clean);

  // Human conversational tuning: slightly relaxed rate, natural warm pitch
  utt.rate = 1.0;
  utt.pitch = 1.02;
  utt.volume = 1.0;

  // Prioritize modern neural and natural voices
  const voices = state.speechSynth.getVoices();
  const naturalVoice = voices.find(v => {
    const name = v.name.toLowerCase();
    return (
      (name.includes('natural') || name.includes('online') || name.includes('neural')) &&
      v.lang.startsWith('en')
    );
  }) || voices.find(v => {
    const name = v.name.toLowerCase();
    return (
      (name.includes('guy') || name.includes('christopher') || name.includes('ryan') ||
       name.includes('google us english') || name.includes('david')) &&
      v.lang.startsWith('en')
    );
  }) || voices.find(v => v.lang.startsWith('en'));

  if (naturalVoice) {
    utt.voice = naturalVoice;
  }

  state.speechSynth.speak(utt);
}


function startVoiceInput() {
  if (!state.recognition) {
    showToast('Voice input not supported in this browser.', 'warn');
    return;
  }
  state.voiceInputActive = true;
  micBtn.classList.add('recording');
  state.recognition.start();
}

function stopVoiceInput() {
  state.voiceInputActive = false;
  micBtn.classList.remove('recording');
  try { state.recognition.stop(); } catch(e) {}
}

// ─── History ──────────────────────────────────────────────────
function addHistory(text) {
  const histList = $('history-list');
  const item = document.createElement('div');
  item.className = 'history-item';
  item.textContent = text;
  item.title = text;
  item.addEventListener('click', () => {
    userInput.value = text;
    userInput.focus();
  });
  histList.prepend(item);
  // Keep only last 20
  while (histList.children.length > 20) {
    histList.removeChild(histList.lastChild);
  }
}

// ─── Quick Actions ────────────────────────────────────────────
function initQuickActions() {
  document.querySelectorAll('.qa-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const cmd = btn.dataset.cmd;
      if (cmd) sendMessage(cmd);
    });
  });
}

// ─── Controls ─────────────────────────────────────────────────
function initControls() {
  $('btn-voice').addEventListener('click', () => {
    $('btn-voice').classList.toggle('active');
    const active = $('btn-voice').classList.contains('active');
    showToast(active ? '🎤 Voice input ready — click mic to speak' : '🎤 Voice input disabled');
  });

  $('btn-speak').addEventListener('click', () => {
    state.voiceOutputEnabled = !state.voiceOutputEnabled;
    $('btn-speak').classList.toggle('active', !state.voiceOutputEnabled);
    showToast(state.voiceOutputEnabled ? '🔊 Voice output: ON' : '🔇 Voice output: OFF');
    if (!state.voiceOutputEnabled && state.speechSynth) {
      state.speechSynth.cancel();
    }
  });

  $('btn-theme').addEventListener('click', () => {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', state.theme === 'light' ? 'light' : '');
    $('btn-theme').textContent = state.theme === 'dark' ? '🌙' : '☀️';
  });

  $('btn-fullscreen').addEventListener('click', () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  });

  micBtn.addEventListener('click', () => {
    if (state.voiceInputActive) {
      stopVoiceInput();
    } else {
      startVoiceInput();
    }
  });
}

// ─── PWA Installation ─────────────────────────────────────────
function initPWA() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js').catch(() => {});
  }

  let deferredPrompt = null;
  const installBtn = $('btn-install');

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (installBtn) {
      installBtn.style.display = 'inline-flex';
      installBtn.addEventListener('click', async () => {
        if (!deferredPrompt) return;
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        if (outcome === 'accepted') {
          installBtn.style.display = 'none';
          showToast('ULTRON Desktop App Installed!');
        }
        deferredPrompt = null;
      });
    }
  });

  window.addEventListener('appinstalled', () => {
    if (installBtn) installBtn.style.display = 'none';
    showToast('ULTRON running in Standalone App Mode');
  });
}

// ─── Input Handlers ───────────────────────────────────────────
function initInputHandlers() {
  sendBtn.addEventListener('click', () => sendMessage(userInput.value));

  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(userInput.value);
    }
  });

  userInput.addEventListener('input', () => autoResize(userInput));

  // Up arrow to recall last message
  let historyIndex = -1;
  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowUp' && userInput.value === '') {
      if (state.msgHistory.length > 0) {
        historyIndex = Math.min(historyIndex + 1, state.msgHistory.length - 1);
        userInput.value = state.msgHistory[state.msgHistory.length - 1 - historyIndex];
      }
    } else if (e.key === 'ArrowDown') {
      historyIndex = Math.max(historyIndex - 1, -1);
      userInput.value = historyIndex >= 0
        ? state.msgHistory[state.msgHistory.length - 1 - historyIndex]
        : '';
    } else {
      historyIndex = -1;
    }
  });
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

// ─── Toast ────────────────────────────────────────────────────
let toastTimeout = null;
function showToast(msg, type = 'info') {
  clearTimeout(toastTimeout);
  toastEl.textContent = msg;
  toastEl.className = `toast show ${type}`;
  toastTimeout = setTimeout(() => {
    toastEl.classList.remove('show');
  }, 3000);
}

// ─── Particles ────────────────────────────────────────────────
function initParticles() {
  const canvas = $('particles-canvas');
  const ctx = canvas.getContext('2d');
  let particles = [];
  const N = 60;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x = Math.random() * canvas.width;
      this.y = Math.random() * canvas.height;
      this.r = Math.random() * 1.5 + 0.3;
      this.vx = (Math.random() - 0.5) * 0.3;
      this.vy = (Math.random() - 0.5) * 0.3;
      this.opacity = Math.random() * 0.5 + 0.1;
    }
    update() {
      this.x += this.vx;
      this.y += this.vy;
      if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) {
        this.reset();
      }
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(0, 212, 255, ${this.opacity})`;
      ctx.fill();
    }
  }

  for (let i = 0; i < N; i++) particles.push(new Particle());

  function drawLines() {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(0, 212, 255, ${0.08 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
  }

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => { p.update(); p.draw(); });
    drawLines();
    requestAnimationFrame(animate);
  }
  animate();
}

// ─── Terminal Panel ───────────────────────────────────────────
function initTerminal() {
  const overlay    = document.getElementById('terminal-overlay');
  const termOutput = document.getElementById('term-output');
  const termInput  = document.getElementById('term-input');
  const termCwd    = document.getElementById('term-cwd');
  const termRun    = document.getElementById('term-run');
  const termClose  = document.getElementById('term-close');
  const qaTermBtn  = document.getElementById('qa-terminal');

  if (!overlay) return;

  let currentCwd = null;
  let cmdHistory = [];
  let histIdx = -1;

  function openTerminal() {
    overlay.classList.remove('hidden');
    termInput.focus();
    if (termOutput.children.length === 0) {
      appendTermLine('system', '⚡ ULTRON Terminal — Type a command and press Enter or click RUN');
      appendTermLine('system', '📂 Working directory: ' + (currentCwd || '~'));
    }
  }

  function closeTerminal() {
    overlay.classList.add('hidden');
  }

  if (qaTermBtn) qaTermBtn.addEventListener('click', openTerminal);
  if (termClose) termClose.addEventListener('click', closeTerminal);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) closeTerminal(); });

  function appendTermLine(type, text) {
    const line = document.createElement('div');
    line.className = 'term-line term-' + type;
    line.textContent = text;
    termOutput.appendChild(line);
    termOutput.scrollTop = termOutput.scrollHeight;
  }

  async function runCommand() {
    const cmd = termInput.value.trim();
    if (!cmd) return;

    cmdHistory.unshift(cmd);
    histIdx = -1;
    termInput.value = '';

    appendTermLine('input', '$ ' + cmd);
    appendTermLine('system', '⏳ Executing...');

    try {
      const res = await fetch('/api/terminal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: cmd, cwd: currentCwd }),
      });
      const data = await res.json();

      // Remove the "Executing..." line
      const lastLine = termOutput.lastElementChild;
      if (lastLine && lastLine.textContent === '⏳ Executing...') termOutput.removeChild(lastLine);

      if (data.stdout) {
        data.stdout.split('\n').forEach(l => appendTermLine('stdout', l));
      }
      if (data.stderr) {
        data.stderr.split('\n').forEach(l => appendTermLine('stderr', l));
      }
      const rc = data.returncode;
      appendTermLine(rc === 0 ? 'success' : 'error',
        `→ Exit ${rc} | Dir: ${data.cwd}`);

      // Update tracked cwd if command was cd
      if (cmd.toLowerCase().startsWith('cd ') && rc === 0 && data.cwd) {
        currentCwd = data.cwd;
        termCwd.textContent = data.cwd;
      } else if (data.cwd) {
        currentCwd = data.cwd;
        termCwd.textContent = data.cwd;
      }
    } catch (err) {
      const lastLine = termOutput.lastElementChild;
      if (lastLine && lastLine.textContent === '⏳ Executing...') termOutput.removeChild(lastLine);
      appendTermLine('error', '✗ Network error: ' + err.message);
    }

    termInput.focus();
  }

  termRun.addEventListener('click', runCommand);
  termInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { runCommand(); return; }
    if (e.key === 'ArrowUp') {
      histIdx = Math.min(histIdx + 1, cmdHistory.length - 1);
      if (cmdHistory[histIdx]) termInput.value = cmdHistory[histIdx];
    }
    if (e.key === 'ArrowDown') {
      histIdx = Math.max(histIdx - 1, -1);
      termInput.value = histIdx >= 0 ? cmdHistory[histIdx] : '';
    }
    if (e.key === 'Escape') closeTerminal();
  });
}

// ─── Location Widget ──────────────────────────────────────────
function initLocation() {
  const widget      = document.getElementById('location-widget');
  const locationTxt = document.getElementById('location-text');
  const closeBtn    = document.getElementById('location-close');

  if (!widget) return;
  if (closeBtn) closeBtn.addEventListener('click', () => widget.classList.add('hidden'));

  // Auto-detect location on load and show in HUD corner quietly
  fetch('/api/location')
    .then(r => r.json())
    .then(data => {
      if (data.ok && data.city) {
        locationTxt.textContent = `📍 ${data.city}, ${data.country}`;
        widget.classList.remove('hidden');
      }
    })
    .catch(() => {}); // fail silently
}
