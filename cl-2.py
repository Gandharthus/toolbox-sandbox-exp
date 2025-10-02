<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>MCP Logs Navigator</title>
  <style>
    :root {
      --bg: #0b0f19;
      --panel: #111827;
      --muted: #94a3b8;
      --text: #e5e7eb;
      --accent: #60a5fa;
      --ok: #34d399;
      --warn: #fbbf24;
      --err: #f87171;
      --card: #0f172a;
      --border: #1f2937;
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial, "Noto Sans", "Apple Color Emoji", "Segoe UI Emoji";
      background: linear-gradient(180deg, var(--bg), #0c1224 60%);
      color: var(--text);
    }
    a { color: var(--accent); text-decoration: none; }
    .container { max-width: 1200px; margin: 0 auto; padding: 24px; }
    header {
      display: flex; gap: 16px; align-items: center; justify-content: space-between; margin-bottom: 18px;
    }
    .title { font-size: 22px; font-weight: 700; letter-spacing: .2px; }
    .card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px; padding: 16px; box-shadow: 0 10px 30px rgba(0,0,0,.25);
    }
    .grid { display: grid; gap: 16px; }
    @media (min-width: 900px) { .grid-cols-2 { grid-template-columns: 1.1fr 1fr; } }
    .row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
    label { font-size: 12px; color: var(--muted); }
    input[type="text"], input[type="number"], input[type="datetime-local"], textarea, select {
      width: 100%; background: var(--card); color: var(--text); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; outline: none;
    }
    textarea { min-height: 92px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 13px; }
    .btn { appearance: none; border: 1px solid var(--border); background: #0b1222; color: var(--text); padding: 10px 14px; border-radius: 10px; cursor: pointer; font-weight: 600; }
    .btn[disabled] { opacity: .5; cursor: not-allowed; }
    .btn.primary { background: linear-gradient(170deg, #0b3b7a, #0c2352); border-color: #17315f; }
    .btn.ghost { background: transparent; border-color: var(--border); }
    .btn.warn { background: #3a2a05; border-color: #704c0b; }
    .badge { font-size: 11px; padding: 4px 8px; border-radius: 999px; background: #0b1630; border: 1px solid #1b2a4d; color: #93c5fd; }
    .muted { color: var(--muted); font-size: 12px; }
    .divider { height: 1px; background: var(--border); margin: 14px 0; }
    .tabs { display: flex; gap: 8px; border-bottom: 1px solid var(--border); margin-bottom: 12px; }
    .tab { padding: 10px 12px; border: 1px solid var(--border); border-bottom: none; border-radius: 10px 10px 0 0; background: #0d1428; cursor: pointer; font-weight: 600; }
    .tab.active { background: #0c1e3e; color: #bfdbfe; }
    .hidden { display: none; }
    .json-view { white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; background: #0a1226; border: 1px solid var(--border); padding: 12px; border-radius: 10px; font-size: 12px; }
    .pill { display: inline-flex; align-items: center; gap: 6px; padding: 6px 10px; border-radius: 999px; border: 1px solid var(--border); background: #0a1325; }
    .status-dot { width: 8px; height: 8px; border-radius: 999px; background: var(--warn); display: inline-block; }
    .status-dot.ok { background: var(--ok); }
    .status-dot.err { background: var(--err); }
    details { background: #0b1222; border: 1px solid var(--border); border-radius: 10px; padding: 8px 10px; }
    summary { cursor: pointer; font-weight: 600; }
    .right { text-align: right; }
    .kvs { display: grid; grid-template-columns: 180px 1fr; gap: 10px; }
    .hl { color: #f59e0b; }
    .footer { margin-top: 22px; font-size: 12px; color: var(--muted); }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="title">LaaS — Talk‑with‑your‑logs (MCP Client)</div>
      <div class="row">
        <span id="serverName" class="badge">Server: –</span>
        <span id="sessionBadge" class="badge">Session: –</span>
      </div>
    </header>

    <!-- CONNECTION PANEL -->
    <div class="card grid grid-cols-2" id="connectionPanel">
      <div>
        <div class="row">
          <div style="flex:1">
            <label for="endpoint">MCP endpoint (Streamable HTTP)</label>
            <input id="endpoint" type="text" placeholder="http://localhost:8000/mcp" value="http://localhost:8000/mcp" />
          </div>
          <div>
            <label>&nbsp;</label>
            <div class="row">
              <button class="btn primary" id="connectBtn">Connect</button>
              <button class="btn ghost" id="disconnectBtn" disabled>Disconnect</button>
            </div>
          </div>
        </div>
        <div class="muted" style="margin-top:8px">We follow MCP initialize → initialized, keep a session id, and call tools over POST. Progress and logging stream over SSE when the server chooses to stream.</div>
      </div>
      <div>
        <div class="kvs">
          <div>Protocol</div><div id="proto">—</div>
          <div>Capabilities</div><div id="caps">—</div>
          <div>Status</div><div><span class="status-dot" id="statusDot"></span> <span id="statusText">Disconnected</span></div>
        </div>
      </div>
    </div>

    <!-- MAIN UI -->
    <div class="card" style="margin-top:16px;" id="appCard" hidden>
      <div class="tabs">
        <div class="tab active" data-tab="search">Search</div>
        <div class="tab" data-tab="patterns">Top patterns</div>
        <div class="tab" data-tab="anomalies">Anomalies</div>
        <div class="tab" data-tab="snapshot">Change snapshot</div>
      </div>

      <div id="tab-search">
        <div class="grid grid-cols-2">
          <div>
            <label>Query (ES DSL or KQL)</label>
            <textarea id="searchQuery" placeholder="@message:(error OR timeout) AND service:payments AND env:prod"></textarea>
          </div>
          <div>
            <div class="row">
              <div style="flex:1">
                <label>From</label>
                <input id="searchFrom" type="datetime-local" />
              </div>
              <div style="flex:1">
                <label>To</label>
                <input id="searchTo" type="datetime-local" />
              </div>
            </div>
            <div class="row" style="margin-top:8px">
              <div style="flex:1">
                <label>Indices (comma‑sep, optional)</label>
                <input id="searchIndices" type="text" placeholder="logs-*,app-2025.10.*" />
              </div>
              <div>
                <label>Limit</label>
                <input id="searchLimit" type="number" min="1" max="10000" value="200" />
              </div>
            </div>
            <div class="row" style="margin-top:8px; justify-content:space-between">
              <label><input id="searchRedact" type="checkbox" checked /> Redact sensitive</label>
              <div class="row">
                <button class="btn" id="previewSearchBtn">Preview args</button>
                <button class="btn primary" id="runSearchBtn">Run search</button>
                <button class="btn warn" id="cancelSearchBtn" disabled>Cancel</button>
              </div>
            </div>
          </div>
        </div>
        <div class="divider"></div>
        <div id="searchResult"></div>
      </div>

      <div id="tab-patterns" class="hidden">
        <div class="grid grid-cols-2">
          <div class="row">
            <div style="flex:1"><label>Service</label><input id="patService" type="text" placeholder="payments" /></div>
            <div style="flex:1"><label>Env</label><input id="patEnv" type="text" placeholder="prod" /></div>
          </div>
          <div class="row">
            <div style="flex:1"><label>From</label><input id="patFrom" type="datetime-local" /></div>
            <div style="flex:1"><label>To</label><input id="patTo" type="datetime-local" /></div>
            <div><label>Top K</label><input id="patK" type="number" min="1" max="100" value="20" /></div>
          </div>
        </div>
        <div class="row" style="margin-top:8px; justify-content:flex-end">
          <button class="btn" id="previewPatBtn">Preview args</button>
          <button class="btn primary" id="runPatBtn">Get patterns</button>
        </div>
        <div class="divider"></div>
        <div id="patResult"></div>
      </div>

      <div id="tab-anomalies" class="hidden">
        <div class="grid grid-cols-2">
          <div class="row">
            <div style="flex:1"><label>Service</label><input id="anoService" type="text" placeholder="payments" /></div>
            <div style="flex:1"><label>Env</label><input id="anoEnv" type="text" placeholder="prod" /></div>
          </div>
          <div class="row">
            <div style="flex:1"><label>From</label><input id="anoFrom" type="datetime-local" /></div>
            <div style="flex:1"><label>To</label><input id="anoTo" type="datetime-local" /></div>
          </div>
        </div>
        <div class="row" style="margin-top:8px; justify-content:flex-end">
          <button class="btn" id="previewAnoBtn">Preview args</button>
          <button class="btn primary" id="runAnoBtn">Show anomalies</button>
        </div>
        <div class="divider"></div>
        <div id="anoResult"></div>
      </div>

      <div id="tab-snapshot" class="hidden">
        <div class="grid grid-cols-2">
          <div class="row">
            <div style="flex:1"><label>Service</label><input id="snapService" type="text" placeholder="payments" /></div>
            <div style="flex:1"><label>Env</label><input id="snapEnv" type="text" placeholder="prod" /></div>
            <div style="flex:1"><label>Change ID</label><input id="snapChangeId" type="text" placeholder="deploy-2025-10-02-1234" /></div>
          </div>
          <div class="row">
            <div><label>Pre (min)</label><input id="snapPre" type="number" min="1" max="120" value="15" /></div>
            <div><label>Post (min)</label><input id="snapPost" type="number" min="1" max="240" value="30" /></div>
          </div>
        </div>
        <div class="row" style="margin-top:8px; justify-content:flex-end">
          <button class="btn" id="previewSnapBtn">Preview args</button>
          <button class="btn primary" id="runSnapBtn">Compare window</button>
        </div>
        <div class="divider"></div>
        <div id="snapResult"></div>
      </div>

      <div class="divider"></div>
      <details>
        <summary>Protocol log</summary>
        <div id="log"></div>
      </details>
    </div>

    <div class="footer">Tip: you can export JSON from any pane via the ⤓ button.</div>
  </div>

  <dialog id="confirmDialog">
    <form method="dialog" style="max-width:780px">
      <h3>Confirm tool call</h3>
      <div class="muted">Review the tool and arguments the client will send to the MCP server.</div>
      <div class="divider"></div>
      <div id="confirmBody" class="json-view"></div>
      <div class="row" style="margin-top:12px; justify-content:flex-end">
        <button class="btn ghost" value="cancel">Cancel</button>
        <button class="btn primary" value="ok">Proceed</button>
      </div>
    </form>
  </dialog>

  <script>
  // ---------- Utilities ----------
  const el = (id) => document.getElementById(id);
  const fmtJSON = (obj) => JSON.stringify(obj, null, 2);
  function nowISO(dtInput) {
    // dtInput value from <input type="datetime-local"> is local time without TZ; convert to ISO
    if (!dtInput) return null;
    const d = new Date(dtInput);
    return d.toISOString();
  }
  function makeResultCard(title, json, extra = "") {
    const id = Math.random().toString(36).slice(2);
    const copy = () => navigator.clipboard.writeText(fmtJSON(json));
    const download = () => {
      const blob = new Blob([fmtJSON(json)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `${title}-${id}.json`; a.click();
      URL.revokeObjectURL(url);
    };
    return `
      <div class="card" style="background: var(--card); margin: 8px 0">
        <div class="row" style="justify-content: space-between; align-items:center">
          <div style="font-weight:700">${title}</div>
          <div class="row">
            ${extra}
            <button class="btn" onclick="(${copy.toString()})()">Copy</button>
            <button class="btn" onclick="(${download.toString()})()">⤓</button>
          </div>
        </div>
        <div class="json-view">${fmtJSON(json).replace(/&/g,'&amp;').replace(/</g,'&lt;')}</div>
      </div>`;
  }

  // ---------- Minimal MCP Streamable HTTP client (browser) ----------
  class MCPHttpClient {
    constructor(endpoint) {
      this.endpoint = endpoint;
      this.sessionId = null;
      this.protocolVersion = '2025-03-26';
      this.nextId = 1;
      this.notificationsController = null; // AbortController for GET stream
    }

    async initialize() {
      const initReq = {
        jsonrpc: '2.0',
        id: this.nextId++,
        method: 'initialize',
        params: {
          protocolVersion: this.protocolVersion,
          capabilities: { sampling: {}, roots: { listChanged: true } },
          clientInfo: { name: 'laas-logs-web-client', version: '0.1.0', title: 'LaaS Logs Navigator' }
        }
      };
      const { headers, messages } = await this.#post([initReq]);
      // Expect an InitializeResult
      const resp = messages.find(m => m.id === initReq.id && (m.result || m.error));
      if (!resp || resp.error) throw new Error('Initialize failed: ' + (resp && resp.error && resp.error.message));
      // Capture session header if present
      this.sessionId = headers.get('Mcp-Session-Id') || null;
      // Send "initialized" notification
      await this.notify('notifications/initialized');
      return resp.result; // { protocolVersion, capabilities, serverInfo, instructions? }
    }

    async listTools() {
      const id = this.nextId++;
      const { messages } = await this.#post([{ jsonrpc: '2.0', id, method: 'tools/list' }]);
      const resp = messages.find(m => m.id === id);
      if (resp.error) throw new Error(resp.error.message);
      return resp.result;
    }

    async callTool(name, args, { onProgress, onLog } = {}) {
      const id = this.nextId++;
      const req = { jsonrpc: '2.0', id, method: 'tools/call', params: { name, arguments: args } };
      const { messages, streamReader } = await this.#post([req]);

      // If server returned JSON directly (no SSE), handle here
      if (!streamReader) {
        const resp = messages.find(m => m.id === id);
        if (!resp) throw new Error('No response for tool call');
        if (resp.error) throw new Error(resp.error.message);
        return resp.result;
      }

      // If streaming, we already accumulated any initial messages; also attach handlers
      for (const m of messages) {
        if (m.method === 'notifications/progress' && onProgress) onProgress(m.params);
        if (m.method && m.method.startsWith('notifications/logging') && onLog) onLog(m.params);
      }
      // Read remaining SSE events until our response arrives
      let result = null;
      while (true) {
        const { done, value } = await streamReader.read();
        if (done) break;
        const events = this.#parseSSEChunk(value);
        for (const ev of events) {
          try {
            const msg = JSON.parse(ev);
            if (Array.isArray(msg)) {
              for (const item of msg) this.#handleMessage(item);
            } else {
              this.#handleMessage(msg);
              if (msg.id === id && (msg.result || msg.error)) {
                if (msg.error) throw new Error(msg.error.message);
                result = msg.result;
              }
            }
          } catch (_) { /* ignore parse errors */ }
        }
        if (result) break;
      }
      if (!result) throw new Error('Stream closed without a result');
      return result;
    }

    async cancel(requestId, reason = 'User requested cancellation') {
      return this.notify('notifications/cancelled', { requestId, reason });
    }

    async notify(method, params) {
      await this.#post([{ jsonrpc: '2.0', method, params }]);
    }

    async openNotificationsStream(onMessage) {
      // Optional background SSE stream via GET for server→client notifications
      if (this.notificationsController) this.notificationsController.abort();
      this.notificationsController = new AbortController();
      const resp = await fetch(this.endpoint, {
        method: 'GET',
        headers: { 'Accept': 'text/event-stream', ...(this.sessionId ? { 'Mcp-Session-Id': this.sessionId } : {}) },
        signal: this.notificationsController.signal,
      });
      if (!resp.ok || !resp.headers.get('content-type')?.includes('text/event-stream')) return;
      const reader = resp.body.getReader();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const events = this.#parseSSEChunk(value);
        for (const data of events) {
          try { const msg = JSON.parse(data); onMessage?.(msg); } catch {}
        }
      }
    }

    async close() {
      if (this.notificationsController) this.notificationsController.abort();
      if (!this.sessionId) return;
      await fetch(this.endpoint, { method: 'DELETE', headers: { 'Mcp-Session-Id': this.sessionId } }).catch(() => {});
      this.sessionId = null;
    }

    async #post(jsonOrArray) {
      const payload = Array.isArray(jsonOrArray) ? jsonOrArray : [jsonOrArray];
      const resp = await fetch(this.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json, text/event-stream',
          ...(this.sessionId ? { 'Mcp-Session-Id': this.sessionId } : {}),
        },
        body: JSON.stringify(payload),
      });
      const headers = resp.headers;
      if (resp.status === 404 && this.sessionId) {
        // Session expired → clear and throw so caller can re-init
        this.sessionId = null;
        throw new Error('Session expired (404). Please reconnect.');
      }
      const ctype = headers.get('content-type') || '';
      if (ctype.includes('application/json')) {
        const data = await resp.json();
        const messages = Array.isArray(data) ? data : [data];
        return { headers, messages, streamReader: null };
      } else if (ctype.includes('text/event-stream')) {
        const reader = resp.body.getReader();
        // We may receive initial events immediately; accumulate one chunk non-blocking
        const { value } = await reader.read();
        const messages = [];
        if (value) {
          const events = this.#parseSSEChunk(value);
          for (const data of events) {
            try { const msg = JSON.parse(data); messages.push(...(Array.isArray(msg) ? msg : [msg])); } catch {}
          }
        }
        return { headers, messages, streamReader: reader };
      } else if (resp.status === 202) {
        return { headers, messages: [], streamReader: null };
      } else {
        const text = await resp.text().catch(() => '');
        throw new Error('Unexpected response: ' + resp.status + ' ' + text);
      }
    }

    #parseSSEChunk(uint8) {
      const text = new TextDecoder().decode(uint8);
      // Split SSE events: events separated by double newlines; take lines starting with "data:"
      return text.split('\n\n')
        .map(block => block.split('\n').filter(l => l.startsWith('data:')).map(l => l.slice(5).trim()).join('\n'))
        .filter(Boolean);
    }

    #handleMessage(msg) { /* no-op; UI registers handlers per call */ }
  }

  // ---------- App wiring ----------
  const state = { client: null, currentCallId: null };
  const logArea = el('log');
  function logLine(kind, obj) {
    const pre = document.createElement('pre');
    pre.className = 'json-view';
    pre.textContent = `[${new Date().toLocaleTimeString()}] ${kind}:\n` + fmtJSON(obj);
    logArea.prepend(pre);
  }

  function switchTab(name) {
    for (const t of document.querySelectorAll('.tab')) t.classList.remove('active');
    document.querySelector(`.tab[data-tab="${name}"]`).classList.add('active');
    for (const pane of ['search','patterns','anomalies','snapshot']) {
      el(`tab-${pane}`)?.classList.toggle('hidden', pane !== name);
    }
  }
  document.querySelectorAll('.tab').forEach(tab => tab.addEventListener('click', () => switchTab(tab.dataset.tab)));

  // Connect / Disconnect
  el('connectBtn').addEventListener('click', async () => {
    try {
      el('connectBtn').disabled = true;
      state.client = new MCPHttpClient(el('endpoint').value.trim());
      const initRes = await state.client.initialize();
      el('serverName').textContent = `Server: ${initRes.serverInfo?.name || 'unknown'} ${initRes.serverInfo?.version ? 'v'+initRes.serverInfo.version : ''}`;
      el('sessionBadge').textContent = `Session: ${state.client.sessionId || '—'}`;
      el('proto').textContent = initRes.protocolVersion || '—';
      el('caps').textContent = Object.keys(initRes.capabilities || {}).join(', ') || '—';
      el('statusDot').classList.add('ok');
      el('statusText').textContent = 'Connected';
      el('disconnectBtn').disabled = false;
      el('appCard').hidden = false;

      // optional background notifications stream
      state.client.openNotificationsStream((msg) => {
        logLine('notify', msg);
      }).catch(() => {});

      // List tools once for sanity
      const tools = await state.client.listTools();
      logLine('tools/list', tools);
    } catch (e) {
      alert(e.message || String(e));
      el('statusDot').classList.remove('ok');
      el('statusText').textContent = 'Disconnected';
    } finally {
      el('connectBtn').disabled = false;
    }
  });

  el('disconnectBtn').addEventListener('click', async () => {
    if (!state.client) return;
    await state.client.close();
    el('disconnectBtn').disabled = true;
    el('statusDot').classList.remove('ok');
    el('statusText').textContent = 'Disconnected';
    el('appCard').hidden = true;
    el('serverName').textContent = 'Server: –';
    el('sessionBadge').textContent = 'Session: –';
  });

  // Helpers: confirmation dialog
  async function confirmArgs(toolName, args) {
    const dialog = el('confirmDialog');
    el('confirmBody').textContent = fmtJSON({ tool: toolName, arguments: args });
    dialog.showModal();
    return new Promise(resolve => {
      dialog.addEventListener('close', function handler() {
        dialog.removeEventListener('close', handler);
        resolve(dialog.returnValue === 'ok');
      });
    });
  }

  // ---- SEARCH
  el('previewSearchBtn').addEventListener('click', () => {
    const args = collectSearchArgs();
    alert(fmtJSON(args));
  });

  function collectSearchArgs() {
    const from_iso = nowISO(el('searchFrom').value);
    const to_iso = nowISO(el('searchTo').value);
    const indicesRaw = el('searchIndices').value.trim();
    return {
      query: el('searchQuery').value.trim(),
      from_iso, to_iso,
      indices: indicesRaw ? indicesRaw.split(',').map(s => s.trim()).filter(Boolean) : null,
      limit: Number(el('searchLimit').value) || 200,
      redact: el('searchRedact').checked,
    };
  }

  el('runSearchBtn').addEventListener('click', async () => {
    const args = collectSearchArgs();
    if (!args.query || !args.from_iso || !args.to_iso) return alert('Query, From, and To are required');
    if (!(await confirmArgs('search_logs', args))) return;

    const btn = el('runSearchBtn'); const cancelBtn = el('cancelSearchBtn');
    btn.disabled = true; cancelBtn.disabled = false;
    el('searchResult').innerHTML = '';

    try {
      const progressEl = document.createElement('div');
      progressEl.className = 'pill';
      progressEl.innerHTML = '<span class="status-dot"></span><span>Running…</span>';
      el('searchResult').appendChild(progressEl);

      const result = await state.client.callTool('search_logs', args, {
        onProgress: ({ progress, total, message }) => {
          progressEl.querySelector('span').textContent = `Running… ${total? Math.round((progress/total)*100): progress}% ${message? '— '+message: ''}`;
        },
        onLog: (msg) => { logLine('log', msg); },
      });

      progressEl.remove();
      el('searchResult').innerHTML = makeResultCard('Search Results', result, `<span class='badge'>limit ${args.limit}</span>`);
    } catch (e) {
      el('searchResult').innerHTML = `<div class='json-view'>Error: ${e.message || e}</div>`;
    } finally {
      btn.disabled = false; cancelBtn.disabled = true;
    }
  });

  el('cancelSearchBtn').addEventListener('click', async () => {
    if (!state.client || state.currentCallId == null) return;
    await state.client.cancel(state.currentCallId).catch(()=>{});
  });

  // ---- TOP PATTERNS
  function collectPatArgs() {
    return {
      service: el('patService').value.trim(),
      env: el('patEnv').value.trim(),
      from_iso: nowISO(el('patFrom').value),
      to_iso: nowISO(el('patTo').value),
      k: Number(el('patK').value) || 20,
    };
  }
  el('previewPatBtn').addEventListener('click', () => alert(fmtJSON(collectPatArgs())));
  el('runPatBtn').addEventListener('click', async () => {
    const args = collectPatArgs();
    if (!args.service || !args.env || !args.from_iso || !args.to_iso) return alert('All fields are required');
    if (!(await confirmArgs('top_patterns', args))) return;
    const resultEl = el('patResult'); resultEl.innerHTML = '';
    try {
      const res = await state.client.callTool('top_patterns', args);
      resultEl.innerHTML = makeResultCard('Top Patterns', res);
    } catch (e) {
      resultEl.innerHTML = `<div class='json-view'>Error: ${e.message || e}</div>`;
    }
  });

  // ---- ANOMALIES
  function collectAnoArgs() {
    return {
      service: el('anoService').value.trim(),
      env: el('anoEnv').value.trim(),
      from_iso: nowISO(el('anoFrom').value),
      to_iso: nowISO(el('anoTo').value),
    };
  }
  el('previewAnoBtn').addEventListener('click', () => alert(fmtJSON(collectAnoArgs())));
  el('runAnoBtn').addEventListener('click', async () => {
    const args = collectAnoArgs();
    if (!args.service || !args.env || !args.from_iso || !args.to_iso) return alert('All fields are required');
    if (!(await confirmArgs('show_anomalies', args))) return;
    const resultEl = el('anoResult'); resultEl.innerHTML = '';
    try {
      const res = await state.client.callTool('show_anomalies', args);
      resultEl.innerHTML = makeResultCard('Anomalies', res);
    } catch (e) {
      resultEl.innerHTML = `<div class='json-view'>Error: ${e.message || e}</div>`;
    }
  });

  // ---- CHANGE SNAPSHOT
  function collectSnapArgs() {
    return {
      service: el('snapService').value.trim(),
      env: el('snapEnv').value.trim(),
      change_id: el('snapChangeId').value.trim(),
      pre_min: Number(el('snapPre').value) || 15,
      post_min: Number(el('snapPost').value) || 30,
    };
  }
  el('previewSnapBtn').addEventListener('click', () => alert(fmtJSON(collectSnapArgs())));
  el('runSnapBtn').addEventListener('click', async () => {
    const args = collectSnapArgs();
    if (!args.service || !args.env || !args.change_id) return alert('Service, Env and Change ID are required');
    if (!(await confirmArgs('change_window_snapshot', args))) return;
    const resultEl = el('snapResult'); resultEl.innerHTML = '';
    try {
      const res = await state.client.callTool('change_window_snapshot', args);
      resultEl.innerHTML = makeResultCard('Change Snapshot', res);
    } catch (e) {
      resultEl.innerHTML = `<div class='json-view'>Error: ${e.message || e}</div>`;
    }
  });

  // Defaults: set sensible From/To (last 60 min)
  const now = new Date();
  const pad = (n) => String(n).padStart(2,'0');
  function dtLocal(d) { return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`; }
  const oneHourAgo = new Date(now.getTime() - 60*60*1000);
  el('searchFrom').value = dtLocal(oneHourAgo);
  el('searchTo').value = dtLocal(now);
  el('patFrom').value = dtLocal(oneHourAgo);
  el('patTo').value = dtLocal(now);
  el('anoFrom').value = dtLocal(oneHourAgo);
  el('anoTo').value = dtLocal(now);
  </script>
</body>
</html>
