from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.models.user import User
from app.models.camera import Camera
from app.models.settings import CameraSettings as DBCameraSettings, ApplicationSettings
from app.services.camera_client import CameraClient, CameraSettings
from app.services.data_retention import cleanup_old_data, get_retention_stats
from app.schemas.settings import SettingsResponse, SettingsUpdate, SettingsReset, ApplicationSettingsResponse, ApplicationSettingsUpdate

logger = structlog.get_logger()
router = APIRouter()

@router.get("/{camera_id}", response_model=SettingsResponse)
async def get_camera_settings(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_settings"))
) -> Any:
    """Get camera settings directly from camera (always fresh)"""
    
    # Get camera
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    # Always fetch fresh settings from camera
    try:
        async with CameraClient(base_url=camera.base_url) as client:
            settings = await client.get_settings()
            settings_dict = settings.dict()
            
            logger.info("Fetched fresh camera settings", camera_id=camera_id, settings_count=len(settings_dict))
            
            # Update database with fresh settings
            db_settings = await db.execute(
                select(DBCameraSettings).where(DBCameraSettings.camera_id == camera_id)
            )
            db_setting = db_settings.scalar_one_or_none()
            
            if db_setting:
                db_setting.settings_data = settings_dict
                db_setting.settings_version = "1.0"
            else:
                db_setting = DBCameraSettings(
                    camera_id=camera_id,
                    settings_data=settings_dict,
                    settings_version="1.0"
                )
                db.add(db_setting)
            
            await db.commit()
            
            return SettingsResponse(
                camera_id=camera_id,
                settings=settings_dict,
                version="1.0"
            )
            
    except Exception as e:
        logger.error("Failed to get camera settings", camera_id=camera_id, error=str(e))
        # If camera is unavailable, return empty settings with defaults
        default_settings = {
            "live_quality_level": 50,
            "recording_quality_level": 50,
            "heater_level": 0,
            "picture_rotation": 90,
            "pre_event_recording_seconds": 10,
            "post_event_recording_seconds": 10
        }
        
        return SettingsResponse(
            camera_id=camera_id,
            settings=default_settings,
            version="1.0"
        )

@router.put("/{camera_id}", response_model=SettingsResponse)
async def update_camera_settings(
    camera_id: int,
    settings_data: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_settings"))
) -> Any:
    """Update camera settings"""
    
    # Get camera
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    try:
        async with CameraClient(base_url=camera.base_url) as client:
            # Get current camera settings first to preserve existing settings
            try:
                current_camera_settings = await client.get_settings()
                current_settings_dict = current_camera_settings.dict()
                logger.info("Retrieved current camera settings", camera_id=camera_id, settings_count=len(current_settings_dict))
            except Exception as e:
                logger.error("Could not get current camera settings", camera_id=camera_id, error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get current camera settings: {str(e)}"
                )
            
            # Only update the fields that were sent
            update_data = settings_data.dict(exclude_unset=True)
            logger.info("Updating camera settings", camera_id=camera_id, update_fields=list(update_data.keys()))
            
            # Update only the specific fields in the current settings
            for field, value in update_data.items():
                if field in current_settings_dict:
                    current_settings_dict[field] = value
                    logger.info(f"Updated field {field} from {current_settings_dict.get(field)} to {value}")
                else:
                    logger.warning(f"Field {field} not found in camera settings, skipping")
            
            # Send complete settings back to camera
            response = await client._make_request("PUT", "/system/settings", json=current_settings_dict)
            
            # Camera will restart after settings update, so we can't fetch updated settings immediately
            # Instead, we'll store the merged settings and return a success response
            logger.info("Camera settings update sent, camera may restart", camera_id=camera_id, user_id=current_user.id, updated_fields=list(update_data.keys()))
            
            # Store the complete updated settings in database
            db_settings = await db.execute(
                select(DBCameraSettings).where(DBCameraSettings.camera_id == camera_id)
            )
            db_setting = db_settings.scalar_one_or_none()
            
            if db_setting:
                # Update with complete settings
                db_setting.settings_data = current_settings_dict
                db_setting.settings_version = "1.0"
            else:
                # Create new settings record with the complete settings
                db_setting = DBCameraSettings(
                    camera_id=camera_id,
                    settings_data=current_settings_dict,
                    settings_version="1.0"
                )
                db.add(db_setting)
            
            await db.commit()
            
            return SettingsResponse(
                camera_id=camera_id,
                settings=current_settings_dict,  # Return the complete updated settings
                version="1.0"
            )
            
    except Exception as e:
        logger.error("Failed to update camera settings", camera_id=camera_id, error=str(e))
        # Check if the error is due to camera restart (empty response or connection error)
        error_msg = str(e)
        if "Expecting value" in error_msg or "connection" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,  # Accepted but processing
                detail="Settings update sent to camera. Camera is restarting and may be unavailable for up to 1 minute."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update camera settings: {str(e)}"
            )

@router.get("/cameras/all", response_model=Dict[str, Any])
async def get_all_cameras_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_settings"))
) -> Any:
    """Get settings for all cameras from database"""
    
    # Get all cameras
    cameras_result = await db.execute(select(Camera))
    cameras = cameras_result.scalars().all()
    
    # Get settings for all cameras
    all_settings = {}
    for camera in cameras:
        db_settings = await db.execute(
            select(DBCameraSettings).where(DBCameraSettings.camera_id == camera.id)
        )
        db_setting = db_settings.scalar_one_or_none()
        
        if db_setting and db_setting.settings_data:
            all_settings[str(camera.id)] = db_setting.settings_data
        else:
            # Return default settings if none stored
            all_settings[str(camera.id)] = {
                "live_quality_level": 50,
                "recording_quality_level": 50,
                "heater_level": 0,
                "picture_rotation": 90,
                "pre_event_recording_seconds": 10,
                "post_event_recording_seconds": 10
            }
    
    return all_settings

@router.delete("/{camera_id}/reset", response_model=SettingsResponse)
async def reset_camera_settings(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_settings"))
) -> Any:
    """Reset camera settings to defaults"""
    
    # Get camera
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    try:
        async with CameraClient(base_url=camera.base_url) as client:
            # Reset settings
            reset_settings = await client.reset_settings()
            
            # Store reset settings in database
            db_settings = await db.execute(
                select(DBCameraSettings).where(DBCameraSettings.camera_id == camera_id)
            )
            db_setting = db_settings.scalar_one_or_none()
            
            if db_setting:
                db_setting.settings_data = reset_settings.dict()
                db_setting.settings_version = "1.0"
            else:
                db_setting = DBCameraSettings(
                    camera_id=camera_id,
                    settings_data=reset_settings.dict(),
                    settings_version="1.0"
                )
                db.add(db_setting)
            
            await db.commit()
            
            logger.info("Camera settings reset", camera_id=camera_id, user_id=current_user.id)
            
            return SettingsResponse(
                camera_id=camera_id,
                settings=reset_settings.dict(),
                version="1.0"
            )
            
    except Exception as e:
        logger.error("Failed to reset camera settings", camera_id=camera_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset camera settings"
        )

@router.get("/{camera_id}/exposure")
async def get_exposure_settings(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_settings"))
) -> Any:
    """Get camera exposure settings"""
    
    # Get camera
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    try:
        async with CameraClient(base_url=camera.base_url) as client:
            exposure_settings = await client.get_exposure_settings()
            
            return {
                "camera_id": camera_id,
                "exposure_settings": exposure_settings
            }
            
    except Exception as e:
        logger.error("Failed to get exposure settings", camera_id=camera_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get exposure settings"
        )

@router.put("/{camera_id}/exposure")
async def update_exposure_settings(
    camera_id: int,
    exposure_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_settings"))
) -> Any:
    """Update camera exposure settings"""
    
    # Get camera
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    try:
        async with CameraClient(base_url=camera.base_url) as client:
            updated_exposure = await client.update_exposure_settings(exposure_data)
            
            logger.info("Exposure settings updated", camera_id=camera_id, user_id=current_user.id)
            
            return {
                "camera_id": camera_id,
                "exposure_settings": updated_exposure
            }
            
    except Exception as e:
        logger.error("Failed to update exposure settings", camera_id=camera_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update exposure settings"
        )

@router.get("/{camera_id}/focus")
async def get_focus_settings(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_settings"))
) -> Any:
    """Get camera focus settings"""
    
    # Get camera
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    try:
        async with CameraClient(base_url=camera.base_url) as client:
            focus_settings = await client.get_focus_settings()
            
            return {
                "camera_id": camera_id,
                "focus_settings": focus_settings
            }
            
    except Exception as e:
        logger.error("Failed to get focus settings", camera_id=camera_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get focus settings"
        )

@router.put("/{camera_id}/focus")
async def update_focus_settings(
    camera_id: int,
    focus_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_settings"))
) -> Any:
    """Update camera focus settings"""
    
    # Get camera
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    try:
        async with CameraClient(base_url=camera.base_url) as client:
            updated_focus = await client.update_focus_settings(focus_data)
            
            logger.info("Focus settings updated", camera_id=camera_id, user_id=current_user.id)
            
            return {
                "camera_id": camera_id,
                "focus_settings": updated_focus
            }
            
    except Exception as e:
        logger.error("Failed to update focus settings", camera_id=camera_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update focus settings"
        )

@router.get("/{camera_id}/overlay")
async def get_overlay_settings(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_settings"))
) -> Any:
    """Get camera overlay settings"""
    
    # Get camera
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    try:
        async with CameraClient(base_url=camera.base_url) as client:
            overlay_settings = await client.get_overlay_settings()
            
            return {
                "camera_id": camera_id,
                "overlay_settings": overlay_settings
            }
            
    except Exception as e:
        logger.error("Failed to get overlay settings", camera_id=camera_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get overlay settings"
        )

@router.put("/{camera_id}/overlay")
async def update_overlay_settings(
    camera_id: int,
    overlay_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_settings"))
) -> Any:
    """Update camera overlay settings"""
    
    # Get camera
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    try:
        async with CameraClient(base_url=camera.base_url) as client:
            updated_overlay = await client.update_overlay_settings(overlay_data)
            
            logger.info("Overlay settings updated", camera_id=camera_id, user_id=current_user.id)
            
            return {
                "camera_id": camera_id,
                "overlay_settings": updated_overlay
            }
            
    except Exception as e:
        logger.error("Failed to update overlay settings", camera_id=camera_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update overlay settings"
        )

@router.get("/application/settings", response_model=ApplicationSettingsResponse)
async def get_application_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get application settings"""
    try:
        # Get the first (and only) settings record
        result = await db.execute(select(ApplicationSettings).limit(1))
        settings = result.scalar_one_or_none()
        
        if not settings:
            # Create default settings if none exist
            settings = ApplicationSettings()
            db.add(settings)
            await db.commit()
            await db.refresh(settings)
        
        return settings
    except Exception as e:
        logger.error("Failed to get application settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get application settings"
        )

@router.put("/application/settings", response_model=ApplicationSettingsResponse)
async def update_application_settings(
    settings_data: ApplicationSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_settings"))
) -> Any:
    """Update application settings"""
    
    # Get the first (and only) settings record
    result = await db.execute(select(ApplicationSettings).limit(1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create default settings if none exist
        settings = ApplicationSettings()
        db.add(settings)
    
    # Update fields
    update_data = settings_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    await db.commit()
    await db.refresh(settings)
    
    logger.info("Application settings updated", user_id=current_user.id, updated_fields=list(update_data.keys()))
    
    return ApplicationSettingsResponse.from_orm(settings)

@router.post("/application/settings/reset")
async def reset_application_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reset application settings to defaults"""
    try:
        # Get the first (and only) settings record
        result = await db.execute(select(ApplicationSettings).limit(1))
        settings = result.scalar_one_or_none()
        
        if settings:
            # Reset to defaults
            settings.auto_start_streams = False
            settings.stream_quality = 'medium'
            settings.data_retention_enabled = True
            settings.event_retention_days = 30
            settings.snapshot_retention_days = 7
            settings.mobile_data_saving = True
            settings.low_bandwidth_mode = False
            settings.pre_event_recording_seconds = 10
            settings.post_event_recording_seconds = 10
        else:
            # Create default settings if none exist
            settings = ApplicationSettings()
            db.add(settings)
        
        await db.commit()
        
        logger.info("Application settings reset to defaults", user_id=current_user.id)
        return {"message": "Settings reset to defaults"}
    except Exception as e:
        logger.error("Failed to reset application settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset application settings"
        )

@router.post("/application/data-retention/cleanup")
async def run_data_retention_cleanup(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_settings"))
):
    """Run data retention cleanup to delete old events and snapshots"""
    try:
        result = await cleanup_old_data(db)
        
        logger.info("Data retention cleanup completed", user_id=current_user.id, result=result)
        
        return result
        
    except Exception as e:
        logger.error("Failed to run data retention cleanup", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run cleanup: {str(e)}"
        )

@router.get("/application/data-retention/stats")
async def get_data_retention_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_settings"))
):
    """Get data retention statistics (what would be deleted)"""
    try:
        stats = await get_retention_stats(db)
        
        return stats
        
    except Exception as e:
        logger.error("Failed to get data retention stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        ) 