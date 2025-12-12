from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from app.worker.pdf_tasks import process_pdf_task
from app.core.database import db
from app.core.config import settings
from urllib.parse import quote
import shutil
import os

router = APIRouter()

@router.post("/submit/", response_model=dict)
async def submit_file_job(file: UploadFile = File(...)):
    file_location = f"uploads/{file.filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    if not os.path.exists(file_location):
        raise HTTPException(status_code=500, detail="Error saving file")

    filename_encoded = quote(file.filename)
    download_url = f"http://{settings.SERVER_IP}:8000/files/{filename_encoded}"
    
    # Dispatch task
    task = process_pdf_task.delay(file.filename, download_url)
    
    await db.client[settings.MONGO_DB_NAME].jobs.insert_one({
        "task_id": task.id,
        "filename": file.filename,
        "status": "queued",
        "type": "file_processing",
        "download_url": download_url,
        "worker": "Waiting..."
    })
    return {"task_id": task.id, "status": "Enviado"}

@router.get("/download/{filename}")
def download_file(filename: str):
    path = f"uploads/{filename}"
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "File not found"}
