from app.worker.math_tasks import calculate_primes_task
from app.core.database import db
from app.core.config import settings
from celery import group

class JobSplitter:
    @staticmethod
    async def split_and_dispatch_prime_job(start: int, end: int, filename_alias: str):
        total_nums = end - start
        
        # Estrategia de partición simple
        # Dividimos en chunks de 10,000 o menos si es pequeño
        CHUNK_SIZE = 10000 
        chunks = []
        
        current_start = start
        while current_start <= end:
            current_end = min(current_start + CHUNK_SIZE - 1, end)
            chunks.append((current_start, current_end))
            current_start += CHUNK_SIZE
            
        print(f"Dividiendo trabajo {start}-{end} en {len(chunks)} tareas.")
        
        # Crear grupo de tareas de Celery (Parallel execution)
        job_group = group(calculate_primes_task.s(c_start, c_end) for c_start, c_end in chunks)
        result = job_group.apply_async()
        
        # Guardar metadatos del "Parent Job"
        await db.client[settings.MONGO_DB_NAME].jobs.insert_one({
            "task_id": result.id, # Group ID
            "filename": filename_alias, # Ej: "Primes 1-100k"
            "status": "processing",
            "type": "computation",
            "total_chunks": len(chunks),
            "range_start": start,
            "range_end": end,
            "created_at": time.time()
        })
        
        return result.id, len(chunks)

import time
