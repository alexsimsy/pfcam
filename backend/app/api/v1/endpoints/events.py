from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from datetime import datetime, timedelta
import structlog
import io

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.models.user import User
from app.models.event import Event
from app.models.camera import Camera
from app.services.camera_client import CameraClient, CameraEvent
from app.schemas.events import EventResponse, EventList, EventDownload

logger = structlog.get_logger()
router = APIRouter()

@router.get("/", response_model=EventList)
async def list_events(
    camera_id: Optional[int] = Query(None, description="Filter by camera ID"),
    event_name: Optional[str] = Query(None, description="Filter by event name"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(50, le=100, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    sort_by: str = Query("triggered_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_events"))
) -> Any:
    """List events with filtering and pagination"""
    
    # Build query
    query = select(Event).join(Camera)
    
    # Apply filters
    if camera_id:
        query = query.where(Event.camera_id == camera_id)
    
    if event_name:
        query = query.where(Event.event_name.ilike(f"%{event_name}%"))
    
    if start_date:
        query = query.where(Event.triggered_at >= start_date)
    
    if end_date:
        query = query.where(Event.triggered_at <= end_date)
    
    # Apply sorting
    if sort_by == "triggered_at":
        if sort_order == "desc":
            query = query.order_by(desc(Event.triggered_at))
        else:
            query = query.order_by(Event.triggered_at)
    elif sort_by == "filename":
        if sort_order == "desc":
            query = query.order_by(desc(Event.filename))
        else:
            query = query.order_by(Event.filename)
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    events = result.scalars().all()
    
    # Get total count
    count_query = select(Event)
    if camera_id:
        count_query = count_query.where(Event.camera_id == camera_id)
    if event_name:
        count_query = count_query.where(Event.event_name.ilike(f"%{event_name}%"))
    if start_date:
        count_query = count_query.where(Event.triggered_at >= start_date)
    if end_date:
        count_query = count_query.where(Event.triggered_at <= end_date)
    
    count_result = await db.execute(count_query)
    total_count = len(count_result.scalars().all())
    
    return EventList(
        events=[EventResponse.from_orm(event) for event in events],
        total=total_count,
        limit=limit,
        offset=offset
    )

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_events"))
) -> Any:
    """Get specific event details"""
    
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    return EventResponse.from_orm(event)

@router.get("/{event_id}/download")
async def download_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("download_events"))
) -> Any:
    """Download event file (image/video)"""
    
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if file exists locally
    if event.file_path and event.is_downloaded:
        # Return local file
        import os
        if os.path.exists(event.file_path):
            return StreamingResponse(
                open(event.file_path, "rb"),
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={event.filename}"}
            )
    
    # Download from camera if not available locally
    try:
        async with CameraClient() as client:
            file_data = await client.get_event_file(event.filename)
            
            # If the camera API returns an error (dict), handle gracefully
            if not isinstance(file_data, bytes):
                logger.error("Camera API did not return file bytes", event_id=event_id, response=file_data)
                raise HTTPException(
                    status_code=502,
                    detail=f"Camera API error: {file_data.get('error') if isinstance(file_data, dict) else str(file_data)}"
                )
            # Store file locally
            import os
            from app.core.config import settings
            
            # Create directory structure
            file_dir = os.path.join(settings.STORAGE_PATH, "events", str(event.camera_id))
            os.makedirs(file_dir, exist_ok=True)
            
            file_path = os.path.join(file_dir, event.filename)
            with open(file_path, "wb") as f:
                f.write(file_data)
            
            # Update event record
            event.file_path = file_path
            event.is_downloaded = True
            event.file_size = len(file_data)
            await db.commit()
            
            # Return file
            return StreamingResponse(
                io.BytesIO(file_data),
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={event.filename}"}
            )
            
    except Exception as e:
        logger.error("Failed to download event file", event_id=event_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download event file"
        )

@router.get("/{event_id}/thumbnail")
async def get_event_thumbnail(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_events"))
) -> Any:
    """Get event thumbnail"""
    
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if thumbnail exists locally
    if event.thumbnail_path:
        import os
        if os.path.exists(event.thumbnail_path):
            return StreamingResponse(
                open(event.thumbnail_path, "rb"),
                media_type="image/jpeg"
            )
    
    # Generate thumbnail from video/image if needed
    # This would require additional image processing logic
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Thumbnail not available"
    )

@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("delete_events"))
) -> Any:
    """Delete event and associated files"""
    
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    try:
        # Delete from camera
        async with CameraClient() as client:
            await client.delete_event(event.filename)
        
        # Delete local files
        import os
        if event.file_path and os.path.exists(event.file_path):
            os.remove(event.file_path)
        
        if event.thumbnail_path and os.path.exists(event.thumbnail_path):
            os.remove(event.thumbnail_path)
        
        # Mark as deleted in database
        event.is_deleted = True
        await db.commit()
        
        logger.info("Event deleted", event_id=event_id, user_id=current_user.id)
        
        return {"message": "Event deleted successfully"}
        
    except Exception as e:
        logger.error("Failed to delete event", event_id=event_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete event"
        )

@router.post("/sync")
async def sync_events(
    camera_id: Optional[int] = Query(None, description="Sync events for specific camera"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_events"))
) -> Any:
    """Sync events from camera to database"""
    
    try:
        async with CameraClient() as client:
            # Get events from camera
            camera_events = await client.get_events()
            
            # Get existing events from database
            if camera_id:
                result = await db.execute(select(Event).where(Event.camera_id == camera_id))
            else:
                result = await db.execute(select(Event))
            
            existing_events = {event.filename: event for event in result.scalars().all()}
            
            # Process new events
            new_events = []
            for camera_event in camera_events:
                if camera_event.fileName not in existing_events:
                    # Parse triggeredAt string to datetime
                    try:
                        triggered_at = datetime.fromisoformat(camera_event.triggeredAt)
                    except ValueError:
                        # Handle different date formats if needed
                        logger.warning("Invalid date format", triggered_at=camera_event.triggeredAt)
                        continue
                    
                    # Create new event record
                    event = Event(
                        camera_id=camera_id or 1,  # Default to first camera
                        filename=camera_event.fileName,
                        event_name=camera_event.eventName,
                        triggered_at=triggered_at,
                        video_extension=camera_event.vidExt,
                        thumbnail_extension=camera_event.thmbExt,
                        playback_time=camera_event.playbackTime,
                        metadata={
                            "age": camera_event.age,
                            "dir": camera_event.dir
                        }
                    )
                    new_events.append(event)
            
            # Add new events to database
            if new_events:
                db.add_all(new_events)
                await db.commit()
                logger.info("Events synced", new_count=len(new_events))
            
            return {
                "message": "Events synced successfully",
                "new_events": len(new_events),
                "total_events": len(camera_events)
            }
            
    except Exception as e:
        logger.error("Failed to sync events", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync events"
        )

@router.get("/active/list")
async def list_active_events(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_events"))
) -> Any:
    """List currently active events from camera"""
    
    try:
        async with CameraClient() as client:
            active_events = await client.get_active_events()
            
            return {
                "active_events": [
                    {
                        "filename": event.fileName,
                        "event_name": event.eventName,
                        "triggered_at": event.triggeredAt,  # Already a string from camera API
                        "age": event.age
                    }
                    for event in active_events
                ],
                "count": len(active_events)
            }
            
    except Exception as e:
        logger.error("Failed to get active events", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active events"
        )

@router.delete("/active/stop")
async def stop_all_active_events(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_system"))
) -> Any:
    """Stop all active events"""
    
    try:
        async with CameraClient() as client:
            await client.stop_all_active_events()
            
            logger.info("All active events stopped", user_id=current_user.id)
            
            return {"message": "All active events stopped successfully"}
            
    except Exception as e:
        logger.error("Failed to stop active events", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop active events"
        ) 