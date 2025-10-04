from pydantic import BaseModel
from typing import List, Dict, Optional

class ProcessRequest(BaseModel):
    operation: str
    file_keys: List[str]
    options: Optional[Dict] = {}

class StatusResponse(BaseModel):
    status: str
    download_url: Optional[str] = None
    error: Optional[str] = None