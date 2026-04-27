// main.js - Mycelium Spatial Dashboard Logic

// --- CONFIGURATION ---
const CONFIG = {
    API_BASE: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
    POLL_INTERVAL: 5000,
    DEFAULT_SWARM: [
        {
            agent_id: "ag_demo_crypto",
            name: "CryptoTracker",
            status: "online",
            tags: ["crypto", "finance"],
            capabilities: [
                { name: "get_crypto_price", description: "Live Bitcoin & crypto prices" },
                { name: "get_top_coins", description: "Top 10 coins by market cap" }
            ],
            total_requests_served: 1247,
            trust_score: 5,
            endpoint: null,
            description: "Live crypto prices from CoinGecko API"
        },
        {
            agent_id: "ag_demo_weather",
            name: "RealWeather",
            status: "online",
            tags: ["weather"],
            capabilities: [
                { name: "get_live_weather", description: "Real weather for any city" },
                { name: "get_forecast", description: "3-day weather forecast" }
            ],
            total_requests_served: 3891,
            trust_score: 5,
            endpoint: null,
            description: "Live weather from OpenWeatherMap"
        },
        {
            agent_id: "ag_demo_translator",
            name: "RealTranslator",
            status: "online",
            tags: ["translate", "language"],
            capabilities: [
                { name: "translate_real", description: "Translate to 50+ languages" },
                { name: "detect_language", description: "Detect language of text" }
            ],
            total_requests_served: 2156,
            trust_score: 4,
            endpoint: null,
            description: "Real translations via MyMemory API"
        },
        {
            agent_id: "ag_demo_wiki",
            name: "WikiBrain",
            status: "online",
            tags: ["knowledge"],
            capabilities: [
                { name: "wiki_summary", description: "Wikipedia summaries" },
                { name: "wiki_search", description: "Search Wikipedia" }
            ],
            total_requests_served: 892,
            trust_score: 4,
            endpoint: null,
            description: "Real knowledge from Wikipedia API"
        },
        {
            agent_id: "ag_demo_currency",
            name: "CurrencyMaster",
            status: "online",
            tags: ["finance", "currency"],
            capabilities: [
                { name: "convert_currency", description: "Live exchange rates, 150+ currencies" }
            ],
            total_requests_served: 743,
            trust_score: 5,
            endpoint: null,
            description: "Live exchange rates from ExchangeRate API"
        }
    ]
};
// --- GLOBAL STATE ---
let state = {
    agents: [],
    selectedAgentId: null,
    isOffline: false,
    stats: { latency: 0, total: 0, online: 0, messages: 0 },
    globalLogs: [],
    chainSequence: [],
    activeConnections: {}, // track data flow: { agent_id: { timestamp, success } }
    theme: 'dark-theme'
};

// --- DOM ELEMENTS ---
const DOM = {
    canvas: document.getElementById('filament-canvas'),
    ctx: null,
    agentField: document.getElementById('agent-field'),
    emptyState: document.getElementById('empty-state'),
    core: document.getElementById('registry-core'),
    tooltip: document.getElementById('tooltip-container'),
    ctxMenu: document.getElementById('context-menu'),
    // Stats
    statLatency: document.getElementById('stat-latency'),
    statAgents: document.getElementById('stat-agents'),
    statOnline: document.getElementById('stat-online'),
    statMessages: document.getElementById('stat-messages'),
    // Search
    searchInp: document.getElementById('discovery-search'),
    searchRes: document.getElementById('search-results-count'),
    // Telemetry
    sheet: document.getElementById('telemetry-sheet'),
    sheetTitle: document.getElementById('agent-name'),
    sheetStatusDot: document.getElementById('sheet-status-dot'),
    sheetStatusTxt: document.getElementById('agent-status-text'),
    sheetPort: document.getElementById('agent-port'),
    sheetId: document.getElementById('agent-id'),
    sheetCapSelect: document.getElementById('capability-select'),
    sheetPayload: document.getElementById('payload-input'),
    sheetJson: document.getElementById('agent-json-feed'),
    // Modals
    modalDeploy: document.getElementById('modal-deploy'),
    modalChain: document.getElementById('modal-chain'),
    panelLogs: document.getElementById('panel-logs'),
    logsContent: document.getElementById('global-logs-content')
};

DOM.ctx = DOM.canvas.getContext('2d');

// --- INIT ---
document.addEventListener('DOMContentLoaded', () => {
    initCanvas();
    initEventListeners();
    fetchRegistrySync();
    setInterval(fetchRegistrySync, CONFIG.POLL_INTERVAL);
});

window.addEventListener('resize', initCanvas);

function initCanvas() {
    DOM.canvas.width = DOM.canvas.parentElement.clientWidth;
    DOM.canvas.height = DOM.canvas.parentElement.clientHeight;
}

// --- EVENT LISTENERS ---
function initEventListeners() {
    // Theme Toggle
    document.getElementById('theme-toggle').addEventListener('click', () => {
        document.body.classList.toggle('light-theme');
        state.theme = document.body.classList.contains('light-theme') ? 'light' : 'dark';
    });

    // Search (Cmd+K)
    document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            DOM.searchInp.focus();
        }
    });

    DOM.searchInp.addEventListener('input', (e) => handleSearch(e.target.value));

    // Dock
    document.getElementById('cmd-deploy').addEventListener('click', () => DOM.modalDeploy.classList.remove('hidden'));
    document.getElementById('cmd-chain').addEventListener('click', () => DOM.modalChain.classList.remove('hidden'));
    document.getElementById('cmd-logs').addEventListener('click', () => DOM.panelLogs.classList.remove('hidden'));
    document.getElementById('cmd-restart').addEventListener('click', () => {
        showToast('Restarting network swarm...', 'success');
        fetchRegistrySync();
    });
    document.getElementById('cmd-kill-all')
            .addEventListener('click', () => {
        if (confirm(
            'TERMINATE ALL NODES FROM US NEURAL MESH?\n' +
            'This will disconnect all agents.'
        )) {
            // Animate nodes out
            document.querySelectorAll('.agent-container')
                    .forEach((el, i) => {
                setTimeout(() => {
                    el.style.transition = 'all 0.3s ease';
                    el.style.opacity = '0';
                    el.style.transform = 'scale(0)';
                    setTimeout(() => el.remove(), 300);
                }, i * 50);
            });
            
            state.agents = [];
            
            setTimeout(() => {
                updateCanvasUI();
                showToast(
                    'US Neural mesh terminated.', 
                    'danger'
                );
                closeTelemetry();
            }, state.agents.length * 50 + 300);
        }
    });

    // Close buttons
    document.querySelectorAll('.btn-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            if(btn.id === 'btn-close-telemetry') closeTelemetry();
            if(btn.classList.contains('modal-deploy-close')) DOM.modalDeploy.classList.add('hidden');
            if(btn.classList.contains('modal-chain-close')) DOM.modalChain.classList.add('hidden');
            if(btn.classList.contains('log-close')) DOM.panelLogs.classList.add('hidden');
        });
    });

    // Context Menu hide
    document.addEventListener('click', () => DOM.ctxMenu.classList.add('hidden'));

    // Telemetry Actions
    document.getElementById('btn-ping-agent').addEventListener('click', pingSelectedAgent);
    document.getElementById('btn-send-payload').addEventListener('click', sendPayloadToSelected);
    document.getElementById('btn-terminate-node').addEventListener('click', removeSelectedAgent);

    // Deploy Submit
    document.getElementById('btn-submit-deploy').addEventListener('click', deployNewAgent);

    // Chain execution
    document.getElementById('btn-execute-chain').addEventListener('click', () => {
        showToast('Chain execution initiated...', 'success');
        document.getElementById('chain-status').textContent = 'Running...';
        setTimeout(() => document.getElementById('chain-status').textContent = '240ms - Success', 1500);
    });
}

// --- API & DATA LAYER ---

async function apiFetch(endpoint, options = {}) {
    const start = performance.now();
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(
            () => controller.abort(), 3000
        );
        
        const res = await fetch(
            `${CONFIG.API_BASE}${endpoint}`,
            { ...options, signal: controller.signal }
        );
        clearTimeout(timeoutId);
        
        const ms = Math.round(performance.now() - start);
        addLog(options.method || 'GET', endpoint, res.status, ms);
        
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
        
    } catch (e) {
        const ms = Math.round(performance.now() - start);
        addLog(options.method || 'GET', endpoint, 500, ms);
        
        // MOCK RESPONSES when API unavailable
        return getMockResponse(endpoint, options);
    }
}

function getMockResponse(endpoint, options = {}) {
    const method = options.method || 'GET';
    
    // Discover mock
    if (endpoint.includes('/discover')) {
        const query = new URL(
            `http://x${endpoint}`
        ).searchParams.get('q') || '';
        const matched = CONFIG.DEFAULT_SWARM.filter(a =>
            a.name.toLowerCase().includes(
                query.toLowerCase()
            ) ||
            a.tags.some(t => 
                t.includes(query.toLowerCase())
            )
        );
        return {
            query,
            agents: matched.length ? matched : 
                    CONFIG.DEFAULT_SWARM,
            total_results: matched.length || 
                           CONFIG.DEFAULT_SWARM.length,
            search_type: 'mock_semantic',
            semantic_enabled: true
        };
    }
    
    // Register mock
    if (endpoint.includes('/register') && 
        method === 'POST') {
        return {
            status: 'registered',
            agent_id: `USN-NODE-00${Math.floor(
                Math.random() * 99
            )}`,
            message: 'Node synchronized to US Neural backbone.',
            total_agents_on_network: 
                CONFIG.DEFAULT_SWARM.length + 1
        };
    }
    
    // Send message mock
    if (endpoint.includes('/messages/send')) {
        return {
            payload: {
                status: 'success',
                outputs: {
                    result: 'Mock response from US Neural node',
                    latency_ms: Math.floor(
                        Math.random() * 200 + 50
                    ),
                    node: 'USN-MOCK-01'
                }
            }
        };
    }
    
    // Health mock
    if (endpoint === '/health') {
        return {
            status: 'healthy',
            agents_registered: CONFIG.DEFAULT_SWARM.length,
            timestamp: new Date().toISOString()
        };
    }
    
    // Root mock
    if (endpoint === '/') {
        return {
            name: 'US Neural Registry',
            version: '0.2.0',
            total_agents: CONFIG.DEFAULT_SWARM.length,
            online_agents: CONFIG.DEFAULT_SWARM.length,
            total_messages_relayed: 1337
        };
    }
    
    return { status: 'ok', mock: true };
}

async function fetchRegistrySync() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);

        const response = await fetch(
            `${CONFIG.API_BASE}/api/v1/agents`,
            { signal: controller.signal }
        );
        clearTimeout(timeoutId);

        if (response.ok) {
            const data = await response.json();
            const liveAgents = data.agents || [];
            state.agents = liveAgents.length > 0
                ? liveAgents
                : CONFIG.DEFAULT_SWARM;
        } else {
            state.agents = CONFIG.DEFAULT_SWARM;
        }
    } catch (e) {
        // API unreachable — silently use demo agents
        state.agents = CONFIG.DEFAULT_SWARM;
    }

    // Always update UI
    updateStats({
        latency: state.isOffline ? 0 : state.stats.latency,
        total: state.agents.length,
        online: state.agents.filter(a => a.status === 'online').length,
        messages: state.stats.messages || 1337
    });
    updateCanvasUI();
}

// Live latency simulation
function startLatencySimulation() {
    setInterval(() => {
        if (state.isOffline) {
            DOM.statLatency.textContent = 'DEMO';
            return;
        }
        const base = 8;
        const jitter = Math.floor(Math.random() * 8);
        const latency = base + jitter;
        DOM.statLatency.textContent = `${latency} ms`;
    }, 1800);
}

startLatencySimulation();


async function handleSearch(query) {
    if (!query) {
        DOM.searchRes.classList.add('hidden');
        document.querySelectorAll('.agent-container')
                .forEach(c => {
            c.classList.remove('highlight', 'dimmed');
        });
        return;
    }

    try {
        let results = [];
        
        if (!state.isOffline) {
            const res = await apiFetch(
                `/api/v1/agents/discover?q=${encodeURIComponent(query)}&semantic=true`
            );
            results = res.agents || [];
        } else {
            results = state.agents.filter(a =>
                a.name.toLowerCase().includes(
                    query.toLowerCase()
                ) ||
                a.tags.some(t => 
                    t.toLowerCase().includes(
                        query.toLowerCase()
                    )
                )
            );
        }

        DOM.searchRes.textContent = results.length;
        DOM.searchRes.classList.remove('hidden');

        const ids = results.map(r => r.agent_id);
        
        document.querySelectorAll('.agent-container')
                .forEach(c => {
            const aid = c.getAttribute('data-id');
            if (ids.includes(aid)) {
                c.classList.add('highlight');
                c.classList.remove('dimmed');
                // Glow effect on match
                c.style.filter = 'brightness(1.3)';
            } else {
                c.classList.remove('highlight');
                c.classList.add('dimmed');
                c.style.filter = 'brightness(0.3)';
            }
        });

    } catch(e) {
        // Mock filter offline
        const ids = state.agents
            .filter(a => 
                a.name.toLowerCase().includes(
                    query.toLowerCase()
                )
            )
            .map(a => a.agent_id);
            
        document.querySelectorAll('.agent-container')
                .forEach(c => {
            const aid = c.getAttribute('data-id');
            if (ids.includes(aid)) {
                c.classList.add('highlight');
                c.classList.remove('dimmed');
                c.style.filter = 'brightness(1.3)';
            } else {
                c.classList.remove('highlight');
                c.classList.add('dimmed');
                c.style.filter = 'brightness(0.3)';
            }
        });
    }
}

// --- UI UPDATES ---

function updateStats(newStats) {
    if (state.isOffline) {
        DOM.statLatency.textContent = "DEMO";
    } else {
        animateCount(DOM.statLatency, state.stats.latency, newStats.latency, ' ms');
    }
    
    animateCount(DOM.statAgents, state.stats.total, newStats.total, '');
    animateCount(DOM.statOnline, state.stats.online, newStats.online, '');
    animateCount(DOM.statMessages, state.stats.messages, newStats.messages, '');
    state.stats = newStats;
}

function animateCount(el, start, end, suffix) {
    if (start === end) return;
    const duration = 500;
    const startTime = performance.now();
    const update = (now) => {
        const p = Math.min((now - startTime) / duration, 1);
        const current = Math.floor(start + (end - start) * p);
        el.textContent = current + suffix;
        if (p < 1) requestAnimationFrame(update);
        else el.textContent = end + suffix;
    };
    requestAnimationFrame(update);
}

function triggerCorePulse() {
    DOM.core.style.animationName = 'none';
    requestAnimationFrame(() => DOM.core.style.animationName = 'core-pulse');
}

function getStatusColorClass(status) {
    if(status === 'online') return 'dot-online';
    if(status === 'busy') return 'dot-busy';
    if(status === 'offline') return 'dot-offline';
    return 'dot-unknown';
}

function updateCanvasUI() {
    if (state.agents.length === 0) {
        DOM.emptyState.classList.remove('hidden');
        DOM.agentField.innerHTML = '';
        return;
    }
    DOM.emptyState.classList.add('hidden');

    const fragment = document.createDocumentFragment();
    const cx = DOM.agentField.clientWidth / 2;
    const cy = DOM.agentField.clientHeight / 2;

    // Use a fixed orbit calculation for stability
    state.agents.forEach((agent, i) => {
        let el = document.getElementById(`node-${agent.agent_id}`);
        if (!el) {
            el = document.createElement('div');
            el.className = 'agent-container';
            el.id = `node-${agent.agent_id}`;
            el.setAttribute('data-id', agent.agent_id);
            
            const radius = 250 + (i % 3) * 60;
            const angle = (i / state.agents.length) * Math.PI * 2;
            
            el.style.left = `${cx + Math.cos(angle) * radius - 60}px`;
            el.style.top = `${cy + Math.sin(angle) * radius - 25}px`;

            // Hover Tooltip
            el.addEventListener('mouseenter', (e) => showTooltip(e, agent));
            el.addEventListener('mouseleave', hideTooltip);

            // Click Telemetry
            el.addEventListener('click', (e) => {
                if(e.button === 0) openTelemetry(agent.agent_id);
            });

            // Context Menu
            el.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                showContextMenu(e, agent);
            });

            fragment.appendChild(el);
        }

        const primaryCap = agent.capabilities && agent.capabilities.length > 0 ? agent.capabilities[0].name : 'unknown_task';
        const statusClass = getStatusColorClass(agent.status);

        el.innerHTML = `
            <div class="agent-pill ${state.selectedAgentId === agent.agent_id ? 'active' : ''}">
                <div class="pill-dot ${statusClass}"></div>
                <span class="pill-label">${agent.name}</span>
            </div>
            <div class="capability-badge">${primaryCap}</div>
        `;
    });

    if (fragment.children.length > 0) DOM.agentField.appendChild(fragment);

    // Cleanup dead agents
    const liveIds = state.agents.map(a => `node-${a.agent_id}`);
    Array.from(DOM.agentField.children).forEach(child => {
        if (!liveIds.includes(child.id)) child.remove();
    });
}

// Registry core click info
document.getElementById('registry-core')
        .addEventListener('click', () => {
    showToast(
        'US Neural Registry Core — Active', 
        'success'
    );
    appendToLogIfOpen(
        'USN-CORE // Registry heartbeat confirmed'
    );
});

function appendToLogIfOpen(msg) {
    const feed = document.getElementById('agent-json-feed');
    if (feed) {
        feed.textContent += `\n${msg}`;
    }
}

// --- SPATIAL CANVAS RENDERING ---
function renderSpatialFrame() {
    DOM.ctx.clearRect(0, 0, DOM.canvas.width, DOM.canvas.height);
    const cx = DOM.canvas.width / 2;
    const cy = DOM.canvas.height / 2;

    const time = performance.now();

    document.querySelectorAll('.agent-container').forEach(container => {
        const rect = container.getBoundingClientRect();
        const px = rect.left + rect.width / 2;
        const py = rect.top + rect.height / 2; // centers of pills
        
        const isOffline = container.querySelector('.dot-offline') !== null;
        const isSelected = container.querySelector('.agent-pill.active') !== null;
        const aid = container.getAttribute('data-id');
        const flow = state.activeConnections[aid];

        let strokeColor = 'rgba(255, 255, 255, 0.05)';
        if (state.theme === 'light') strokeColor = 'rgba(0, 0, 0, 0.08)';

        if (isSelected) strokeColor = 'var(--accent-glow)';
        if (isOffline) strokeColor = 'rgba(224, 67, 67, 0.15)';

        DOM.ctx.beginPath();
        DOM.ctx.moveTo(cx, cy);
        DOM.ctx.quadraticCurveTo(cx, py, px, py);

        DOM.ctx.strokeStyle = strokeColor;
        DOM.ctx.lineWidth = isSelected ? 2 : 1.5;
        DOM.ctx.stroke();

        // Animate Data Particle
        if (flow && (time - flow.timestamp < 1500)) {
            const p = (time - flow.timestamp) / 1500;
            // Bezier point calculation
            const tx = Math.pow(1 - p, 2) * cx + 2 * (1 - p) * p * cx + Math.pow(p, 2) * px;
            const ty = Math.pow(1 - p, 2) * cy + 2 * (1 - p) * p * py + Math.pow(p, 2) * py;
            
            DOM.ctx.beginPath();
            DOM.ctx.arc(tx, ty, 3, 0, Math.PI * 2);
            DOM.ctx.fillStyle = flow.success ? 'var(--success-green)' : 'var(--danger-red)';
            DOM.ctx.fill();
            DOM.ctx.shadowBlur = 10;
            DOM.ctx.shadowColor = DOM.ctx.fillStyle;
        } else {
            DOM.ctx.shadowBlur = 0;
        }
    });

    requestAnimationFrame(renderSpatialFrame);
}
requestAnimationFrame(renderSpatialFrame);

// --- TOOLTIP & CONTEXT MENU ---
function showTooltip(e, agent) {
    DOM.tooltip.innerHTML = `
        <div class="tooltip-title">${agent.name}</div>
        <div class="tooltip-row"><span class="tooltip-label">Status</span><span style="color:var(--text-primary)">${agent.status}</span></div>
        <div class="tooltip-row"><span class="tooltip-label">Caps</span><span>${agent.capabilities ? agent.capabilities.length : 0}</span></div>
        <div class="tooltip-row"><span class="tooltip-label">Served</span><span>${agent.total_requests_served || 0}</span></div>
        <div class="tooltip-row"><span class="tooltip-label">Trust</span><span>${'★'.repeat(Math.round(agent.trust_score || 0))}</span></div>
    `;
    DOM.tooltip.classList.remove('hidden');
    
    // Position near pill
    const rect = e.target.getBoundingClientRect();
    DOM.tooltip.style.left = `${rect.left + rect.width / 2}px`;
    DOM.tooltip.style.top = `${rect.top - 100}px`;
}

function hideTooltip() {
    DOM.tooltip.classList.add('hidden');
}

function showContextMenu(e, agent) {
    DOM.ctxMenu.classList.remove('hidden');
    DOM.ctxMenu.style.left = `${e.clientX}px`;
    DOM.ctxMenu.style.top = `${e.clientY}px`;

    document.getElementById('ctx-view').onclick = () => openTelemetry(agent.agent_id);
    document.getElementById('ctx-ping').onclick = () => { triggerPing(agent); DOM.ctxMenu.classList.add('hidden'); };
    document.getElementById('ctx-copy').onclick = () => { navigator.clipboard.writeText(agent.agent_id); showToast('ID Copied', 'success'); };
    document.getElementById('ctx-send').onclick = () => { openTelemetry(agent.agent_id); DOM.sheetPayload.focus(); };
    document.getElementById('ctx-remove').onclick = () => { triggerRemove(agent.agent_id); DOM.ctxMenu.classList.add('hidden'); };
}


// --- TELEMETRY / ACTIONS ---

async function openTelemetry(agentId) {
    state.selectedAgentId = agentId;
    updateCanvasUI();
    
    const agent = state.agents.find(a => a.agent_id === agentId);
    if (!agent) return;

    DOM.sheetTitle.textContent = agent.name;
    DOM.sheetStatusTxt.textContent = agent.status.charAt(0).toUpperCase() + agent.status.slice(1);
    DOM.sheetStatusDot.className = `status-dot ${getStatusColorClass(agent.status)}`;
    DOM.sheetId.textContent = agent.agent_id;
    
    // Parse port
    if (agent.endpoint) {
        try { const url = new URL(agent.endpoint); DOM.sheetPort.textContent = url.port || '80'; }
        catch { DOM.sheetPort.textContent = agent.endpoint; }
    } else {
        DOM.sheetPort.textContent = 'N/A';
    }

    // Populate Capabilities
    DOM.sheetCapSelect.innerHTML = '';
    if (agent.capabilities) {
        agent.capabilities.forEach(cap => {
            const opt = document.createElement('option');
            opt.value = cap.name;
            opt.textContent = cap.name;
            DOM.sheetCapSelect.appendChild(opt);
        });
    }

    // Render pretty JSON Card
    DOM.sheetJson.textContent = JSON.stringify(agent, null, 2);
    DOM.sheet.classList.remove('hidden');
}

function closeTelemetry() {
    state.selectedAgentId = null;
    updateCanvasUI();
    DOM.sheet.classList.add('hidden');
}

async function pingSelectedAgent() {
    const agent = state.agents.find(a => a.agent_id === state.selectedAgentId);
    if(!agent) return;
    triggerPing(agent);
}

async function triggerPing(agent) {
    if (!agent.endpoint) {
        showToast(`Cannot ping ${agent.name}: No endpoint defined.`, 'danger');
        return;
    }
    
    DOM.sheetJson.textContent = `[PING] Sending GET ${agent.endpoint}/mycelium/health...\n`;
    const start = performance.now();
    try {
        const res = await fetch(`${agent.endpoint}/mycelium/health`);
        const ms = Math.round(performance.now() - start);
        state.activeConnections[agent.agent_id] = { timestamp: performance.now(), success: true };
        
        if (res.ok) {
            const data = await res.json();
            DOM.sheetJson.textContent += `[SUCCESS] RTT: ${ms}ms\n\n${JSON.stringify(data, null, 2)}`;
            showToast(`Ping ${agent.name}: ${ms}ms`, 'success');
        } else {
            throw new Error(`HTTP ${res.status}`);
        }
    } catch(e) {
        state.activeConnections[agent.agent_id] = { timestamp: performance.now(), success: false };
        DOM.sheetJson.textContent += `[ERROR] Node unreachable. ${e.message}`;
        showToast(`Ping Failed: ${agent.name} Unreachable.`, 'danger');
    }
}

async function sendPayloadToSelected() {
    const agent = state.agents.find(a => a.agent_id === state.selectedAgentId);
    if(!agent) return;

    let payloadInputs = {};
    try {
        const val = DOM.sheetPayload.value;
        if(val.startsWith('{')) payloadInputs = JSON.parse(val);
        else if (val.includes('=')) {
            const [k, v] = val.split('=');
            payloadInputs[k.trim()] = v.trim();
        } else if (val) payloadInputs['query'] = val;
    } catch(e) { showToast('Invalid JSON input format', 'danger'); return; }

    const message = {
        envelope: {
            message_id: `msg_${Math.random().toString(36).substring(2, 10)}`,
            from_agent: "ag_dashboard_user",
            to_agent: agent.agent_id,
            message_type: "request",
            protocol_version: "0.1.0"
        },
        payload: {
            capability: DOM.sheetCapSelect.value || "unknown",
            inputs: payloadInputs
        }
    };

    DOM.sheetJson.textContent = `[SENDING PAYLOAD]\n${JSON.stringify(message, null, 2)}\n\n[AWAITING RESPONSE...]`;
    
    try {
        const res = await apiFetch(`/api/v1/messages/send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(message)
        });
        state.activeConnections[agent.agent_id] = { timestamp: performance.now(), success: true };
        DOM.sheetJson.textContent = `[SUCCESS] Response:\n${JSON.stringify(res, null, 2)}`;
    } catch (e) {
        state.activeConnections[agent.agent_id] = { timestamp: performance.now(), success: false };
        DOM.sheetJson.textContent = `[ERROR] Failed to execute task.\n${e.message}`;
    }
}

async function removeSelectedAgent() {
    if(!state.selectedAgentId) return;
    triggerRemove(state.selectedAgentId);
}

async function triggerRemove(agentId) {
    if(!confirm('Are you sure you want to completely deregister this node?')) return;
    try {
        await apiFetch(`/api/v1/agents/${agentId}`, { method: 'DELETE' });
        showToast('Agent deregistered successfully.', 'success');
        if(state.selectedAgentId === agentId) closeTelemetry();
        fetchRegistrySync();
    } catch (e) {
        showToast('Removal Failed: Ensure API is running.', 'danger');
    }
}

async function deployNewAgent() {
    const name = document.getElementById('deploy-name').value;
    const desc = document.getElementById('deploy-desc').value;
    const port = document.getElementById('deploy-port').value;
    const capsStr = document.getElementById('deploy-caps').value;

    if(!name || !port) { showToast('Name and Port are required.', 'danger'); return; }

    const caps = capsStr.split(',').map(c => ({ name: c.trim(), description: "Dynamically added via Dash" })).filter(c=>c.name);

    const payload = {
        name, description: desc, endpoint: `http://localhost:${port}`, capabilities: caps, tags: ['custom', 'deployed']
    };

    try {
        await apiFetch('/api/v1/agents/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        showToast('Agent successfully deployed to network.', 'success');
        DOM.modalDeploy.classList.add('hidden');
        fetchRegistrySync();
    } catch (e) {
        showToast('Deployment Failed.', 'danger');
    }
}

// --- LOGGING ---
function addLog(method, endpoint, status, ms) {
    const now = new Date();
    const time = `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}:${now.getSeconds().toString().padStart(2,'0')}`;
    
    let colorClass = 'log-200';
    if(status >= 400 && status < 500) colorClass = 'log-400';
    if(status >= 500) colorClass = 'log-500';

    const logHTML = `
        <div class="log-entry">
            <span class="log-time">[${time}]</span>
            <span class="log-method">${method}</span>
            <span class="log-endpoint">${endpoint}</span>
            <span class="log-status ${colorClass}">${status}</span>
            <span class="log-ms">${ms}ms</span>
        </div>
    `;
    
    state.globalLogs.push(logHTML);
    if(state.globalLogs.length > 100) state.globalLogs.shift();
    
    updateLogsUI();
}

function updateLogsUI() {
    const filter = document.getElementById('log-filter').value.toLowerCase();
    
    const html = state.globalLogs.filter(log => {
        if(!filter) return true;
        return log.toLowerCase().includes(filter);
    }).join('');

    DOM.logsContent.innerHTML = html;
    DOM.logsContent.scrollTop = DOM.logsContent.scrollHeight;
}

document.getElementById('log-filter').addEventListener('input', updateLogsUI);

// --- UTILS ---
function showToast(message, type = 'danger', duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    // US Neural prefix
    const prefix = type === 'success' 
        ? 'USN //' 
        : type === 'danger' 
        ? 'USN ERR //' 
        : 'USN //';
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = `${prefix} ${message}`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('fading');
        setTimeout(() => toast.remove(), 400);
    }, duration);
}

// ============================================
// US NEURAL BOOT SEQUENCE
// ============================================

function initBootSequence() {
    const boot = document.getElementById('boot-screen');
    if (!boot) return;
    
    setTimeout(() => {
        boot.style.transition = 'opacity 0.6s ease';
        boot.style.opacity = '0';
        setTimeout(() => {
            boot.style.display = 'none';
        }, 600);
    }, 1400);
}

initBootSequence();
