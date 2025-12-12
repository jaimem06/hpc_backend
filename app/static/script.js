const API_URL = "/api";


document.addEventListener('DOMContentLoaded', () => {
    fetchClusterStatus();
    fetchJobs();

    // Auto refresh
    setInterval(fetchClusterStatus, 3000);
    setInterval(fetchJobs, 5000);
});

// --- UI TABS ---
function switchTab(tabId) {
    // 1. Activate Pane
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    const pane = document.getElementById(tabId);
    if (pane) pane.classList.add('active');

    // 2. Activate Button
    document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('active');
        // Auto-select the button that points to this tab
        if (b.getAttribute('onclick').includes(`'${tabId}'`)) {
            b.classList.add('active');
        }
    });
}

// --- JOBS & STATUS ---

// 1. Submit File
document.getElementById('file-input').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const msg = document.getElementById('upload-msg');

    msg.innerText = "Desplegando...";

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch(`${API_URL}/files/submit/`, { method: 'POST', body: formData });
        if (res.ok) {
            msg.innerText = "✔ Desplegado exitosamente";
            fetchJobs();
            switchTab('history');
        } else {
            const errData = await res.json().catch(() => ({}));
            msg.innerText = `Error al subir: ${errData.detail || res.statusText}`;
        }
    } catch (e) { msg.innerText = `Error conexión: ${e.message}`; }
});

// 2. Submit Math
async function submitPrimeJob() {
    const start = document.getElementById('prime-start').value;
    const end = document.getElementById('prime-end').value;
    const msg = document.getElementById('computation-msg');

    msg.innerText = "Dividiendo y asignando tareas...";

    try {
        const res = await fetch(`${API_URL}/computation/submit/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ start_range: parseInt(start), end_range: parseInt(end) })
        });
        const data = await res.json();
        if (res.ok) {
            msg.innerText = `✔ ${data.msg}`;
            fetchJobs();
            switchTab('history');
        } else {
            msg.innerText = `Error iniciado: ${data.detail || res.statusText}`;
        }
    } catch (e) { msg.innerText = `Error: ${e.message}`; }
}

// 3. Status (Worker Details)
async function fetchClusterStatus() {
    try {
        const res = await fetch('/cluster/status');
        const data = await res.json();

        document.getElementById('online-nodes').innerText = data.total_nodes || 0;

        let total = 0;
        if (data.tasks_running) total = Object.values(data.tasks_running).flat().length;
        document.getElementById('active-tasks').innerText = total;

        const cont = document.getElementById('nodes-container');
        cont.innerHTML = '';

        const activeTasksMap = data.tasks_running || {};

        if (!data.online_nodes || data.online_nodes.length === 0) {
            cont.innerHTML = '<span style="color:#666; font-size:0.8rem">No hay workers conectados.</span>';
            return;
        }

        // Render card detallada por worker
        data.online_nodes.forEach(nodeName => {
            const tasks = activeTasksMap[nodeName] || [];
            const taskCount = tasks.length;
            const statusLabel = taskCount > 0 ? "OCUPADO" : "IDLE";
            const statusColor = taskCount > 0 ? "#FFC107" : "#00C853"; // Amarillo vs Verde

            // Generar ID corto
            const shortId = nodeName.includes("@") ? nodeName.split("@")[1] : nodeName;

            const div = document.createElement('div');
            div.className = 'worker-card';
            div.innerHTML = `
                <div class="worker-info">
                    <h4>${nodeName}</h4>
                    <small>ID: ${shortId}</small>
                </div>
                <div class="worker-stats">
                     <span class="worker-badge" style="color: ${statusColor}">${statusLabel}</span>
                     <div style="font-size:0.75rem; color:#888; margin-top:2px;">Tareas: ${taskCount}</div>
                </div>
            `;
            cont.appendChild(div);
        });
    } catch (e) { }
}

// 4. History
async function fetchJobs() {
    try {
        const res = await fetch(`${API_URL}/jobs/`);
        const jobs = await res.json();
        const tbody = document.getElementById('jobs-table');
        tbody.innerHTML = '';

        jobs.forEach(j => {
            const tr = document.createElement('tr');
            let action = '';
            if (j.download_url) action = `<a href="${j.download_url}" style="color:#FFF">⬇ BAJAR</a>`;

            // Traducir estados
            let displayStatus = j.status;
            if (j.status === 'queued') displayStatus = 'EN COLA';
            if (j.status === 'completed') displayStatus = 'COMPLETADO';
            if (j.status === 'processing') displayStatus = 'PROCESANDO';
            if (j.status === 'failed') displayStatus = 'FALLIDO';

            tr.innerHTML = `
                <td>${j.filename}</td>
                <td style="font-size:0.8rem; color:#888">${j.type === 'computation' ? 'Cálculo' : 'Archivo'}</td>
                <td><span class="status-badge status-${j.status}">${displayStatus}</span></td>
                <td>${j.worker}</td>
                <td>${action}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) { }
}