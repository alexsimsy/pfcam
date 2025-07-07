import httpx
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
import structlog
from pydantic import BaseModel

from app.core.config import settings

logger = structlog.get_logger()

class CameraEvent(BaseModel):
    """Camera event model based on actual API response"""
    age: int
    dir: str
    eventName: Optional[str] = None
    fileName: str
    playbackTime: int
    thmbExt: str
    triggeredAt: str  # ISO format string from camera
    vidExt: str

class CameraSettings(BaseModel):
    """Camera settings model based on actual API response"""
    # Access settings
    access_password_hash_admin: str = ""
    access_password_hash_viewer: str = ""
    access_user_name_admin: str = "admin"
    access_user_name_viewer: str = "viewer"
    
    # Network settings
    network_ip: str
    network_mask: int
    network_gateway: str = ""
    network_dns: str = ""
    network_dhcp: bool = True
    network_ntp: str = ""
    network_ntp_ignore_server_sync: bool = False
    
    # FTP settings
    network_ftp_host: str = ""
    network_ftp_port: int = 21
    network_ftp_user: str = ""
    network_ftp_password: str = ""
    network_ftp_path: str = ""
    network_ftp_recordings: bool = False
    network_ftp_snapshots: bool = False
    
    # Recording settings
    recording_seconds_pre_event: int
    recording_seconds_post_event: int
    recording_seconds_pre_event_extended: int = 120
    recording_seconds_post_event_extended: int = 120
    recording_seconds_extended: bool = False
    recording_resolution_width: int
    recording_quality_level: int
    recording_quota_named: int = 100
    recording_quota_unnamed: int = 100
    recording_ensure_free_storage: bool = True
    recording_size_extended: bool = False
    
    # Exposure settings
    exposure_iso: int
    exposure_shutter: int
    exposure_manual: bool
    
    # Focus settings
    focus_setpoint: int
    
    # Overlay settings
    overlay_datetime: bool
    overlay_name: bool
    overlay_background: bool
    overlay_user: bool = True
    
    # Live stream settings
    live_resolution_width: int
    live_quality_level: int
    
    # RTSP settings
    rtsp: bool = True
    rtsp_port: int
    rtsp_path: str = ""
    rtsp_fps: int
    rtsp_quality_level: int
    rtsp_resolution_width: int
    rtsp_resolution_width_2: int = 640
    rtsp_auth: bool = False
    rtsp_type: int = 2
    
    # Other settings
    name: str
    picture_rotation: int = 0
    heater_level: int = 0
    time_zone: str = ""

class StreamUrl(BaseModel):
    """Stream URL model"""
    absolute: str
    relative: Optional[str] = None

class StreamSnapshot(BaseModel):
    """Stream snapshot model"""
    url: StreamUrl

class StreamInfo(BaseModel):
    """Stream information model based on actual API response"""
    name: str
    codec: str
    fps: int
    resolution: Dict[str, int]
    url: StreamUrl
    snapshot: Optional[StreamSnapshot] = None

class SystemInfo(BaseModel):
    """System information model based on actual API response"""
    brand: str
    customSerialNumber: str
    firmwareLink: str
    hardwareVersion: str
    hasVcm: bool
    heaterTemperature: float
    ipAddress: str
    macAddress: str
    name: str
    serialNumber: str
    service_uptime: int
    settingsLink: str
    softwareVersion: str
    systemTime: str
    timezone: str
    uptime: int

class CameraClient:
    """Client for interacting with the industrial event camera API"""
    
    def __init__(self, base_url: str = None, timeout: int = None):
        self.base_url = base_url or settings.CAMERA_BASE_URL
        self.timeout = timeout or settings.CAMERA_TIMEOUT
        self.retry_attempts = settings.CAMERA_RETRY_ATTEMPTS
        self.client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to camera API with retry logic"""
        if not self.client:
            raise RuntimeError("CameraClient not initialized. Use async context manager.")

        # Normalize base_url to avoid double /api
        if self.base_url.rstrip('/').endswith('/api'):
            url = f"{self.base_url.rstrip('/')}{endpoint}"
        else:
            url = f"{self.base_url.rstrip('/')}/api{endpoint}"

        for attempt in range(self.retry_attempts):
            try:
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                
                if response.headers.get("content-type", "").startswith("application/json"):
                    return response.json()
                else:
                    return response.content
                        
            except httpx.HTTPError as e:
                logger.warning(
                    "Camera API request failed",
                    attempt=attempt + 1,
                    endpoint=endpoint,
                    error=str(e)
                )
                
                if attempt == self.retry_attempts - 1:
                    raise
                
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def get_events(self, filters: Dict[str, Any] = None) -> List[CameraEvent]:
        """Get list of events from camera"""
        params = filters or {}
        response = await self._make_request("GET", "/events", params=params)
        
        events = []
        for event_data in response:
            # Handle null eventName
            if event_data.get("eventName") is None:
                event_data["eventName"] = None
            events.append(CameraEvent(**event_data))
        
        return events
    
    async def get_event_file(self, filename: str) -> bytes:
        """Download event file (image/video) from camera"""
        return await self._make_request("GET", f"/events/{filename}")
    
    async def delete_event(self, filename: str) -> bool:
        """Delete specific event from camera"""
        await self._make_request("DELETE", f"/events/{filename}")
        return True
    
    async def delete_all_events(self) -> bool:
        """Delete all events from camera"""
        await self._make_request("DELETE", "/events")
        return True
    
    async def get_active_events(self) -> List[CameraEvent]:
        """Get list of currently active events"""
        response = await self._make_request("GET", "/events/active")
        
        events = []
        for event_data in response:
            # Handle null eventName
            if event_data.get("eventName") is None:
                event_data["eventName"] = None
            events.append(CameraEvent(**event_data))
        
        return events
    
    async def stop_active_event(self, event_name: str) -> bool:
        """Stop specific active event"""
        await self._make_request("DELETE", f"/events/active/{event_name}")
        return True
    
    async def stop_all_active_events(self) -> bool:
        """Stop all active events"""
        await self._make_request("DELETE", "/events/active")
        return True
    
    async def get_settings(self) -> CameraSettings:
        """Get current camera settings"""
        response = await self._make_request("GET", "/system/settings")
        return CameraSettings(**response)
    
    async def update_settings(self, settings: CameraSettings) -> CameraSettings:
        """Update camera settings"""
        response = await self._make_request("PUT", "/system/settings", json=settings.dict())
        return CameraSettings(**response)
    
    async def reset_settings(self) -> CameraSettings:
        """Reset camera settings to defaults"""
        response = await self._make_request("DELETE", "/system/settings")
        return CameraSettings(**response)
    
    async def get_streams(self) -> Dict[str, StreamInfo]:
        """Get available video streams"""
        response = await self._make_request("GET", "/streams")
        
        streams = {}
        for name, stream_data in response.items():
            streams[name] = StreamInfo(**stream_data)
        
        return streams
    
    async def get_system_info(self) -> SystemInfo:
        """Get system information"""
        response = await self._make_request("GET", "/system")
        return SystemInfo(**response)
    
    async def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information"""
        return await self._make_request("GET", "/system/storage")
    
    async def get_firmware_info(self) -> Dict[str, Any]:
        """Get firmware information"""
        return await self._make_request("GET", "/system/firmware")
    
    async def reboot_system(self) -> bool:
        """Reboot the camera system"""
        await self._make_request("POST", "/system/reboot")
        return True
    
    async def get_datetime(self) -> Dict[str, Any]:
        """Get current date/time settings"""
        return await self._make_request("GET", "/system/datetime")
    
    async def get_timezones(self) -> List[str]:
        """Get available timezones"""
        return await self._make_request("GET", "/system/timezones")
    
    async def get_exposure_settings(self) -> Dict[str, Any]:
        """Get exposure settings"""
        return await self._make_request("GET", "/system/exposure")
    
    async def update_exposure_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update exposure settings"""
        return await self._make_request("PUT", "/system/exposure", json=settings)
    
    async def get_focus_settings(self) -> Dict[str, Any]:
        """Get focus settings"""
        return await self._make_request("GET", "/system/focus")
    
    async def update_focus_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update focus settings"""
        return await self._make_request("PUT", "/system/focus", json=settings)
    
    async def get_overlay_settings(self) -> Dict[str, Any]:
        """Get overlay settings"""
        return await self._make_request("GET", "/system/overlay")
    
    async def update_overlay_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update overlay settings"""
        return await self._make_request("PUT", "/system/overlay", json=settings)
    
    async def test_connection(self) -> bool:
        """Test connection to camera"""
        try:
            await self._make_request("GET", "/system")
            return True
        except Exception as e:
            logger.error("Camera connection test failed", error=str(e))
            return False

    async def take_snapshot(self, stream_name: str = "hd") -> bytes:
        """Take a direct snapshot from the specified stream"""
        try:
            # First get the stream info to find the snapshot URL
            streams = await self.get_streams()
            if stream_name not in streams:
                raise ValueError(f"Stream '{stream_name}' not found")
            
            stream = streams[stream_name]
            if not stream.snapshot:
                raise ValueError(f"Snapshot not available for stream '{stream_name}'")
            
            # Get the snapshot URL
            snapshot_url = stream.snapshot.url.absolute or stream.snapshot.url.relative
            if not snapshot_url:
                raise ValueError("Snapshot URL not available")
            
            # Make a direct request to the snapshot URL
            if not self.client:
                raise RuntimeError("CameraClient not initialized. Use async context manager.")
            
            # If it's a relative URL, construct the full URL
            if snapshot_url.startswith('/'):
                full_url = f"{self.base_url.rstrip('/')}{snapshot_url}"
            else:
                full_url = snapshot_url
            
            async with self.client.get(full_url) as response:
                response.raise_for_status()
                return await response.read()
                
        except Exception as e:
            logger.error("Failed to take snapshot", stream_name=stream_name, error=str(e))
            raise

    async def trigger_event(
        self,
        pre_event_seconds: int = 10,
        post_event_seconds: int = 10,
        event_name: str = "string",
        overlay_text: str = "string",
        stop_other_events: str = "none"
    ) -> bool:
        # Always send a fixed post-event duration (default 10s)
        payload = {
            "eventName": event_name,
            "overlayText": overlay_text,
            "preEventSeconds": pre_event_seconds,
            "postEventSeconds": post_event_seconds,
            "postEventUnlimited": False,
            "stopOtherEvents": stop_other_events
        }
        logger.info("Triggering camera event", payload=payload)
        try:
            response = await self._make_request("POST", "/events", json=payload)
            logger.info("Camera event triggered successfully", response=response)
            return True
        except Exception as e:
            logger.error("Failed to trigger event", error=str(e), payload=payload)
            return False

# Factory function for creating camera client
async def get_camera_client() -> CameraClient:
    """Get camera client instance"""
    return CameraClient() 