from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.config import settings
from app.api.router import api_router
from app.services.monitor import get_workers_status
import os

app = FastAPI(title=settings.PROJECT_NAME)

# 1. Configurar Archivos Estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/files", StaticFiles(directory="uploads"), name="files") # Direct Serve

os.makedirs("uploads", exist_ok=True)

@app.on_event("startup")
async def startup():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown():
    await close_mongo_connection()

# --- API ROUTER ---
app.include_router(api_router, prefix="/api")

# --- ROOT ---
@app.get("/")
def read_root():
    return FileResponse('app/static/index.html')

@app.get("/cluster/status")
def cluster_status():
    return get_workers_status()