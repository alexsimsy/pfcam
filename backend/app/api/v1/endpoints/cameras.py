from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
import structlog
import subprocess

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.models.user import User
from app.models.camera import Camera
from app.services.camera_client import CameraClient
from app.schemas.cameras import CameraResponse, CameraCreate, CameraUpdate, CameraStatus
from app.services.mediamtx_config import generate_mediamtx_config, write_mediamtx_config

logger = structlog.get_logger()
router = APIRouter()

@router.get("/", response_model=List[CameraResponse])
async def list_cameras(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_online: Optional[bool] = Query(None, description="Filter by online status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_cameras"))
) -> Any:
    """List all cameras with optional filtering"""
    
    query = select(Camera)
    
    if is_active is not None:
        query = query.where(Camera.is_active == is_active)
    
    if is_online is not None:
        query = query.where(Camera.is_online == is_online)
    
    result = await db.execute(query)
    cameras = result.scalars().all()
    
    return [CameraResponse.from_orm(camera) for camera in cameras]

@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_cameras"))
) -> Any:
    """Get specific camera details"""
    
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    return CameraResponse.from_orm(camera)

async def update_mediamtx_config_and_reload(db):
    # Fetch all cameras and their RTSP settings
    result = await db.execute(select(Camera))
    cameras = result.scalars().all()
    camera_dicts = []
    for cam in cameras:
        # Fetch RTSP settings from camera
        try:
            async with CameraClient(base_url=cam.base_url) as client:
                settings = await client.get_settings()
                camera_dicts.append({
                    'name': cam.name,
                    'ip_address': cam.ip_address,
                    'rtsp_port': settings.rtsp_port,
                    'rtsp_path': settings.rtsp_path,
                    'username': cam.username,
                    'password': cam.password,
                    'rtsp_auth': settings.rtsp_auth,
                })
        except Exception as e:
            # Skip cameras that are offline or misconfigured
            continue
    config = generate_mediamtx_config(camera_dicts)
    write_mediamtx_config(config)
    # Reload MediaMTX (docker restart)
    try:
        subprocess.run(["docker", "compose", "restart", "mediamtx"], check=True)
    except Exception as e:
        pass

@router.post("/", response_model=CameraResponse)
async def create_camera(
    camera_data: CameraCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_cameras"))
) -> Any:
    """Create a new camera"""
    
    # Check if camera with same IP already exists
    result = await db.execute(select(Camera).where(Camera.ip_address == camera_data.ip_address))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Camera with this IP address already exists"
        )
    
    # Test camera connection
    try:
        async with CameraClient(base_url=camera_data.base_url) as client:
            is_connected = await client.test_connection()
            if not is_connected:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot connect to camera at the specified URL"
                )
            
            # Get camera system info
            system_info = await client.get_system_info()
            
    except Exception as e:
        logger.error("Failed to test camera connection", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to connect to camera"
        )
    
    # Create camera record
    camera = Camera(
        name=camera_data.name,
        ip_address=camera_data.ip_address,
        port=camera_data.port,
        base_url=camera_data.base_url,
        username=camera_data.username,
        password=camera_data.password,
        use_ssl=camera_data.use_ssl,
        model=system_info.softwareVersion if system_info else None,
        is_online=True,
        last_seen=datetime.utcnow()
    )
    
    db.add(camera)
    await db.commit()
    await db.refresh(camera)
    
    # Check if auto-download is enabled and configure FTP automatically
    try:
        from app.models.settings import ApplicationSettings
        app_settings_result = await db.execute(select(ApplicationSettings).limit(1))
        app_settings = app_settings_result.scalar_one_or_none()
        
        if app_settings and app_settings.auto_download_events:
            logger.info(f"Auto-download enabled, configuring FTP for new camera {camera.id}")
            try:
                async with CameraClient(base_url=camera.base_url) as client:
                    await client.configure_ftp()
                    logger.info(f"FTP configured for new camera {camera.id} ({camera.name})")
            except Exception as e:
                logger.error(f"Failed to configure FTP for new camera {camera.id}", error=str(e))
                # Don't fail camera creation if FTP config fails
    except Exception as e:
        logger.error("Failed to check auto-download settings", error=str(e))
        # Don't fail camera creation if settings check fails
    
    logger.info("Camera created", camera_id=camera.id, name=camera.name)
    # Update MediaMTX config and reload
    await update_mediamtx_config_and_reload(db)
    
    return CameraResponse.from_orm(camera)

@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: int,
    camera_data: CameraUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_cameras"))
) -> Any:
    """Update camera settings"""
    
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    # Update fields
    update_data = camera_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(camera, field, value)
    
    await db.commit()
    await db.refresh(camera)
    
    logger.info("Camera updated", camera_id=camera.id, user_id=current_user.id)
    # Update MediaMTX config and reload
    await update_mediamtx_config_and_reload(db)
    
    return CameraResponse.from_orm(camera)

@router.delete("/{camera_id}")
async def delete_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_cameras"))
) -> Any:
    """Delete camera"""
    
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    # Check if camera has associated events
    from app.models.event import Event
    event_result = await db.execute(select(Event).where(Event.camera_id == camera_id))
    if event_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete camera with associated events"
        )
    
    await db.delete(camera)
    await db.commit()
    
    logger.info("Camera deleted", camera_id=camera_id, user_id=current_user.id)
    
    return {"message": "Camera deleted successfully"}

@router.get("/{camera_id}/status", response_model=CameraStatus)
async def get_camera_status(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_cameras"))
) -> Any:
    """Get camera status and health information"""
    
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    try:
        async with CameraClient(base_url=camera.base_url) as client:
            # Test connection
            is_connected = await client.test_connection()
            
            if is_connected:
                # Get system information
                system_info = await client.get_system_info()
                storage_info = await client.get_storage_info()
                
                # Update camera status
                camera.is_online = True
                camera.last_seen = datetime.utcnow()
                await db.commit()
                
                return CameraStatus(
                    camera_id=camera.id,
                    is_online=True,
                    last_seen=camera.last_seen,
                    system_info=system_info.dict() if system_info else None,
                    storage_info=storage_info,
                    connection_status="connected"
                )
            else:
                # Update camera status
                camera.is_online = False
                await db.commit()
                
                return CameraStatus(
                    camera_id=camera.id,
                    is_online=False,
                    last_seen=camera.last_seen,
                    connection_status="disconnected"
                )
                
    except Exception as e:
        logger.error("Failed to get camera status", camera_id=camera_id, error=str(e))
        
        # Update camera status
        camera.is_online = False
        await db.commit()
        
        return CameraStatus(
            camera_id=camera.id,
            is_online=False,
            last_seen=camera.last_seen,
            connection_status="error",
            error_message=str(e)
        )

@router.post("/{camera_id}/test")
async def test_camera_connection(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_cameras"))
) -> Any:
    """Test camera connection"""
    
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    try:
        async with CameraClient(base_url=camera.base_url) as client:
            is_connected = await client.test_connection()
            
            if is_connected:
                # Update camera status
                camera.is_online = True
                camera.last_seen = datetime.utcnow()
                await db.commit()
                
                return {
                    "status": "connected",
                    "message": "Camera connection successful",
                    "last_seen": camera.last_seen
                }
            else:
                # Update camera status
                camera.is_online = False
                await db.commit()
                
                return {
                    "status": "disconnected",
                    "message": "Camera connection failed"
                }
                
    except Exception as e:
        logger.error("Camera connection test failed", camera_id=camera_id, error=str(e))
        
        # Update camera status
        camera.is_online = False
        await db.commit()
        
        return {
            "status": "error",
            "message": f"Connection test failed: {str(e)}"
        }

@router.post("/{camera_id}/reboot")
async def reboot_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_system"))
) -> Any:
    """Reboot camera"""
    
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    try:
        async with CameraClient(base_url=camera.base_url) as client:
            success = await client.reboot_system()
            
            if success:
                # Update camera status
                camera.is_online = False
                camera.last_seen = datetime.utcnow()
                await db.commit()
                
                logger.info("Camera reboot initiated", camera_id=camera_id, user_id=current_user.id)
                return {"message": "Camera reboot initiated successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to reboot camera"
                )
                
    except Exception as e:
        logger.error("Failed to reboot camera", camera_id=camera_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reboot camera"
        )

@router.post("/{camera_id}/snapshot")
async def take_camera_snapshot(
    camera_id: int,
    stream_name: str = "hd",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_streams"))
) -> Any:
    """Take a direct snapshot from camera"""
    
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    try:
        async with CameraClient(base_url=camera.base_url) as client:
            # Take the snapshot
            snapshot_data = await client.take_snapshot(stream_name)
            
            # Return the image data with appropriate headers
            from fastapi.responses import Response
            return Response(
                content=snapshot_data,
                media_type="image/jpeg",
                headers={
                    "Content-Disposition": f"inline; filename=snapshot_{camera_id}_{stream_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
                }
            )
                
    except ValueError as e:
        logger.warning("Snapshot request failed", camera_id=camera_id, stream_name=stream_name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to take snapshot", camera_id=camera_id, stream_name=stream_name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to take snapshot"
        )

@router.post("/{camera_id}/trigger-event")
async def trigger_camera_event(
    camera_id: int,
    pre_event_seconds: int = Body(10),
    post_event_seconds: int = Body(10),
    event_name: str = Body("string"),
    overlay_text: str = Body("string"),
    stop_other_events: str = Body("none"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_cameras"))
) -> Any:
    """Trigger an event on the specified camera"""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    try:
        async with CameraClient(base_url=camera.base_url) as client:
            success = await client.trigger_event(
                pre_event_seconds,
                post_event_seconds,
                event_name,
                overlay_text,
                stop_other_events
            )
            if success:
                logger.info("Event triggered successfully", camera_id=camera_id, user_id=current_user.id)
                return {"message": "Event triggered successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to trigger event"
                )
    except Exception as e:
        logger.error("Failed to trigger event", camera_id=camera_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger event"
        )

@router.get("/{camera_id}/streams")
async def get_camera_streams(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_streams"))
) -> Any:
    """Get available camera streams"""
    
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    try:
        async with CameraClient(base_url=camera.base_url) as client:
            streams = await client.get_streams()
            
            return {
                "camera_id": camera_id,
                "streams": streams
            }
            
    except Exception as e:
        logger.error("Failed to get camera streams", camera_id=camera_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get camera streams"
        )

@router.post("/bulk/status")
async def get_bulk_camera_status(
    camera_ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_cameras"))
) -> Any:
    """Get status for multiple cameras"""
    
    result = await db.execute(select(Camera).where(Camera.id.in_(camera_ids)))
    cameras = result.scalars().all()
    
    status_results = []
    
    for camera in cameras:
        try:
            async with CameraClient(base_url=camera.base_url) as client:
                is_connected = await client.test_connection()
                
                if is_connected:
                    camera.is_online = True
                    camera.last_seen = datetime.utcnow()
                    status_results.append({
                        "camera_id": camera.id,
                        "name": camera.name,
                        "status": "online",
                        "last_seen": camera.last_seen
                    })
                else:
                    camera.is_online = False
                    status_results.append({
                        "camera_id": camera.id,
                        "name": camera.name,
                        "status": "offline",
                        "last_seen": camera.last_seen
                    })
                    
        except Exception as e:
            camera.is_online = False
            status_results.append({
                "camera_id": camera.id,
                "name": camera.name,
                "status": "error",
                "error": str(e)
            })
    
    await db.commit()
    
    return {
        "results": status_results,
        "total": len(status_results)
    }

@router.post("/refresh-mediamtx")
async def refresh_mediamtx(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_cameras"))
):
    """Manually refresh MediaMTX config and reload the service."""
    await update_mediamtx_config_and_reload(db)
    return {"message": "MediaMTX config refreshed and service reloaded."}

@router.post("/{camera_id}/refresh-mediamtx")
async def refresh_camera_mediamtx(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_cameras"))
):
    """Manually refresh MediaMTX config for a single camera and reload the service."""
    # Fetch all cameras
    result = await db.execute(select(Camera))
    cameras = result.scalars().all()
    camera_dicts = []
    for cam in cameras:
        if cam.id == camera_id:
            # Fetch RTSP settings from this camera
            try:
                async with CameraClient(base_url=cam.base_url) as client:
                    settings = await client.get_settings()
                    camera_dicts.append({
                        'name': cam.name,
                        'ip_address': cam.ip_address,
                        'rtsp_port': settings.rtsp_port,
                        'rtsp_path': settings.rtsp_path,
                        'username': cam.username,
                        'password': cam.password,
                        'rtsp_auth': settings.rtsp_auth,
                    })
            except Exception as e:
                continue
        else:
            # Use last known settings for other cameras
            try:
                async with CameraClient(base_url=cam.base_url) as client:
                    settings = await client.get_settings()
                    camera_dicts.append({
                        'name': cam.name,
                        'ip_address': cam.ip_address,
                        'rtsp_port': settings.rtsp_port,
                        'rtsp_path': settings.rtsp_path,
                        'username': cam.username,
                        'password': cam.password,
                        'rtsp_auth': settings.rtsp_auth,
                    })
            except Exception as e:
                continue
    config = generate_mediamtx_config(camera_dicts)
    write_mediamtx_config(config)
    # Reload MediaMTX (docker restart)
    try:
        subprocess.run(["docker", "compose", "restart", "mediamtx"], check=True)
    except Exception as e:
        pass
    return {"message": f"MediaMTX config refreshed for camera {camera_id} and service reloaded."}

@router.post("/{camera_id}/configure-ftp")
async def configure_camera_ftp(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_cameras"))
) -> Any:
    """Configure the camera's FTP settings to point to the backend FTP server."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    try:
        async with CameraClient(base_url=camera.base_url) as client:
            await client.configure_ftp()
            logger.info("Camera FTP configured via API", camera_id=camera_id)
            return {"message": "Camera FTP settings updated successfully"}
    except Exception as e:
        logger.error("Failed to configure camera FTP", camera_id=camera_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to configure camera FTP"
        )

@router.post("/configure-ftp-all")
async def configure_all_cameras_ftp(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_cameras"))
) -> Any:
    """Configure FTP settings on all active cameras."""
    try:
        # Get all active cameras
        cameras_result = await db.execute(
            select(Camera).where(Camera.is_active == True)
        )
        cameras = cameras_result.scalars().all()
        
        if not cameras:
            return {"message": "No active cameras found"}
        
        success_count = 0
        failed_count = 0
        failed_cameras = []
        
        for camera in cameras:
            try:
                async with CameraClient(base_url=camera.base_url) as client:
                    await client.configure_ftp()
                    logger.info(f"FTP configured for camera {camera.id} ({camera.name})")
                    success_count += 1
            except Exception as e:
                logger.error(f"Failed to configure FTP for camera {camera.id}", error=str(e))
                failed_count += 1
                failed_cameras.append({"id": camera.id, "name": camera.name, "error": str(e)})
        
        logger.info("Bulk FTP configuration completed", 
                   total=len(cameras), 
                   success=success_count, 
                   failed=failed_count)
        
        return {
            "message": f"FTP configuration completed for {success_count} cameras",
            "total_cameras": len(cameras),
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_cameras": failed_cameras
        }
        
    except Exception as e:
        logger.error("Failed to configure FTP on all cameras", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to configure FTP on all cameras"
        ) 