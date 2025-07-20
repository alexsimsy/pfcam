from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime

class NotificationPreferences(BaseModel):
    """Notification preferences for a user"""
    email_notifications: bool = True
    webhook_url: Optional[str] = None
    event_notifications: bool = True
    camera_status_notifications: bool = True
    system_alerts: bool = True

class NotificationPreferencesUpdate(BaseModel):
    """Update notification preferences"""
    email_notifications: Optional[bool] = None
    webhook_url: Optional[str] = None
    event_notifications: Optional[bool] = None
    camera_status_notifications: Optional[bool] = None
    system_alerts: Optional[bool] = None

class NotificationMessage(BaseModel):
    """Real-time notification message"""
    type: str
    title: str
    message: str
    data: Dict[str, Any]
    timestamp: str
    priority: str = "normal"
    category: str = "general"

class NotificationStatus(BaseModel):
    """Notification system status"""
    websocket_connected: bool
    email_enabled: bool
    webhook_configured: bool
    active_connections: int

class TestEmailResponse(BaseModel):
    """Response for test email endpoint"""
    message: str 