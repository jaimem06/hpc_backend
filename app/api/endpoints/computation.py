from fastapi import APIRouter, Body
from app.schemas.job import ComputationJobCreate
from app.services.job_splitter import JobSplitter

router = APIRouter()

@router.post("/submit/", response_model=dict)
async def submit_computation_job(job_data: ComputationJobCreate):
    task_id, chunks = await JobSplitter.split_and_dispatch_prime_job(
        job_data.start_range, 
        job_data.end_range, 
        f"Primes {job_data.start_range}-{job_data.end_range}"
    )
    
    return {
        "task_id": task_id, 
        "status": "Splitting", 
        "msg": f"Job dividido en {chunks} tareas"
    }
