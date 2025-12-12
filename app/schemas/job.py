from pydantic import BaseModel
from typing import Optional, List

class JobBase(BaseModel):
    filename: Optional[str] = None
    status: str
    worker: str = "Pending"
    task_id: str
    download_url: Optional[str] = None
    type: str = "file_processing" # "file_processing" or "computation"

class JobCreate(BaseModel):
    pass

class ComputationJobCreate(BaseModel):
    start_range: int
    end_range: int

class JobResponse(JobBase):
    pass
