from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class TagBase(BaseModel):
    name: str
    color: Optional[str] = "#3B82F6"
    description: Optional[str] = None

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None

class TagResponse(TagBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TagList(BaseModel):
    tags: List[TagResponse]
    total: int

class EventTagAssignment(BaseModel):
    event_id: int
    tag_ids: List[int]

class TagUsage(BaseModel):
    tag: TagResponse
    usage_count: int 