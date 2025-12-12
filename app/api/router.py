from fastapi import APIRouter
from app.api.endpoints import files, computation, jobs, logs

api_router = APIRouter()

api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(computation.router, prefix="/computation", tags=["computation"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
