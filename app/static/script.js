const API_URL = "/api";

document.addEventListener('DOMContentLoaded', () => {
    // Poll basic worker usage
    setInterval(fetchClusterStatus, 5000);
    fetchClusterStatus();
});

// --- CLUSTER STATUS ---
async function fetchClusterStatus() {
    try {
        const res = await fetch('/cluster/status');
        const data = await res.json();
        const total = data.online_nodes ? data.online_nodes.length : 0;
        document.getElementById('online-nodes').innerText = total;
    } catch (e) { }
}

// --- FILE UPLOAD LOGIC ---
document.getElementById('file-input').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Show Preview
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('input-preview').src = e.target.result;
        document.getElementById('input-info').innerText = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;

        // Show Process UI
        document.getElementById('process-card').style.display = 'block';
        document.getElementById('upload-card').style.display = 'none';

        // Start Process
        startDistributedJob(file);
    };
    reader.readAsDataURL(file);
});


async function startDistributedJob(file) {
    const chunks = document.getElementById('chunk-select').value;
    const statusText = document.getElementById('cluster-status-text');
    const workersGrid = document.getElementById('workers-grid');

    statusText.innerText = `Subiendo y dividiendo en ${chunks} partes...`;
    statusText.style.color = '#FFF';

    workersGrid.innerHTML = '';

    // Create initial placeholders
    for (let i = 0; i < chunks; i++) {
        const div = document.createElement('div');
        div.className = 'worker-node';
        div.id = `chunk-node-${i}`;
        div.innerText = `Chunk ${i}: Pendiente`;
        div.style.background = '#333';
        workersGrid.appendChild(div);
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        // 1. Submit Job
        const res = await fetch(`${API_URL}/computation/process-image?chunks=${chunks}`, {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error("Error subiendo imagen");

        const data = await res.json();
        const jobId = data.job_id;

        statusText.innerText = "Distribuido. Procesando en GPU...";
        statusText.style.color = '#FFC107'; // Warning color (Yellow)

        // 2. Poll Status
        pollJobStatus(jobId);

    } catch (e) {
        statusText.innerText = `Error: ${e.message}`;
        statusText.style.color = 'red';
    }
}

async function pollJobStatus(jobId) {
    const interval = setInterval(async () => {
        try {
            const res = await fetch(`${API_URL}/computation/job/${jobId}`);
            const job = await res.json();

            if (job.status === 'completed') {
                clearInterval(interval);
                renderResults(job);
            } else if (job.status === 'failed') {
                clearInterval(interval);
                alert("Job Failed!");
            } else {
                // Update Progress (fake visual)
                document.getElementById('cluster-status-text').innerText = `Procesando... ${job.progress || 0}%`;
            }

        } catch (e) {
            console.error(e);
        }
    }, 1000);
}

function renderResults(job) {
    // Status Text
    const statusText = document.getElementById('cluster-status-text');
    statusText.innerText = "¡Completado!";
    statusText.style.color = '#00C853'; // Success Green

    // Render Output Image
    const outImg = document.getElementById('output-preview');
    // Si viene como base64 string directo
    outImg.src = `data:image/png;base64,${job.result_b64}`;
    outImg.style.display = 'block';

    // Stats
    document.getElementById('stat-gpu').innerText = job.stats.total_gpu_time.toFixed(4) + "s";
    document.getElementById('stat-workers').innerText = job.stats.workers.length;
    document.getElementById('stat-status').innerText = "DONE";

    // Details Table
    const tbody = document.getElementById('chunk-details-body');
    tbody.innerHTML = '';

    const workersGrid = document.getElementById('workers-grid');
    workersGrid.innerHTML = ''; // Rebuild with final info

    job.chunks_data.forEach(chunk => {
        // Table Row
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${chunk.index}</td>
            <td>${chunk.worker}</td>
            <td style="color:#00C853">${chunk.gpu_time.toFixed(4)}s</td>
            <td>${chunk.device}</td>
        `;
        tbody.appendChild(tr);

        // Grid Box
        const div = document.createElement('div');
        div.className = 'worker-node';
        div.style.border = '1px solid #00C853';
        div.innerHTML = `
            <div style="color:#fff">Chunk ${chunk.index}</div>
            <div style="font-size:0.6rem; color:#aaa">${chunk.worker}</div>
            <div style="font-size:0.6rem; color:#00C853">GPU: ${chunk.gpu_time.toFixed(3)}s</div>
        `;
        workersGrid.appendChild(div);
    });
}