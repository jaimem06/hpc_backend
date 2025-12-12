from app.core.celery_app import celery_app
import math
import time

def is_prime(n):
    if n < 2: return False
    if n % 2 == 0: return False
    
    sqrt_n = int(math.isqrt(n))
    for i in range(3, sqrt_n + 1, 2):
        if n % i == 0:
            return False
    return True

@celery_app.task(bind=True, name="calculate_primes_task")
def calculate_primes_task(self, start: int, end: int):
    worker_name = self.request.hostname
    print(f"[{worker_name}] 🧮 Calculando primos en rango: {start}-{end}")
    
    primes = []
    
    # Real CPU work
    for num in range(start, end + 1):
        if is_prime(num):
            primes.append(num)
            
    print(f"[{worker_name}] ✅ Rango {start}-{end} completado. Encontrados: {len(primes)}")
    
    return {
        "status": "completed",
        "processed_by": worker_name,
        "primes_found": len(primes), # No devolvemos la lista entera para no saturar Redis/Mongo si es muy grande
        "range": f"{start}-{end}",
        "sample_primes": primes[:10] # Solo una muestra
    }
