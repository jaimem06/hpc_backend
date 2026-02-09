from fastapi import APIRouter, File, UploadFile
from typing import List, Dict, Any
from app.worker.gpu_tasks import process_image_chunk
from app.services.image_processor import ImageProcessor
from celery import group
from celery.result import GroupResult, AsyncResult
from app.core.celery_app import celery_app
import uuid
import base64
import time
import asyncio
from starlette.concurrency import run_in_threadpool

router = APIRouter()

# Almacenamiento temporal de jobs en memoria (para demo)
# En prod usar Redis/Mongo
JOBS = {}

@router.post("/process-image")
async def process_image(file: UploadFile = File(...), chunks: int = 2):
    """
    Sube una imagen, la divide en N chunks y distribuye a workers.
    """
    content = await file.read()
    
    # 1. Dividir imagen
    parts = ImageProcessor.split_image(content, chunks=chunks)
    
    # 2. Crear grupo de tareas Celery
    job_id = str(uuid.uuid4())
    tasks = []
    
    for part in parts:
        # Firma de la tarea
        t = process_image_chunk.s(part, filter_type="sobel")
        tasks.append(t)
        
    # Lanzar grupo
    job_group = group(tasks)
    async_result = job_group.apply_async()
    
    # Guardar referencia
    async_result.save()
    JOBS[job_id] = {
        "group_id": async_result.id,
        "total_chunks": chunks,
        "status": "processing",
        "filename": file.filename
    }
    
    return {"job_id": job_id, "message": f"Procesando en {chunks} partes"}

@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in JOBS:
        return {"error": "Job not found"}
    
    job_info = JOBS[job_id]
    group_res = GroupResult.restore(job_info["group_id"], app=celery_app)
    
    if not group_res:
        return {"status": "unknown"}
    
    # Verificar progreso
    ready = group_res.ready()
    completed = group_res.completed_count()
    total = len(group_res.children) if group_res.children else job_info["total_chunks"]
    
    print(f"Job {job_id}: ready={ready}, completed={completed}/{total}")

    if ready or completed >= total:
        # Todo terminado
        try:
            results = group_res.join()
        except:
             results = group_res.get()
             
    if ready or completed >= total:
        # Todo terminado
        try:
             results = group_res.join()
        except:
             results = group_res.get()
             
        # Verificar errores
        if any(r.get("status") == "failed" for r in results):
            print(f"Job {job_id} failed: {results}")
            return {"status": "failed", "details": results}
            
        def process_results_sync(results):
            # Unir imagen (Bloqueante)
            final_img_bytes = ImageProcessor.merge_images(results)
            b64_str = base64.b64encode(final_img_bytes).decode('utf-8')
            
            # Calcular stats
            total_gpu = sum(r.get("gpu_time", 0) for r in results)
            workers_used = list(set(r.get("worker") for r in results))
            
            return {
                "status": "completed",
                "progress": 100,
                "result_b64": b64_str,
                "stats": {
                    "total_gpu_time": total_gpu,
                    "workers": workers_used
                },
                "chunks_data": [
                    {
                        "worker": r.get("worker"), 
                        "gpu_time": r.get("gpu_time"),
                        "device": r.get("device"),
                        "index": r.get("index")
                    } for r in results 
                ]
            }

        print(f"Job {job_id}: merging images in threadpool...")
        response = await run_in_threadpool(process_results_sync, results)
        print(f"Job {job_id}: returning response status={response['status']}")
        return response
    else:
        # En progreso
        progress = int((completed / total) * 100) if total > 0 else 0
        return {
            "status": "processing",
            "progress": progress, 
            "total_chunks": job_info["total_chunks"]
        }
