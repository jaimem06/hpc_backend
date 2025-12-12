from fastapi import APIRouter
from app.core.database import db
from app.core.config import settings
from typing import List
from app.schemas.job import JobResponse

router = APIRouter()

@router.get("/", response_model=List[JobResponse])
async def get_jobs_history():
    jobs_cursor = db.client[settings.MONGO_DB_NAME].jobs.find().sort("_id", -1).limit(20)
    jobs = await jobs_cursor.to_list(length=20)
    
    results = []
    for job in jobs:
        results.append({
            "filename": job.get("filename"),
            "status": job.get("status"),
            "worker": job.get("worker", "Pendiente"),
            "task_id": str(job.get("task_id")),
            "download_url": job.get("download_url"),
            "type": job.get("type", "file_processing")
        })
    return results
