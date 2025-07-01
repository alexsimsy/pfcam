from typing import Optional, Dict, Any
from pydantic import BaseModel, field_validator
from datetime import datetime

class CameraResponse(BaseModel):
    id: int
    name: str
    ip_address: str
    port: int
    base_url: str
    username: Optional[str]
    password: Optional[str]
    use_ssl: bool
    model: Optional[str]
    firmware_version: Optional[str]
    serial_number: Optional[str]
    is_active: bool
    is_online: bool
    last_seen: Optional[datetime]
    settings: Optional[Dict[str, Any]]
    camera_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class CameraCreate(BaseModel):
    name: str
    ip_address: str
    port: int = 80
    base_url: str
    username: Optional[str] = None
    password: Optional[str] = None
    use_ssl: bool = False
    
    @field_validator('base_url')
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('base_url must start with http:// or https://')
        return v

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    base_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    use_ssl: Optional[bool] = None
    is_active: Optional[bool] = None
    
    @field_validator('base_url')
    def validate_base_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('base_url must start with http:// or https://')
        return v

class CameraStatus(BaseModel):
    camera_id: int
    is_online: bool
    last_seen: Optional[datetime]
    system_info: Optional[Dict[str, Any]]
    storage_info: Optional[Dict[str, Any]]
    connection_status: str  # "connected", "disconnected", "error"
    error_message: Optional[str] = None

class CameraStream(BaseModel):
    name: str
    codec: str
    fps: int
    resolution: Dict[str, int]
    url: Dict[str, str]
    snapshot: Optional[Dict[str, Dict[str, str]]] = None

class CameraBulkStatus(BaseModel):
    camera_ids: list[int]

class CameraConnectionTest(BaseModel):
    camera_id: int
    test_connection: bool = True 