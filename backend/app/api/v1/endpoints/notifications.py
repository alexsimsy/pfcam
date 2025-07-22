from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import json
import structlog

from app.core.database import get_db
from app.core.security import get_current_user_ws, get_current_user
from app.models.user import User
from app.services.notification_service import notification_service, NotificationType
from app.schemas.notifications import NotificationPreferences, NotificationPreferencesUpdate

logger = structlog.get_logger()
router = APIRouter()

@router.websocket("/test")
async def test_websocket(websocket: WebSocket):
    """Test WebSocket endpoint"""
    logger.info("Test WebSocket connection attempt")
    await websocket.accept()
    await websocket.send_text("Test WebSocket working!")
    await websocket.close()

@router.post("/test-websocket")
async def test_websocket_notification(
    current_user: User = Depends(get_current_user)
):
    """Send a test WebSocket notification to the current user"""
    try:
        # Create a test notification payload
        from app.services.notification_service import NotificationPayload
        from datetime import datetime
        
        payload = NotificationPayload(
            type=NotificationType.SYSTEM_ALERT,
            title="WebSocket Test",
            message="This is a test WebSocket notification",
            data={"test": True, "timestamp": datetime.now().isoformat()},
            timestamp=datetime.now(),
            priority="normal",
            category="test"
        )
        
        # Send directly to the current user via WebSocket
        ws_manager = notification_service.get_websocket_manager()
        await ws_manager.send_to_user(current_user.id, payload)
        
        logger.info("Test WebSocket notification sent", user_id=current_user.id)
        
        return {"message": "Test WebSocket notification sent successfully"}
        
    except Exception as e:
        logger.error("Failed to send test WebSocket notification", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test WebSocket notification"
        )

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for real-time notifications"""
    logger.info("WebSocket connection attempt", user_id=user_id, client=websocket.client)
    await websocket.accept()
    
    # Verify user authentication
    try:
        user = await get_current_user_ws(websocket, user_id)
        if not user:
            await websocket.close(code=4001, reason="Authentication failed")
            return
    except Exception as e:
        logger.error("WebSocket authentication failed", user_id=user_id, error=str(e))
        await websocket.close(code=4001, reason="Authentication failed")
        return
    
    # Use the authenticated user's ID for the connection
    actual_user_id = user.id
    logger.info("Using authenticated user ID for WebSocket", requested_user_id=user_id, actual_user_id=actual_user_id)
    
    # Get WebSocket manager and create connection
    ws_manager = notification_service.get_websocket_manager()
    queue = await ws_manager.connect(actual_user_id)
    
    logger.info("WebSocket connection established", user_id=user_id)
    
    try:
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "WebSocket connection established",
            "user_id": actual_user_id,
            "timestamp": "2024-01-01T00:00:00Z"  # Placeholder
        }))
        
        # Keep connection alive and forward messages
        while True:
            try:
                # Wait for notification from queue
                message = await queue.get()
                await websocket.send_text(message)
                
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected", user_id=user_id)
                break
            except Exception as e:
                logger.error("WebSocket error", user_id=user_id, error=str(e))
                break
                
    except Exception as e:
        logger.error("WebSocket connection error", user_id=user_id, error=str(e))
    finally:
        # Clean up connection
        await ws_manager.disconnect(actual_user_id, queue)
        logger.info("WebSocket connection cleaned up", user_id=actual_user_id)

@router.get("/preferences", response_model=NotificationPreferences)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationPreferences:
    """Get current user's notification preferences"""
    return NotificationPreferences(
        email_notifications=current_user.email_notifications,
        webhook_url=current_user.webhook_url,
        event_notifications=current_user.event_notifications,
        camera_status_notifications=current_user.camera_status_notifications,
        system_alerts=current_user.system_alerts
    )

@router.put("/preferences", response_model=NotificationPreferences)
async def update_notification_preferences(
    preferences: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationPreferences:
    """Update current user's notification preferences"""
    try:
        # Update user preferences
        if preferences.email_notifications is not None:
            current_user.email_notifications = preferences.email_notifications
        
        if preferences.webhook_url is not None:
            current_user.webhook_url = preferences.webhook_url
            
        if preferences.event_notifications is not None:
            current_user.event_notifications = preferences.event_notifications
            
        if preferences.camera_status_notifications is not None:
            current_user.camera_status_notifications = preferences.camera_status_notifications
            
        if preferences.system_alerts is not None:
            current_user.system_alerts = preferences.system_alerts
        
        await db.commit()
        
        logger.info("Notification preferences updated", user_id=current_user.id)
        
        return NotificationPreferences(
            email_notifications=current_user.email_notifications,
            webhook_url=current_user.webhook_url,
            event_notifications=current_user.event_notifications,
            camera_status_notifications=current_user.camera_status_notifications,
            system_alerts=current_user.system_alerts
        )
        
    except Exception as e:
        logger.error("Failed to update notification preferences", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification preferences"
        )

@router.post("/test-email")
async def test_email_notification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a test email notification to the current user"""
    try:
        # Create a test notification payload
        from app.services.notification_service import NotificationPayload
        from datetime import datetime
        
        payload = NotificationPayload(
            type=NotificationType.SYSTEM_ALERT,
            title="Test Email Notification",
            message="This is a test email notification from Event Cam",
            data={"test": True},
            timestamp=datetime.now(),
            priority="normal",
            category="test"
        )
        
        # Send test email
        email_service = notification_service.email_service
        html_content = """
        <h2>Test Email Notification</h2>
                        <p>This is a test email notification from your Event Cam system.</p>
        <p>If you received this email, your email notification system is working correctly.</p>
        <p>Time: {timestamp}</p>
        """.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        success = await email_service.send_email(
            current_user.email,
            "Event Cam Test Email Notification",
            html_content
        )
        
        if success:
            return {"message": "Test email sent successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send test email"
            )
            
    except Exception as e:
        logger.error("Failed to send test email", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test email"
        )

@router.get("/status")
async def get_notification_status(
    current_user: User = Depends(get_current_user)
):
    """Get notification system status for the current user"""
    ws_manager = notification_service.get_websocket_manager()
    
    # Check if user has active WebSocket connections
    has_websocket_connection = current_user.id in ws_manager.active_connections
    
    return {
        "websocket_connected": has_websocket_connection,
        "email_enabled": current_user.email_notifications,
        "webhook_configured": bool(current_user.webhook_url),
        "active_connections": len(ws_manager.active_connections.get(current_user.id, set()))
    }

@router.post("/test")
async def test_notification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a test notification to the current user"""
    try:
        # Send test notification specifically to the current user
        await notification_service.send_system_alert(
            title="Event Cam System Test",
            message="Event Cam notification system is working correctly",
            priority="normal",
            users=[current_user]  # Send only to current user
        )
        
        logger.info("Test notification sent to current user", user_id=current_user.id)
        
        return {"message": "Test notification sent successfully"}
        
    except Exception as e:
        logger.error("Failed to send test notification", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification"
        ) 