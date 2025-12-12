from app.core.celery_app import celery_app

def get_workers_status():
    i = celery_app.control.inspect()
    
    # Nodos activos (ping)
    active_nodes = i.ping()
    if not active_nodes:
        return {"active": [], "disconnected": "No workers found"}

    # Lista de nodos conectados
    online_hosts = list(active_nodes.keys())
    
    # Tareas activas ejecutándose ahora mismo
    active_tasks = i.active()
    
    return {
        "online_nodes": online_hosts,
        "total_nodes": len(online_hosts),
        "tasks_running": active_tasks
    }