from app.core.celery_app import celery_app
import time
import requests
import os

@celery_app.task(bind=True, name="process_pdf_task")
def process_pdf_task(self, filename: str, download_url: str):
    worker_name = self.request.hostname
    print(f"[{worker_name}] 📥 Recibiendo tarea para: {filename}")
    
    # Crear carpeta temporal en el Worker
    os.makedirs("temp_worker", exist_ok=True)
    local_path = f"temp_worker/{filename}"

    try:
        # 1. Descargar el archivo REAL desde el servidor (API)
        print(f"   Descargando desde: {download_url}")
        response = requests.get(download_url, timeout=30)
        response.raise_for_status() # Lanza error si falla la descarga
        
        with open(local_path, "wb") as f:
            f.write(response.content)
            
        # 2. Procesamiento (Simulado)
        print(f"   ⚙️ Procesando {filename}...")
        time.sleep(5) # Simular trabajo pesado
        
        # Aquí iría tu código real de análisis de PDF
        
        # 3. Limpieza (Opcional)
        if os.path.exists(local_path):
            os.remove(local_path)

        return {
            "status": "completed",
            "processed_by": worker_name,
            "message": f"Archivo {filename} procesado correctamente."
        }

    except Exception as e:
        return {
            "status": "failed",
            "processed_by": worker_name,
            "error": str(e)
        }