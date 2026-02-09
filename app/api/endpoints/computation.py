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
    if group_res.ready():
        # Todo terminado
        results = group_res.get()
        # Verificar errores
        if any(r.get("status") == "failed" for r in results):
            return {"status": "failed", "details": results}
            
        # Unir imagen
        final_img_bytes = ImageProcessor.merge_images(results)
        
        # Calcular stats
        total_gpu = sum(r.get("gpu_time", 0) for r in results)
        workers_used = list(set(r.get("worker") for r in results))
        
        return {
            "status": "completed",
            "progress": 100,
            "result_image": final_img_bytes.decode('latin1'), # Enviar como raw bytes string (o base64 en pydantic)
            # Mejor enviemos base64 para simpleza en frontend
            "result_b64": str(final_img_bytes, 'latin1') if False else None, # Hack, mejor recodificar
            "stats": {
                "total_gpu_time": total_gpu,
                "workers": list(workers_used) # Fix set json serialization
            },
            "chunks_data": [
                {
                    "worker": r.get("worker"), 
                    "gpu_time": r.get("gpu_time"),
                    "device": r.get("device"),
                    "index": r.get("index")
                } for r in results 
            ] # Send metadata only, not image data
        }
    else:
        # En progreso
        # completed_count() is flaky sometimes, better calculate from children
        # But for group result we need backend to support it. 
        # Using simple running estimate
        return {
            "status": "processing",
            "progress": 50, # Fake progress if not ready
            "total_chunks": job_info["total_chunks"]
        }
