from app.core.celery_app import celery_app
import time
import base64
import io
import numpy as np
from PIL import Image, ImageFilter

# Intentar importar librerías de GPU
try:
    import cupy as cp
    import cupyx.scipy.ndimage as ndimage
    HAS_CUPY = True
except ImportError:
    HAS_CUPY = False

def apply_sobel_cpu(img):
    """Fallback CPU implementation using Pillow"""
    return img.filter(ImageFilter.FIND_EDGES)

def apply_sobel_gpu(img_array):
    """GPU implementation using Cupy"""
    # Convertir a array de GPU
    gpu_array = cp.asarray(img_array)
    
    # Convertir a escala de grises para simplificar Sobel (promedio de canales)
    if gpu_array.ndim == 3:
        gpu_gray = cp.mean(gpu_array, axis=2)
    else:
        gpu_gray = gpu_array

    # Sobel X y Y
    sx = ndimage.sobel(gpu_gray, axis=0, mode='constant')
    sy = ndimage.sobel(gpu_gray, axis=1, mode='constant')
    
    # Magnitud
    hypot = cp.hypot(sx, sy)
    
    # Normalizar a 0-255
    hypot = hypot / cp.max(hypot) * 255
    
    # Volver a CPU
    return cp.asnumpy(hypot).astype(np.uint8)

@celery_app.task(bind=True, name="process_image_chunk")
def process_image_chunk(self, chunk_data: dict, filter_type: str = "sobel"):
    worker_name = self.request.hostname
    start_time = time.time()
    
    # Decodificar
    img_bytes = base64.b64decode(chunk_data["data_b64"])
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    
    processing_device = "CPU"
    gpu_time = 0
    
    try:
        if HAS_CUPY:
            # --- RUTA GPU ---
            processing_device = f"GPU ({cp.cuda.Device().pci_bus_id})" if hasattr(cp.cuda.Device(), 'pci_bus_id') else "GPU"
            img_array = np.array(img)
            
            t0 = time.time()
            result_array = apply_sobel_gpu(img_array)
            cp.cuda.Stream.null.synchronize() # Sync
            gpu_time = time.time() - t0
            
            result_img = Image.fromarray(result_array).convert("RGB")
            print(f"[{worker_name}] 🖼 Procesado en GPU: {gpu_time:.4f}s")
        else:
            # --- RUTA CPU ---
            processing_device = "CPU (Fallback)"
            t0 = time.time()
            result_img = apply_sobel_cpu(img)
            gpu_time = time.time() - t0 # Es tiempo CPU en realidad
            print(f"[{worker_name}] 🖼 Procesado en CPU: {gpu_time:.4f}s")

        # Codificar respuesta
        buf = io.BytesIO()
        result_img.save(buf, format="PNG")
        result_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        
    except Exception as e:
        print(f"[{worker_name}] ❌ Error: {e}")
        return {"status": "failed", "error": str(e)}

    total_time = time.time() - start_time
    
    return {
        "status": "completed",
        "index": chunk_data["index"],
        "data_b64": result_b64,
        "worker": worker_name,
        "device": processing_device,
        "gpu_time": gpu_time,
        "total_time": total_time
    }