from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class SettingsResponse(BaseModel):
    camera_id: int
    settings: Dict[str, Any]
    version: str

class SettingsUpdate(BaseModel):
    # Network settings
    network_ip: Optional[str] = None
    network_mask: Optional[str] = None
    network_gateway: Optional[str] = None
    network_dns: Optional[str] = None
    network_dhcp: Optional[bool] = None
    
    # Recording settings
    recording_seconds_pre_event: Optional[int] = None
    recording_seconds_post_event: Optional[int] = None
    recording_resolution_width: Optional[int] = None
    recording_quality_level: Optional[int] = None
    
    # Exposure settings
    exposure_iso: Optional[int] = None
    exposure_shutter: Optional[int] = None
    exposure_manual: Optional[bool] = None
    
    # Focus settings
    focus_setpoint: Optional[int] = None
    
    # Overlay settings
    overlay_datetime: Optional[bool] = None
    overlay_name: Optional[bool] = None
    overlay_background: Optional[bool] = None
    
    # RTSP settings
    rtsp_port: Optional[int] = None
    rtsp_path: Optional[str] = None
    rtsp_fps: Optional[int] = None
    rtsp_quality_level: Optional[int] = None

class SettingsReset(BaseModel):
    confirm: bool = False

class ExposureSettings(BaseModel):
    iso: Optional[int] = None
    shutter: Optional[int] = None
    manual: Optional[bool] = None

class FocusSettings(BaseModel):
    setpoint: Optional[int] = None

class OverlaySettings(BaseModel):
    datetime: Optional[bool] = None
    name: Optional[bool] = None
    background: Optional[bool] = None

class ApplicationSettingsBase(BaseModel):
    auto_start_streams: bool = False
    stream_quality: str = 'medium'
    store_data_on_camera: bool = True
    auto_download_events: bool = False
    auto_download_snapshots: bool = False
    event_retention_days: int = 30
    snapshot_retention_days: int = 7
    mobile_data_saving: bool = True
    low_bandwidth_mode: bool = False

class ApplicationSettingsCreate(ApplicationSettingsBase):
    pass

class ApplicationSettingsUpdate(BaseModel):
    auto_start_streams: Optional[bool] = None
    stream_quality: Optional[str] = None
    store_data_on_camera: Optional[bool] = None
    auto_download_events: Optional[bool] = None
    auto_download_snapshots: Optional[bool] = None
    event_retention_days: Optional[int] = None
    snapshot_retention_days: Optional[int] = None
    mobile_data_saving: Optional[bool] = None
    low_bandwidth_mode: Optional[bool] = None

class ApplicationSettingsResponse(ApplicationSettingsBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 