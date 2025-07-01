from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog
from fastapi.responses import FileResponse
import os
from app.core.config import settings
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.models.user import User
from app.models.camera import Camera
from app.services.camera_client import CameraClient
from app.schemas.streams import StreamResponse, StreamList
from app.models.snapshot import Snapshot

logger = structlog.get_logger()
router = APIRouter()

@router.get("/snapshots/{camera_id}")
async def list_snapshots(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_streams"))
):
    """List all snapshots for a camera"""
    result = await db.execute(select(Snapshot).where(Snapshot.camera_id == camera_id).order_by(Snapshot.taken_at.desc()))
    snapshots = result.scalars().all()
    return [
        {
            "id": s.id,
            "filename": s.filename,
            "taken_at": s.taken_at,
            "download_url": s.get_download_url()
        } for s in snapshots
    ]

@router.get("/snapshots/{snapshot_id}/download")
async def download_snapshot(
    snapshot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_streams"))
):
    """Download a snapshot image by ID"""
    result = await db.execute(select(Snapshot).where(Snapshot.id == snapshot_id))
    snapshot = result.scalar_one_or_none()
    if not snapshot or not os.path.exists(snapshot.file_path):
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return FileResponse(snapshot.file_path, media_type="image/jpeg", filename=snapshot.filename)

@router.delete("/snapshots/{snapshot_id}")
async def delete_snapshot(
    snapshot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_streams"))
):
    """Delete a snapshot by ID"""
    result = await db.execute(select(Snapshot).where(Snapshot.id == snapshot_id))
    snapshot = result.scalar_one_or_none()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    try:
        # Delete the file from disk
        if os.path.exists(snapshot.file_path):
            os.remove(snapshot.file_path)
        
        # Delete from database
        await db.delete(snapshot)
        await db.commit()
        
        return {"message": "Snapshot deleted successfully"}
    except Exception as e:
        logger.error("Failed to delete snapshot", snapshot_id=snapshot_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete snapshot"
        )

@router.get("/{camera_id}", response_model=StreamList)
async def get_camera_streams(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_streams"))
) -> Any:
    """Get available streams for a camera"""
    
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
            streams = await client.get_streams()
            
            stream_list = []
            for name, stream in streams.items():
                stream_list.append(StreamResponse(
                    name=name,
                    stream_info=stream.dict(),
                    camera_id=camera_id
                ))
            
            return StreamList(
                camera_id=camera_id,
                streams=stream_list,
                count=len(stream_list)
            )
            
    except Exception as e:
        logger.error("Failed to get camera streams", camera_id=camera_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get camera streams"
        )

@router.get("/{camera_id}/{stream_name}")
async def get_stream_info(
    camera_id: int,
    stream_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_streams"))
) -> Any:
    """Get specific stream information"""
    
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
            streams = await client.get_streams()
            
            if stream_name not in streams:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stream not found"
                )
            
            stream = streams[stream_name]
            
            return StreamResponse(
                name=stream_name,
                stream_info=stream.dict(),
                camera_id=camera_id
            )
            
    except Exception as e:
        logger.error("Failed to get stream info", camera_id=camera_id, stream_name=stream_name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get stream information"
        )

@router.get("/{camera_id}/{stream_name}/url")
async def get_stream_url(
    camera_id: int,
    stream_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_streams"))
) -> Any:
    """Get stream URL for video player"""
    
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
            streams = await client.get_streams()
            
            if stream_name not in streams:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stream not found"
                )
            
            stream = streams[stream_name]
            
            return {
                "camera_id": camera_id,
                "stream_name": stream_name,
                "stream_url": stream.url.absolute or stream.url.relative,
                "codec": stream.codec,
                "fps": stream.fps,
                "resolution": stream.resolution
            }
            
    except Exception as e:
        logger.error("Failed to get stream URL", camera_id=camera_id, stream_name=stream_name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get stream URL"
        )

@router.get("/{camera_id}/{stream_name}/snapshot")
async def get_stream_snapshot(
    camera_id: int,
    stream_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_streams"))
) -> Any:
    """Get snapshot from stream and save it"""
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
            if stream_name not in streams:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stream not found"
                )
            stream = streams[stream_name]
            if not stream.snapshot:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Snapshot not available for this stream"
                )
            # Download the snapshot image
            snapshot_url = stream.snapshot.url.absolute or stream.snapshot.url.relative
            import httpx
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(snapshot_url)
                if response.status_code != 200:
                    raise HTTPException(status_code=502, detail="Failed to fetch snapshot image")
                image_bytes = response.content
            # Save to disk
            snapshot_dir = os.path.join(settings.STORAGE_PATH, "snapshots", str(camera_id))
            os.makedirs(snapshot_dir, exist_ok=True)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"snapshot_{camera_id}_{stream_name}_{timestamp}.jpg"
            file_path = os.path.join(snapshot_dir, filename)
            with open(file_path, "wb") as f:
                f.write(image_bytes)
            # Save metadata to DB
            snapshot = Snapshot(camera_id=camera_id, filename=filename, file_path=file_path)
            db.add(snapshot)
            await db.commit()
            await db.refresh(snapshot)
            return {
                "camera_id": camera_id,
                "stream_name": stream_name,
                "snapshot_id": snapshot.id,
                "filename": filename,
                "file_path": file_path,
                "taken_at": snapshot.taken_at,
                "download_url": f"/api/v1/streams/snapshots/{snapshot.id}/download"
            }
    except Exception as e:
        logger.error("Failed to get stream snapshot", camera_id=camera_id, stream_name=stream_name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get stream snapshot"
        )

@router.get("/{camera_id}/rtsp/info")
async def get_rtsp_info(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_streams"))
) -> Any:
    """Get RTSP stream information"""
    
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
            streams = await client.get_streams()
            
            rtsp_stream = streams.get("rtsp")
            if not rtsp_stream:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="RTSP stream not available"
                )
            
            return {
                "camera_id": camera_id,
                "rtsp_url": rtsp_stream.url.get("absolute", rtsp_stream.url.get("relative")),
                "codec": rtsp_stream.codec,
                "fps": rtsp_stream.fps,
                "resolution": rtsp_stream.resolution,
                "name": rtsp_stream.name
            }
            
    except Exception as e:
        logger.error("Failed to get RTSP info", camera_id=camera_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get RTSP information"
        )

@router.get("/{camera_id}/hd/info")
async def get_hd_stream_info(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_streams"))
) -> Any:
    """Get HD stream information"""
    
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
            streams = await client.get_streams()
            
            hd_stream = streams.get("hd")
            if not hd_stream:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="HD stream not available"
                )
            
            return {
                "camera_id": camera_id,
                "hd_url": hd_stream.url.absolute or hd_stream.url.relative,
                "codec": hd_stream.codec,
                "fps": hd_stream.fps,
                "resolution": hd_stream.resolution,
                "name": hd_stream.name,
                "snapshot_url": hd_stream.snapshot.url.absolute or hd_stream.snapshot.url.relative if hd_stream.snapshot else None
            }
            
    except Exception as e:
        logger.error("Failed to get HD stream info", camera_id=camera_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get HD stream information"
        ) 