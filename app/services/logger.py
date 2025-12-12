from app.core.config import settings
from datetime import datetime
import time

class Logger:
    def __init__(self):
        self._client = None
        self._collection = None

    def _get_collection(self):
        # Lazy initialization
        if self._collection is None:
            try:
                from pymongo import MongoClient
                print(f"LOGGER: Intentando conectar a Mongo en: {settings.MONGO_URI}")
                
                 # Connect with shorter timeout
                try:
                    self._client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
                    # Force connection check
                    self._client.admin.command('ping')
                except Exception as e:
                    print(f"LOGGER: Falló conexión a {settings.MONGO_URI}. Intentando localhost...")
                    self._client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
                    self._client.admin.command('ping')

                self._collection = self._client[settings.MONGO_DB_NAME]['logs']
                print("LOGGER: Conexión a Mongo EXITOSA.")
                
            except Exception as e:
                print(f"LOGGER INIT ERROR: {e}")
                return None
        return self._collection

    def log(self, worker_name: str, message: str, level: str = "INFO"):
        try:
             collection = self._get_collection()
             if collection is not None:
                entry = {
                    "worker": worker_name,
                    "message": message,
                    "level": level,
                    "timestamp": time.time(),
                    "dt_string": datetime.now().strftime("%H:%M:%S")
                }
                collection.insert_one(entry)
             
             # Always print to console as fallback
             print(f"[{worker_name}] {message}")
             
        except Exception as e:
            # If DB fails, assume connection lost, reset client for next try
            print(f"FAILED TO LOG TO DB: {e} | MSG: {message}")
            self._client = None
            self._collection = None

logger = Logger()
