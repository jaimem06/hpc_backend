from app.core.celery_app import celery_app
import time
import requests
import os

@celery_app.task(bind=True, name="process_pdf_task")
def process_pdf_task(self, filename: str, download_url: str):
    worker_name = self.request.hostname
    print(f"[{worker_name}] 📥 Iniciando descarga: {filename} desde {download_url}")
    
    os.makedirs("temp_worker", exist_ok=True)
    local_path = f"temp_worker/{filename}"

    try:
        with requests.get(download_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            
            content_type = r.headers.get('content-type', '')
            if 'text' in content_type or 'json' in content_type:
                raise Exception(f"URL devolvió texto en lugar de archivo: {r.text[:100]}")

            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"[{worker_name}] || Descarga completa ({os.path.getsize(local_path)} bytes). Procesando...")
        
        # Simula procesamiento
        time.sleep(5) 
        
        if os.path.exists(local_path):
            os.remove(local_path)

        return {
            "status": "completed",
            "processed_by": worker_name,
            "message": f"Archivo procesado correctamente."
        }

    except requests.exceptions.HTTPError as e:
        print(f"[{worker_name}] || Error HTTP al descargar: {e}")
        return {"status": "failed", "error": f"Error de red: {str(e)}"}
    except Exception as e:
        print(f"[{worker_name}] || Error crítico: {e}")
        return {"status": "failed", "error": str(e)}
