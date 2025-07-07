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
from app.schemas.settings import SettingsResponse, SettingsUpdate, SettingsReset, ApplicationSettingsResponse, ApplicationSettingsUpdate

logger = structlog.get_logger()
router = APIRouter()

@router.get("/{camera_id}", response_model=SettingsResponse)
async def get_camera_settings(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_settings"))
) -> Any:
    """Get camera settings"""
    
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
            settings = await client.get_settings()
            
            # Store settings in database
            db_settings = await db.execute(
                select(DBCameraSettings).where(DBCameraSettings.camera_id == camera_id)
            )
            db_setting = db_settings.scalar_one_or_none()
            
            if db_setting:
                db_setting.settings_data = settings.dict()
                db_setting.settings_version = "1.0"
            else:
                db_setting = DBCameraSettings(
                    camera_id=camera_id,
                    settings_data=settings.dict(),
                    settings_version="1.0"
                )
                db.add(db_setting)
            
            await db.commit()
            
            return SettingsResponse(
                camera_id=camera_id,
                settings=settings.dict(),
                version="1.0"
            )
            
    except Exception as e:
        logger.error("Failed to get camera settings", camera_id=camera_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get camera settings"
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
            # Only send the changed fields to the camera
            update_data = settings_data.dict(exclude_unset=True)
            # PATCH: Use _make_request directly to send only changed fields
            response = await client._make_request("PUT", "/system/settings", json=update_data)
            # Optionally, fetch the updated settings from the camera
            updated_settings = await client.get_settings()
            
            # Store updated settings in database
            db_settings = await db.execute(
                select(DBCameraSettings).where(DBCameraSettings.camera_id == camera_id)
            )
            db_setting = db_settings.scalar_one_or_none()
            
            if db_setting:
                db_setting.settings_data = updated_settings.dict()
                db_setting.settings_version = "1.0"
            else:
                db_setting = DBCameraSettings(
                    camera_id=camera_id,
                    settings_data=updated_settings.dict(),
                    settings_version="1.0"
                )
                db.add(db_setting)
            
            await db.commit()
            
            logger.info("Camera settings updated", camera_id=camera_id, user_id=current_user.id)
            
            return SettingsResponse(
                camera_id=camera_id,
                settings=updated_settings.dict(),
                version="1.0"
            )
            
    except Exception as e:
        logger.error("Failed to update camera settings", camera_id=camera_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update camera settings: {str(e)}"
        )

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
    
    # Check if auto_download_events is being changed
    auto_download_changed = (
        settings_data.auto_download_events is not None and 
        settings_data.auto_download_events != settings.auto_download_events
    )
    
    # Update fields
    update_data = settings_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    await db.commit()
    await db.refresh(settings)
    
    # Handle FTP configuration based on auto_download_events setting
    if auto_download_changed:
        try:
            # Get all active cameras
            cameras_result = await db.execute(
                select(Camera).where(Camera.is_active == True)
            )
            cameras = cameras_result.scalars().all()
            
            if settings.auto_download_events:
                # Enable FTP on all cameras
                logger.info("Auto-download enabled, configuring FTP on all cameras")
                for camera in cameras:
                    try:
                        async with CameraClient(base_url=camera.base_url) as client:
                            await client.configure_ftp()
                            logger.info(f"FTP configured for camera {camera.id} ({camera.name})")
                    except Exception as e:
                        logger.error(f"Failed to configure FTP for camera {camera.id}", error=str(e))
            else:
                # Disable FTP on all cameras
                logger.info("Auto-download disabled, clearing FTP settings on all cameras")
                for camera in cameras:
                    try:
                        async with CameraClient(base_url=camera.base_url) as client:
                            # Clear FTP settings by setting empty values
                            await client.configure_ftp(
                                ftp_host="",
                                ftp_user="",
                                ftp_password="",
                                ftp_recordings=False,
                                ftp_snapshots=False
                            )
                            logger.info(f"FTP disabled for camera {camera.id} ({camera.name})")
                    except Exception as e:
                        logger.error(f"Failed to disable FTP for camera {camera.id}", error=str(e))
                        
        except Exception as e:
            logger.error("Failed to handle FTP configuration", error=str(e))
            # Don't fail the settings update if FTP config fails
    
    logger.info("Application settings updated", user_id=current_user.id, auto_download_events=settings.auto_download_events)
    
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
            settings.store_data_on_camera = True
            settings.auto_download_events = False
            settings.auto_download_snapshots = False
            settings.event_retention_days = 30
            settings.snapshot_retention_days = 7
            settings.mobile_data_saving = True
            settings.low_bandwidth_mode = False
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