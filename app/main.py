from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from app.core.celery_app import celery_app
from app.tasks import process_pdf_task
from app.services.monitor import get_workers_status
from app.core.database import connect_to_mongo, close_mongo_connection, db
from app.core.config import settings
import shutil
import os

app = FastAPI(title=settings.PROJECT_NAME)

os.makedirs("uploads", exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "online", "server": settings.PROJECT_NAME, "ip": settings.SERVER_IP}

@app.on_event("startup")
async def startup():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown():
    await close_mongo_connection()

@app.post("/submit-job/")
async def submit_job(file: UploadFile = File(...)):
    file_location = f"uploads/{file.filename}"
    
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Generar URL dinámica basada en la config
    download_url = f"http://{settings.SERVER_IP}:8000/files/{file.filename}"

    # Enviar tarea a Celery
    task = process_pdf_task.delay(file.filename, download_url)
    
    # Guardar estado inicial en Mongo
    # Usamos db.client[settings.MONGO_DB_NAME] para ser seguros
    await db.client[settings.MONGO_DB_NAME].jobs.insert_one({
        "task_id": task.id,
        "filename": file.filename,
        "status": "queued",
        "download_url": download_url
    })

    return {"task_id": task.id, "status": "Enviado al cluster", "url": download_url}

@app.get("/files/{filename}")
def download_file(filename: str):
    path = f"uploads/{filename}"
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "File not found"}

@app.get("/cluster/status")
def cluster_status():
    return get_workers_status()