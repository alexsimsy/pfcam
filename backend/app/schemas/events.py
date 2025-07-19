from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from .tags import TagResponse

class EventResponse(BaseModel):
    id: int  # This will be our Event ID
    camera_id: int
    filename: str  # Keep for internal use but won't display
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
    is_orphaned: Optional[bool] = False
    is_played: Optional[bool] = False
    event_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Camera information
    camera_name: Optional[str] = None
    
    # Tags
    tags: List[TagResponse] = []
    
    # Computed fields for display
    @property
    def event_id(self) -> str:
        """Return formatted Event ID"""
        return f"E{self.id:04d}"
    
    @property
    def display_name(self) -> str:
        """Return a user-friendly event name"""
        if self.event_name and self.event_name.strip():
            return self.event_name.strip()
        return f"Event {self.event_id}"
    
    @property
    def status_summary(self) -> dict:
        """Return status summary for UI display"""
        return {
            "on_camera": not self.is_orphaned and not self.is_downloaded,
            "downloaded": self.is_downloaded,
            "played": self.is_played,
            "processed": self.is_processed
        }
    
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