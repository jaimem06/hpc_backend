import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Configuración de la App
    PROJECT_NAME: str = "HPC Cluster Manager"
    SERVER_IP: str = "127.0.0.1" # IP de TU máquina (cambiar en .env)
    
    # Base de Datos
    MONGO_URI: str
    MONGO_DB_NAME: str
    
    # Cola de Tareas (Redis)
    REDIS_URL: str

    class Config:
        env_file = ".env"

settings = Settings()