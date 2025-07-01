from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class EventResponse(BaseModel):
    id: int
    camera_id: int
    filename: str
    event_name: Optional[str]
    triggered_at: datetime
    file_size: Optional[int]
    file_path: Optional[str]
    thumbnail_path: Optional[str]
    video_extension: Optional[str]
    thumbnail_extension: Optional[str]
    playback_time: Optional[int]
    is_downloaded: bool
    is_processed: bool
    is_deleted: bool
    event_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Camera information
    camera_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class EventList(BaseModel):
    events: List[EventResponse]
    total: int
    limit: int
    offset: int

class EventDownload(BaseModel):
    event_id: int
    filename: str
    file_size: int
    download_url: str

class EventSync(BaseModel):
    camera_id: Optional[int] = None
    force_sync: bool = False

class EventFilter(BaseModel):
    camera_id: Optional[int] = None
    event_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_downloaded: Optional[bool] = None
    is_processed: Optional[bool] = None

class EventBulkAction(BaseModel):
    event_ids: List[int]
    action: str  # "download", "delete", "process"

class ActiveEvent(BaseModel):
    filename: str
    event_name: str
    triggered_at: datetime
    age: int 