from app.core.database import db
from app.core.config import settings
import time
from datetime import datetime

class Logger:
    @staticmethod
    def log(worker_name: str, message: str, level: str = "INFO"):
        """
        Logs an event to MongoDB.
        Note: This is synchronous because Celery tasks might run in sync context.
        If using async, we might need a different approach or run_in_executor.
        For simplicity in this demo, we assume the db client is accessible or we use a separate connection if needed.
        HOWEVER, our db.client is Motor (Async).
        For Celery workers (sync), we should ideally use PyMongo or just print to stdout and have a log collector.
        
        To keep it simple and consistent with the "No new libraries" rule and existing architecture:
        We will use a synchronous PyMongo connection specifically for workers, OR just rely on print
        and have a background task capture it? 
        
        BETTER APPROACH:
        The user wants to see logs in the web. The workers are Celery.
        We can't easily share the Async Motor client in Celery (Multiprocessing).
        
        Let's use a simple requests.post to the API to save the log? 
        No, that's inefficient.
        
        Let's just use standard PyMongo for the Logger inside tasks.
        But we need to install pymongo? It is likely installed as dependency of Motor.
        Yes, motor depends on pymongo.
        """
        try:
             # Just for the simulation, we will "fire and forget" if possible, 
             # but here we'll do a quick sync insert.
             # We need a sync client.
             from pymongo import MongoClient
             
             client = MongoClient(settings.MONGO_URI)
             collection = client[settings.MONGO_DB_NAME]['logs']
             
             entry = {
                 "worker": worker_name,
                 "message": message,
                 "level": level,
                 "timestamp": time.time(),
                 "dt_string": datetime.now().strftime("%H:%M:%S")
             }
             collection.insert_one(entry)
             client.close()
             
             # Also print to console for debugging
             print(f"[{worker_name}] {message}")
             
        except Exception as e:
            print(f"FAILED TO LOG TO DB: {e}")

logger = Logger()
