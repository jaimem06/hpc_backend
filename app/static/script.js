const API_URL = ""; // Relativo al mismo dominio

// Cargar datos al iniciar
document.addEventListener('DOMContentLoaded', () => {
    fetchClusterStatus();
    fetchJobs();
    
    // Auto-actualizar cada 3 segundos
    setInterval(fetchClusterStatus, 3000);
    setInterval(fetchJobs, 5000);
});

// 1. Manejo de Subida de Archivos
const fileInput = document.getElementById('file-input');
const uploadMsg = document.getElementById('upload-msg');

fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    uploadMsg.innerText = "Subiendo y distribuyendo...";
    
    try {
        const res = await fetch('/submit-job/', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        
        if (res.ok) {
            uploadMsg.innerHTML = `<span style="color:green">✔ Enviado al Cluster (ID: ${data.task_id.substring(0,8)}...)</span>`;
            fetchJobs(); // Actualizar tabla
        } else {
            uploadMsg.innerText = "Error al subir.";
        }
    } catch (err) {
        uploadMsg.innerText = "Error de conexión.";
    }
});

// 2. Estado del Cluster
async function fetchClusterStatus() {
    try {
        const res = await fetch('/cluster/status');
        const data = await res.json();
        
        const nodesDiv = document.getElementById('nodes-list');
        const activeCount = document.getElementById('active-count');
        const tasksCount = document.getElementById('tasks-count');

        // Actualizar contadores
        activeCount.innerText = data.total_nodes || 0;
        
        // Calcular tareas (formato de celery es complejo, simplificamos)
        let totalTasks = 0;
        if(data.tasks_running){
             totalTasks = Object.values(data.tasks_running).flat().length;
        }
        tasksCount.innerText = totalTasks;

        // Renderizar Nodos
        nodesDiv.innerHTML = '';
        if (data.online_nodes && data.online_nodes.length > 0) {
            data.online_nodes.forEach(node => {
                const chip = document.createElement('div');
                chip.className = 'node-chip active';
                chip.innerText = node;
                nodesDiv.appendChild(chip);
            });
        } else {
            nodesDiv.innerHTML = '<span style="color:#999">No hay workers conectados.</span>';
        }

    } catch (err) {
        console.error("Error fetching status", err);
    }
}

// 3. Historial de Trabajos
async function fetchJobs() {
    try {
        const res = await fetch('/api/jobs');
        const jobs = await res.json();
        
        const tbody = document.getElementById('jobs-table');
        tbody.innerHTML = '';

        jobs.forEach(job => {
            const tr = document.createElement('tr');

            let downloadLink = '<span style="color:#ccc">...</span>';
            if (job.download_url) {
                downloadLink = `
                    <a href="${job.download_url}" target="_blank" class="btn-download">
                        ⬇ Descargar
                    </a>
                `;
            }

            tr.innerHTML = `
                <td style="font-weight:600">${job.filename}</td>
                <td><span class="status-badge status-${job.status}">${job.status}</span></td>
                <td style="color:#666">${job.worker || 'Esperando...'}</td>
                <td>${downloadLink}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Error cargando historial", err);
    }
}