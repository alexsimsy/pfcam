from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from datetime import datetime, timedelta
import structlog
import io
import os

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
    """List events with filtering and pagination, excluding deleted events"""
    
    # Build query
    query = select(Event).join(Camera).where(Event.is_deleted == False)
    
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
        if os.path.exists(event.file_path):
            return StreamingResponse(
                open(event.file_path, "rb"),
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={event.filename}"}
            )
    
    # Download from camera if not available locally
    try:
        # Get camera details for the event
        camera_result = await db.execute(select(Camera).where(Camera.id == event.camera_id))
        camera = camera_result.scalar_one_or_none()
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found for this event"
            )
        
        async with CameraClient(base_url=camera.base_url) as client:
            file_data = await client.get_event_file(event.filename)
            
            # If the camera API returns an error (dict), handle gracefully
            if not isinstance(file_data, bytes):
                logger.error("Camera API did not return file bytes", event_id=event_id, response=file_data)
                raise HTTPException(
                    status_code=502,
                    detail=f"Camera API error: {file_data.get('error') if isinstance(file_data, dict) else str(file_data)}"
                )
            # Store file locally
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
        # Get camera details for the event
        camera_result = await db.execute(select(Camera).where(Camera.id == event.camera_id))
        camera = camera_result.scalar_one_or_none()
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found for this event"
            )
        
        # Delete from camera
        async with CameraClient(base_url=camera.base_url) as client:
            await client.delete_event(event.filename)
        
        # Delete local files
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
    """Sync events from camera API and FTP directory to database"""
    try:
        # 1. Sync from camera API (existing logic)
        # If camera_id is provided, get the camera details
        if camera_id:
            camera_result = await db.execute(select(Camera).where(Camera.id == camera_id))
            camera = camera_result.scalar_one_or_none()
            if not camera:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Camera not found"
                )
            cameras = [camera]
        else:
            # Get all cameras
            camera_result = await db.execute(select(Camera))
            cameras = camera_result.scalars().all()
            if not cameras:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No cameras found in database"
                )
        
        total_new_events = 0
        total_camera_events = 0
        
        for camera in cameras:
            try:
                async with CameraClient(base_url=camera.base_url) as client:
                    # Get events from camera
                    camera_events = await client.get_events()
                    total_camera_events += len(camera_events)
                    
                    # Get existing events from database for this camera
                    result = await db.execute(select(Event).where(Event.camera_id == camera.id))
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
                                logger.warning("Invalid date format", triggered_at=camera_event.triggeredAt, camera_id=camera.id)
                                continue
                            
                            # Create new event record
                            event = Event(
                                camera_id=camera.id,
                                filename=camera_event.fileName,
                                event_name=camera_event.eventName,
                                triggered_at=triggered_at,
                                video_extension=camera_event.vidExt,
                                thumbnail_extension=camera_event.thmbExt,
                                playback_time=camera_event.playbackTime,
                                event_metadata={
                                    "age": camera_event.age,
                                    "dir": camera_event.dir
                                }
                            )
                            new_events.append(event)
                    
                    # Add new events to database
                    if new_events:
                        db.add_all(new_events)
                        total_new_events += len(new_events)
                        logger.info("Events synced for camera", camera_id=camera.id, new_count=len(new_events))
                        
            except Exception as e:
                logger.error("Failed to sync events for camera", camera_id=camera.id, error=str(e))
                # Continue with other cameras even if one fails
                continue
        
        # Commit all changes
        await db.commit()

        # 2. Sync from FTP directory
        ftp_dir = os.path.abspath(os.path.join(os.getcwd(), "ftpdata"))
        if os.path.exists(ftp_dir):
            for fname in os.listdir(ftp_dir):
                if not fname.lower().endswith(('.mp4', '.avi', '.mov')):
                    continue
                file_path = os.path.join(ftp_dir, fname)
                # Check if event already exists
                result = await db.execute(select(Event).where(Event.filename == fname))
                event = result.scalar_one_or_none()
                if not event:
                    # Create a new event record with minimal info
                    event = Event(
                        filename=fname,
                        event_name=None,
                        triggered_at=datetime.fromtimestamp(os.path.getmtime(file_path)),
                        file_path=file_path,
                        is_downloaded=True,
                        is_deleted=False
                    )
                    db.add(event)
            await db.commit()

        return {
            "message": "Events synced from camera and FTP directory",
            "new_events": total_new_events,
            "total_events": total_camera_events,
            "cameras_processed": len(cameras)
        }
    except Exception as e:
        logger.error("Failed to sync events", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync events"
        )

@router.get("/active/list")
async def list_active_events(
    camera_id: Optional[int] = Query(None, description="Get active events for specific camera"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_events"))
) -> Any:
    """List currently active events from camera"""
    
    try:
        # If camera_id is provided, get the camera details
        if camera_id:
            camera_result = await db.execute(select(Camera).where(Camera.id == camera_id))
            camera = camera_result.scalar_one_or_none()
            if not camera:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Camera not found"
                )
            cameras = [camera]
        else:
            # Get all cameras
            camera_result = await db.execute(select(Camera))
            cameras = camera_result.scalars().all()
            if not cameras:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No cameras found in database"
                )
        
        all_active_events = []
        
        for camera in cameras:
            try:
                async with CameraClient(base_url=camera.base_url) as client:
                    active_events = await client.get_active_events()
                    
                    for event in active_events:
                        all_active_events.append({
                            "camera_id": camera.id,
                            "camera_name": camera.name,
                            "filename": event.fileName,
                            "event_name": event.eventName,
                            "triggered_at": event.triggeredAt,  # Already a string from camera API
                            "age": event.age
                        })
                        
            except Exception as e:
                logger.error("Failed to get active events for camera", camera_id=camera.id, error=str(e))
                # Continue with other cameras even if one fails
                continue
        
        return {
            "active_events": all_active_events,
            "count": len(all_active_events)
        }
        
    except Exception as e:
        logger.error("Failed to get active events", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active events"
        )

@router.delete("/active/stop")
async def stop_all_active_events(
    camera_id: Optional[int] = Query(None, description="Stop active events for specific camera"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_system"))
) -> Any:
    """Stop all active events"""
    
    try:
        # If camera_id is provided, get the camera details
        if camera_id:
            camera_result = await db.execute(select(Camera).where(Camera.id == camera_id))
            camera = camera_result.scalar_one_or_none()
            if not camera:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Camera not found"
                )
            cameras = [camera]
        else:
            # Get all cameras
            camera_result = await db.execute(select(Camera))
            cameras = camera_result.scalars().all()
            if not cameras:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No cameras found in database"
                )
        
        stopped_cameras = []
        failed_cameras = []
        
        for camera in cameras:
            try:
                async with CameraClient(base_url=camera.base_url) as client:
                    await client.stop_all_active_events()
                    stopped_cameras.append(camera.id)
                    logger.info("Active events stopped for camera", camera_id=camera.id, user_id=current_user.id)
                    
            except Exception as e:
                logger.error("Failed to stop active events for camera", camera_id=camera.id, error=str(e))
                failed_cameras.append(camera.id)
                continue
        
        if failed_cameras:
            return {
                "message": "Active events stopped with some failures",
                "stopped_cameras": stopped_cameras,
                "failed_cameras": failed_cameras
            }
        else:
            return {
                "message": "All active events stopped successfully",
                "stopped_cameras": stopped_cameras
            }
            
    except Exception as e:
        logger.error("Failed to stop active events", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop active events"
        )

@router.delete("/{event_id}/local")
async def delete_event_local(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("delete_events"))
) -> Any:
    """Delete event file from local storage only (not from camera, not marking as deleted)."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    if event.file_path and os.path.exists(event.file_path):
        os.remove(event.file_path)
        event.file_path = None
        event.is_downloaded = False
        await db.commit()
        return {"message": "Event file deleted from local storage"}
    else:
        return {"message": "No local file to delete"}

@router.get("/{event_id}/play")
async def play_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_events"))
) -> Any:
    """Stream event video for playback (from local storage only)."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    if event.file_path and os.path.exists(event.file_path):
        if not event.is_downloaded:
            event.is_downloaded = True
            await db.commit()
        # Guess content type based on extension
        import mimetypes
        mime_type, _ = mimetypes.guess_type(event.filename)
        if not mime_type:
            mime_type = "application/octet-stream"
        return FileResponse(event.file_path, media_type=mime_type, filename=event.filename)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Local event file not found"
        )

@router.get("/{event_id}/sync-status")
async def get_event_sync_status(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_events"))
) -> Any:
    """Return sync status for an event: present on server (FTP/local) and on camera."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    on_server = bool(event.file_path and os.path.exists(event.file_path))
    # Check on camera
    camera_result = await db.execute(select(Camera).where(Camera.id == event.camera_id))
    camera = camera_result.scalar_one_or_none()
    on_camera = False
    if camera:
        try:
            async with CameraClient(base_url=camera.base_url) as client:
                camera_events = await client.get_events()
                on_camera = any(e.fileName == event.filename for e in camera_events)
        except Exception as e:
            logger.warning("Failed to check event on camera", event_id=event_id, error=str(e))
    event.is_downloaded = on_server
    await db.commit()
    return {"on_server": on_server, "on_camera": on_camera}

@router.get("/{event_id}/refresh")
async def refresh_event_sync_status(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_events"))
) -> Any:
    """Re-check and update the is_downloaded (Sync) status in the database based on file presence."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    on_server = bool(event.file_path and os.path.exists(event.file_path))
    event.is_downloaded = on_server
    await db.commit()
    return {"on_server": on_server} 