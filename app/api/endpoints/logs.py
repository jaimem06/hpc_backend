from fastapi import APIRouter, Query
from app.core.database import db
from app.core.config import settings
from typing import List
from pydantic import BaseModel

class LogEntry(BaseModel):
    worker: str
    message: str
    level: str
    dt_string: str

router = APIRouter()

@router.get("/live", response_model=List[LogEntry])
async def get_live_logs(limit: int = 50):
    """Get the most recent logs"""
    # Sort by timestamp desc
    cursor = db.client[settings.MONGO_DB_NAME].logs.find().sort("timestamp", -1).limit(limit)
    logs = await cursor.to_list(length=limit)
    
    # Return reversed (oldest to newest) for the terminal view
    return list(reversed(logs))
