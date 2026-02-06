from app.core.celery_app import celery_app
import cupy as cp
import time

@celery_app.task(bind=True, name="gpu_matrix_calculation")
def gpu_matrix_calculation(self, size: int):
    worker_name = self.request.hostname
    print(f"[{worker_name}] 🚀 Iniciando cálculo en GPU (Matriz {size}x{size})")
    
    try:
        # Crear matrices aleatorias directamente en la memoria de la GPU
        a_gpu = cp.random.rand(size, size)
        b_gpu = cp.random.rand(size, size)
        
        # Multiplicación de matrices acelerada por hardware
        start_time = time.time()
        result_gpu = cp.dot(a_gpu, b_gpu)
        # Forzar sincronización para medir tiempo real
        cp.cuda.Stream.null.synchronize()
        end_time = time.time()
        
        return {
            "status": "completed",
            "processed_by": worker_name,
            "execution_time": end_time - start_time,
            "device": cp.cuda.Device().pci_bus_id,
            "message": "Cálculo paralelo en GPU exitoso"
        }
    except Exception as e:
        print(f"[{worker_name}] ❌ Error en GPU: {str(e)}")
        return {"status": "failed", "error": str(e)}