from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
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
from app.services.notification_service import notification_service

logger = structlog.get_logger()
router = APIRouter()

def normalize_filename(filename: str) -> str:
    """
    Normalize filename for comparison by removing common video extensions.
    This handles the mismatch between camera API (no extension) and FTP (with extension).
    """
    # Remove common video extensions
    extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
    base_name = filename.lower()
    for ext in extensions:
        if base_name.endswith(ext):
            return base_name[:-len(ext)]
    return base_name

def find_matching_event_by_filename(db_events: List[Event], target_filename: str) -> Optional[Event]:
    """
    Find an event that matches the target filename, accounting for extension differences.
    """
    normalized_target = normalize_filename(target_filename)
    
    for event in db_events:
        normalized_event = normalize_filename(event.filename)
        if normalized_event == normalized_target:
            return event
    
    return None

@router.get("/", response_model=EventList)
async def list_events(
    camera_id: Optional[int] = Query(None, description="Filter by camera ID"),
    event_name: Optional[str] = Query(None, description="Filter by event name"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    tag_ids: Optional[str] = Query(None, description="Comma-separated list of tag IDs to filter by"),
    is_played: Optional[bool] = Query(None, description="Filter by played status"),
    limit: int = Query(50, le=100, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    sort_by: str = Query("triggered_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    show_orphaned: bool = Query(False, description="Show events that are not on camera and not downloaded locally"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_events"))
) -> Any:
    """List events with filtering and pagination, excluding deleted events"""
    
    # Build query with camera information and tags
    query = select(Event, Camera.name.label('camera_name')).join(Camera).where(Event.is_deleted == False)
    query = query.options(selectinload(Event.tags))
    
    # Apply filters
    if camera_id:
        query = query.where(Event.camera_id == camera_id)
    
    if event_name:
        query = query.where(Event.event_name.ilike(f"%{event_name}%"))
    
    if start_date:
        query = query.where(Event.triggered_at >= start_date)
    
    if end_date:
        query = query.where(Event.triggered_at <= end_date)
    
    # Filter by played status
    if is_played is not None:
        query = query.where(Event.is_played == is_played)
    
    # Filter by tags
    if tag_ids:
        tag_id_list = [int(tid.strip()) for tid in tag_ids.split(',') if tid.strip().isdigit()]
        if tag_id_list:
            # Filter events that have any of the specified tags
            from app.models.tag import event_tags
            query = query.join(event_tags).where(event_tags.c.tag_id.in_(tag_id_list))
    
    # Filter out orphaned events (not on camera and not downloaded locally) unless explicitly requested
    if not show_orphaned:
        # Only show events that are not marked as orphaned
        query = query.where(Event.is_orphaned == False)
    
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
    events_with_camera = result.all()
    
    # Process results to include camera names
    events = []
    for event_row in events_with_camera:
        event = event_row[0]  # Event object
        event.camera_name = event_row[1]  # Camera name
        events.append(event)
    
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
    
    # Apply same filters to count query
    if is_played is not None:
        count_query = count_query.where(Event.is_played == is_played)
    
    if tag_ids:
        tag_id_list = [int(tid.strip()) for tid in tag_ids.split(',') if tid.strip().isdigit()]
        if tag_id_list:
            from app.models.tag import event_tags
            count_query = count_query.join(event_tags).where(event_tags.c.tag_id.in_(tag_id_list))
    
    # Apply same orphaned filter to count query
    if not show_orphaned:
        count_query = count_query.where(Event.is_orphaned == False)
    
    count_result = await db.execute(count_query)
    total_count = len(count_result.scalars().all())
    
    return EventList(
        events=[EventResponse(
            **{**event.__dict__, "triggered_at": str(event.triggered_at) if event.triggered_at is not None else None}
        ) for event in events],
        total=total_count,
        limit=limit,
        offset=offset
    )

@router.get("/orphaned", response_model=EventList)
async def list_orphaned_events(
    camera_id: Optional[int] = Query(None, description="Filter by camera ID"),
    limit: int = Query(50, le=100, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_events"))
) -> Any:
    """List orphaned events (not on camera and not downloaded locally)"""
    
    # Build query for orphaned events with camera information and tags
    query = select(Event, Camera.name.label('camera_name')).join(Camera).where(Event.is_deleted == False)
    query = query.options(selectinload(Event.tags))
    
    # Apply camera filter
    if camera_id:
        query = query.where(Event.camera_id == camera_id)
    
    # Filter for orphaned events (marked as orphaned)
    query = query.where(Event.is_orphaned == True)
    
    # Apply sorting (most recent first)
    query = query.order_by(desc(Event.triggered_at))
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    events_with_camera = result.all()
    
    # Process results to include camera names
    events = []
    for event_row in events_with_camera:
        event = event_row[0]  # Event object
        event.camera_name = event_row[1]  # Camera name
        events.append(event)
    
    # Get total count
    count_query = select(Event).where(Event.is_deleted == False)
    if camera_id:
        count_query = count_query.where(Event.camera_id == camera_id)
    count_query = count_query.where(Event.is_orphaned == True)
    
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
    
    return EventResponse(
        **{**event.__dict__, "triggered_at": str(event.triggered_at) if event.triggered_at is not None else None}
    )

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
            # Construct proper filename with extension
            download_filename = event.filename
            if event.video_extension and not download_filename.endswith(event.video_extension):
                download_filename += event.video_extension
            
            return StreamingResponse(
                open(event.file_path, "rb"),
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={download_filename}"}
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
            # Construct proper filename with extension
            download_filename = event.filename
            if event.video_extension and not download_filename.endswith(event.video_extension):
                download_filename += event.video_extension
            
            return StreamingResponse(
                io.BytesIO(file_data),
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={download_filename}"}
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
    logger.info("/sync endpoint called", camera_id=camera_id)
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
                    
                    # Get all events to check for duplicates across cameras using normalized filenames
                    all_events_result = await db.execute(select(Event))
                    all_existing_events = list(all_events_result.scalars().all())
                    
                    # Process new events
                    new_events = []
                    for camera_event in camera_events:
                        # Check if event exists in this camera's events (exact match)
                        if camera_event.fileName not in existing_events:
                            # Check if event exists in any camera using normalized filename comparison
                            matching_event = find_matching_event_by_filename(all_existing_events, camera_event.fileName)
                            
                            if not matching_event:
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
                                logger.info("Created new event from camera", filename=camera_event.fileName, camera_id=camera.id)
                            else:
                                # Event exists in another camera, update the existing record if needed
                                logger.info("Event already exists, skipping duplicate", 
                                          filename=camera_event.fileName, existing_camera_id=matching_event.camera_id, new_camera_id=camera.id)
                                
                                # Update the existing event with camera information if it's missing
                                if not matching_event.event_name and camera_event.eventName:
                                    matching_event.event_name = camera_event.eventName
                                if not matching_event.video_extension and camera_event.vidExt:
                                    matching_event.video_extension = camera_event.vidExt
                                if not matching_event.thumbnail_extension and camera_event.thmbExt:
                                    matching_event.thumbnail_extension = camera_event.thmbExt
                                if not matching_event.playback_time and camera_event.playbackTime:
                                    matching_event.playback_time = camera_event.playbackTime
                    
                    # Add new events to database
                    if new_events:
                        db.add_all(new_events)
                        total_new_events += len(new_events)
                        logger.info("Events synced for camera", camera_id=camera.id, new_count=len(new_events))
                        
                        # Send notifications for new events
                        try:
                            # Get all users for notifications
                            users_result = await db.execute(select(User).where(User.is_active == True))
                            users = users_result.scalars().all()
                            
                            # Send notifications for each new event
                            for event in new_events:
                                await notification_service.send_event_notification(event, camera, users)
                                
                        except Exception as e:
                            logger.error("Failed to send event notifications", camera_id=camera.id, error=str(e))
                        
            except Exception as e:
                logger.error("Exception in camera sync loop", camera_id=camera.id, error=str(e))
                continue
        
        # Commit all changes
        await db.commit()
        logger.info("Camera sync section complete, entering FTP sync section")

        # 2. Sync from FTP directory - now using filename as unique key
        ftp_dir = os.path.abspath(os.path.join(os.getcwd(), "ftpdata"))
        ftp_files_processed = 0
        ftp_files_updated = 0
        ftp_files_created = 0
        logger.info("FTP sync: entering FTP sync section", ftp_dir=ftp_dir)
        if os.path.exists(ftp_dir):
            logger.info("FTP sync: directory exists", ftp_dir=ftp_dir)
            try:
                files_in_dir = os.listdir(ftp_dir)
                logger.info("FTP sync: files in directory", files_count=len(files_in_dir), files=files_in_dir)
                for fname in files_in_dir:
                    if not fname.lower().endswith((".mp4", ".avi", ".mov")):
                        logger.info("FTP sync: skipping non-video file", filename=fname)
                        continue
                    file_path = os.path.join(ftp_dir, fname)
                    logger.info("FTP sync: found file", filename=fname, file_path=file_path)
                    
                    # Get all events to check for duplicates using normalized filenames
                    all_events_result = await db.execute(select(Event))
                    all_existing_events = list(all_events_result.scalars().all())
                    
                    # Check if event already exists by normalized filename
                    matching_event = find_matching_event_by_filename(all_existing_events, fname)
                    
                    if matching_event:
                        # Update existing event with FTP file information
                        matching_event.file_path = file_path
                        matching_event.is_downloaded = True
                        # Update file size if available
                        try:
                            matching_event.file_size = os.path.getsize(file_path)
                        except OSError:
                            pass
                        await db.commit()
                        logger.info("FTP sync: updated existing event", event_id=matching_event.id, filename=fname, normalized=normalize_filename(fname))
                        ftp_files_updated += 1
                    else:
                        # Create new event only if it doesn't exist anywhere
                        # Try to determine which camera this file belongs to based on filename patterns
                        # Look for camera name patterns in the filename
                        camera_result = await db.execute(select(Camera))
                        all_cameras = camera_result.scalars().all()
                        
                        # Try to match filename to camera name
                        matched_camera = None
                        for camera in all_cameras:
                            if camera.name.lower() in fname.lower():
                                matched_camera = camera
                                break
                        
                        # If no match found, use the first camera or fallback to 1
                        if not matched_camera and all_cameras:
                            matched_camera = all_cameras[0]
                        
                        event = Event(
                            filename=fname,
                            file_path=file_path,
                            is_downloaded=True,
                            camera_id=matched_camera.id if matched_camera else 1,  # Use matched camera or fallback to 1
                            event_name="Motion Event",
                            triggered_at=datetime.now()
                        )
                        db.add(event)
                        await db.commit()
                        logger.info("FTP sync: created new event", event_id=event.id, filename=fname)
                        ftp_files_created += 1
                        
                        # Send notifications for FTP events
                        try:
                            # Get camera for the event (default camera ID 1)
                            camera_result = await db.execute(select(Camera).where(Camera.id == event.camera_id))
                            camera = camera_result.scalar_one_or_none()
                            
                            if camera:
                                # Get all users for notifications
                                users_result = await db.execute(select(User).where(User.is_active == True))
                                users = users_result.scalars().all()
                                
                                # Send notification for the new FTP event
                                await notification_service.send_event_notification(event, camera, users)
                                
                        except Exception as e:
                            logger.error("Failed to send FTP event notifications", event_id=event.id, error=str(e))
                    ftp_files_processed += 1
            except Exception as e:
                logger.error("FTP sync: exception in FTP sync loop", error=str(e), exc_info=True)
        else:
            logger.warning("FTP sync: directory does not exist", ftp_dir=ftp_dir)
        
        logger.info("FTP sync: summary", processed=ftp_files_processed, updated=ftp_files_updated, created=ftp_files_created)

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
        # Mark as downloaded and played
        if not event.is_downloaded:
            event.is_downloaded = True
        if not event.is_played:
            event.is_played = True
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
    # Check in FTP directory
    ftp_dir = os.path.abspath(os.path.join(os.getcwd(), "ftpdata"))
    in_ftp = False
    if os.path.exists(ftp_dir):
        ftp_file_path = os.path.join(ftp_dir, event.filename)
        in_ftp = os.path.exists(ftp_file_path)
    
    # Update event status
    event.is_downloaded = on_server
    # Mark as orphaned if not on camera and not downloaded
    event.is_orphaned = not on_camera and not on_server
    await db.commit()
    
    # Return clear status information
    return {
        "on_server": on_server,
        "on_camera": on_camera, 
        "in_ftp": in_ftp,
        "is_downloaded": on_server,
        "is_orphaned": not on_camera and not on_server
    }

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