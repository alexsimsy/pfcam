import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import structlog

from app.core.config import settings
from app.models.user import User
from app.models.event import Event
from app.models.camera import Camera

logger = structlog.get_logger()

class NotificationType(Enum):
    EVENT_CAPTURED = "event_captured"
    CAMERA_OFFLINE = "camera_offline"
    CAMERA_ONLINE = "camera_online"
    STORAGE_FULL = "storage_full"
    SYSTEM_ALERT = "system_alert"
    USER_ACTIVITY = "user_activity"

@dataclass
class NotificationPayload:
    type: NotificationType
    title: str
    message: str
    data: Dict[str, Any]
    timestamp: datetime
    priority: str = "normal"  # low, normal, high, urgent
    category: str = "general"

class WebSocketManager:
    """Manages WebSocket connections for real-time notifications"""
    
    def __init__(self):
        self.active_connections: Dict[int, Set[asyncio.Queue]] = {}
        self.connection_lock = asyncio.Lock()
    
    async def connect(self, user_id: int) -> asyncio.Queue:
        """Add a new WebSocket connection for a user"""
        async with self.connection_lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            
            queue = asyncio.Queue()
            self.active_connections[user_id].add(queue)
            logger.info("WebSocket connection added", user_id=user_id, total_connections=len(self.active_connections[user_id]))
            return queue
    
    async def disconnect(self, user_id: int, queue: asyncio.Queue):
        """Remove a WebSocket connection for a user"""
        async with self.connection_lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(queue)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                logger.info("WebSocket connection removed", user_id=user_id)
    
    async def send_to_user(self, user_id: int, payload: NotificationPayload):
        """Send notification to a specific user"""
        if user_id not in self.active_connections:
            return
        
        message = {
            "type": payload.type.value,
            "title": payload.title,
            "message": payload.message,
            "data": payload.data,
            "timestamp": payload.timestamp.isoformat(),
            "priority": payload.priority,
            "category": payload.category
        }
        
        # Send to all connections for this user
        for queue in self.active_connections[user_id].copy():
            try:
                await queue.put(json.dumps(message))
            except Exception as e:
                logger.error("Failed to send WebSocket message", user_id=user_id, error=str(e))
                # Remove broken connection
                await self.disconnect(user_id, queue)
    
    async def broadcast_to_all(self, payload: NotificationPayload, exclude_user: Optional[int] = None):
        """Broadcast notification to all connected users"""
        for user_id in list(self.active_connections.keys()):
            if exclude_user and user_id == exclude_user:
                continue
            await self.send_to_user(user_id, payload)

class EmailService:
    """Handles email notifications"""
    
    def __init__(self):
        self.smtp_config = {
            "hostname": settings.SMTP_SERVER,
            "port": settings.SMTP_PORT,
            "username": settings.SMTP_USER,
            "password": settings.SMTP_PASSWORD,
            "use_tls": settings.SMTP_TLS
        }
    
    async def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Send an email notification"""
        if not all([self.smtp_config["hostname"], self.smtp_config["username"], self.smtp_config["password"]]):
            logger.warning("SMTP not configured, skipping email")
            return False
        
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.smtp_config["username"]
            message["To"] = to_email
            
            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_config["hostname"],
                port=self.smtp_config["port"],
                username=self.smtp_config["username"],
                password=self.smtp_config["password"],
                use_tls=self.smtp_config["use_tls"]
            )
            
            logger.info("Email sent successfully", to=to_email, subject=subject)
            return True
            
        except Exception as e:
            logger.error("Failed to send email", to=to_email, error=str(e))
            return False
    
    def render_event_email_template(self, event: Event, camera: Camera, user: User) -> tuple[str, str]:
        """Render email template for event notifications"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Event Cam Event Alert</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #2563eb; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f8fafc; }
                .event-details { background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }
                .button { display: inline-block; padding: 10px 20px; background: #2563eb; color: white; text-decoration: none; border-radius: 5px; }
                .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
                @media (max-width: 600px) {
                    .container { padding: 10px; }
                    .header { padding: 15px; }
                    .content { padding: 15px; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 Event Cam Event Alert</h1>
                </div>
                <div class="content">
                    <h2>New Event Captured</h2>
                    <p>Hello {{ user.full_name or user.username }},</p>
                    <p>A new event has been captured by your camera system.</p>
                    
                    <div class="event-details">
                        <h3>Event Details:</h3>
                        <ul>
                            <li><strong>Camera:</strong> {{ camera.name }}</li>
                            <li><strong>Event Name:</strong> {{ event.event_name or 'Motion Event' }}</li>
                            <li><strong>Triggered:</strong> {{ event.triggered_at.strftime('%Y-%m-%d %H:%M:%S') }}</li>
                            <li><strong>File:</strong> {{ event.filename }}</li>
                            {% if event.playback_time %}
                            <li><strong>Duration:</strong> {{ event.playback_time }} seconds</li>
                            {% endif %}
                        </ul>
                    </div>
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{{ app_url }}/events" class="button">View Event</a>
                    </p>
                    
                    <p><small>This is an automated notification from your Event Cam system.</small></p>
                </div>
                <div class="footer">
                    <p>Event Cam - Industrial Event Camera Management</p>
                    <p>Generated on {{ timestamp }}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_template = """
Event Cam Event Alert

New Event Captured

Hello {{ user.full_name or user.username }},

A new event has been captured by your camera system.

Event Details:
- Camera: {{ camera.name }}
- Event Name: {{ event.event_name or 'Motion Event' }}
- Triggered: {{ event.triggered_at.strftime('%Y-%m-%d %H:%M:%S') }}
- File: {{ event.filename }}
{% if event.playback_time %}- Duration: {{ event.playback_time }} seconds{% endif %}

View the event at: {{ app_url }}/events

This is an automated notification from your Event Cam system.

Event Cam - Industrial Event Camera Management
Generated on {{ timestamp }}
        """
        
        # Template variables
        template_vars = {
            "user": user,
            "event": event,
            "camera": camera,
            "app_url": settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else "http://localhost:3000",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Render templates
        html_content = Template(html_template).render(**template_vars)
        text_content = Template(text_template).render(**template_vars)
        
        return html_content, text_content

class NotificationService:
    """Main notification service that coordinates all notification types"""
    
    def __init__(self):
        self.websocket_manager = WebSocketManager()
        self.email_service = EmailService()
    
    async def send_event_notification(self, event: Event, camera: Camera, users: List[User]):
        """Send notifications for new events"""
        logger.info("Sending event notifications", event_id=event.id, camera_id=camera.id, users_count=len(users))
        
        # Create notification payload
        payload = NotificationPayload(
            type=NotificationType.EVENT_CAPTURED,
            title="New Event Captured",
            message=f"Camera {camera.name} captured a new event",
            data={
                "event_id": event.id,
                "camera_id": camera.id,
                "camera_name": camera.name,
                "event_name": event.event_name,
                "filename": event.filename,
                "triggered_at": event.triggered_at.isoformat(),
                "playback_time": event.playback_time
            },
            timestamp=datetime.now(),
            priority="high",
            category="events"
        )
        
        # Send notifications to each user
        for user in users:
            try:
                # WebSocket notification (real-time)
                await self.websocket_manager.send_to_user(user.id, payload)
                
                # Email notification (if enabled)
                if user.email_notifications:
                    html_content, text_content = self.email_service.render_event_email_template(event, camera, user)
                    subject = f"Event Cam Alert: New Event from {camera.name}"
                    await self.email_service.send_email(user.email, subject, html_content, text_content)
                
            except Exception as e:
                logger.error("Failed to send notification to user", user_id=user.id, error=str(e))
    
    async def send_camera_status_notification(self, camera: Camera, is_online: bool, users: List[User]):
        """Send camera status change notifications"""
        status = "online" if is_online else "offline"
        notification_type = NotificationType.CAMERA_ONLINE if is_online else NotificationType.CAMERA_OFFLINE
        
        payload = NotificationPayload(
            type=notification_type,
            title=f"Camera {camera.name} {status.title()}",
            message=f"Camera {camera.name} is now {status}",
            data={
                "camera_id": camera.id,
                "camera_name": camera.name,
                "status": status,
                "timestamp": datetime.now().isoformat()
            },
            timestamp=datetime.now(),
            priority="normal" if is_online else "high",
            category="camera_status"
        )
        
        for user in users:
            try:
                await self.websocket_manager.send_to_user(user.id, payload)
                
                if user.email_notifications and not is_online:  # Only email for offline events
                    html_content = f"""
                    <h2>Camera Status Alert</h2>
                    <p>Camera <strong>{camera.name}</strong> is currently <strong>offline</strong>.</p>
                    <p>Please check the camera connection and power supply.</p>
                    <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    """
                    await self.email_service.send_email(
                        user.email,
                        f"Event Cam Alert: Camera {camera.name} Offline",
                        html_content
                    )
            except Exception as e:
                logger.error("Failed to send camera status notification", user_id=user.id, error=str(e))
    
    async def send_system_alert(self, title: str, message: str, priority: str = "normal", users: List[User] = None):
        """Send system-wide alerts"""
        payload = NotificationPayload(
            type=NotificationType.SYSTEM_ALERT,
            title=title,
            message=message,
            data={
                "alert_type": "system",
                "timestamp": datetime.now().isoformat()
            },
            timestamp=datetime.now(),
            priority=priority,
            category="system"
        )
        
        if users:
            for user in users:
                try:
                    await self.websocket_manager.send_to_user(user.id, payload)
                except Exception as e:
                    logger.error("Failed to send system alert", user_id=user.id, error=str(e))
        else:
            # Broadcast to all connected users
            await self.websocket_manager.broadcast_to_all(payload)
    
    def get_websocket_manager(self) -> WebSocketManager:
        """Get the WebSocket manager instance"""
        return self.websocket_manager

# Global notification service instance
notification_service = NotificationService() 