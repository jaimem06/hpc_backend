from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None

db = Database()

async def get_database():
    return db.client[settings.MONGO_DB_NAME]

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(settings.MONGO_URI)
    print("|| Conectado a MongoDB")

async def close_mongo_connection():
    db.client.close()
    print("|| Desconectado de MongoDB")