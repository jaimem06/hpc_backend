from urllib.parse import quote
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles # Nuevo
from app.core.celery_app import celery_app
from app.tasks import process_pdf_task
from app.services.monitor import get_workers_status
from app.core.database import connect_to_mongo, close_mongo_connection, db
from app.core.config import settings
import shutil
import os

app = FastAPI(title=settings.PROJECT_NAME)

# 1. Configurar Archivos Estáticos (La Web)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

os.makedirs("uploads", exist_ok=True)

@app.on_event("startup")
async def startup():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown():
    await close_mongo_connection()

# --- RUTAS DE LA API ---

@app.get("/")
def read_root():
    return FileResponse('app/static/index.html')

@app.get("/api/jobs")
async def get_jobs_history():
    """Devuelve los últimos 10 trabajos para la tabla"""
    jobs = await db.client[settings.MONGO_DB_NAME].jobs.find().sort("_id", -1).limit(10).to_list(10)
    for job in jobs:
        job["_id"] = str(job["_id"])
    return jobs

@app.post("/submit-job/")
async def submit_job(file: UploadFile = File(...)):
    file_location = f"uploads/{file.filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        buffer.flush()
        os.fsync(buffer.fileno())

    if not os.path.exists(file_location) or os.path.getsize(file_location) == 0:
        return {"error": "Error guardando el archivo en el servidor"}

    filename_encoded = quote(file.filename)
    download_url = f"http://{settings.SERVER_IP}:8000/files/{filename_encoded}"
    task = process_pdf_task.delay(file.filename, download_url)
    
    await db.client[settings.MONGO_DB_NAME].jobs.insert_one({
        "task_id": task.id,
        "filename": file.filename,
        "status": "queued",
        "download_url": download_url,
        "worker": "Waiting..."
    })
    return {"task_id": task.id, "status": "Enviado"}

@app.get("/files/{filename}")
def download_file(filename: str):
    path = f"uploads/{filename}"
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "File not found"}

@app.get("/cluster/status")
def cluster_status():
    return get_workers_status()

app.get("/api/jobs")
async def get_jobs_history():
    jobs_cursor = db.client[settings.MONGO_DB_NAME].jobs.find().sort("_id", -1).limit(20)
    jobs = await jobs_cursor.to_list(length=20)
    
    results = []
    for job in jobs:
        results.append({
            "filename": job.get("filename"),
            "status": job.get("status"),
            "worker": job.get("worker", "Pendiente"),
            "task_id": job.get("task_id"),
            "download_url": job.get("download_url")
        })
    return results