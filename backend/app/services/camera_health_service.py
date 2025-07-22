import asyncio
from datetime import datetime
from typing import List
from sqlalchemy import select
import structlog

from app.core.database import get_db
from app.models.camera import Camera
from app.models.user import User
from app.services.camera_client import CameraClient
from app.services.notification_service import notification_service, CameraOfflineException

logger = structlog.get_logger()

class CameraHealthService:
    """Background service to monitor camera online/offline status and notify on changes."""
    def __init__(self, check_interval: int = 1800):  # 30 minutes
        self.check_interval = check_interval
        self.running = False
        self.task = None
        self.last_status = {}  # camera_id -> is_online

    async def start(self):
        if self.running:
            logger.warning("Camera health service is already running")
            return
        self.running = True
        self.task = asyncio.create_task(self._run())
        logger.info("Camera health service started", check_interval=self.check_interval)

    async def stop(self):
        if not self.running:
            return
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Camera health service stopped")

    async def _run(self):
        while self.running:
            try:
                await self._check_all_cameras()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in camera health service", error=str(e))
                await asyncio.sleep(60)

    async def _check_all_cameras(self):
        async for db in get_db():
            try:
                cameras = await db.execute(select(Camera).where(Camera.is_active == True))
                cameras = cameras.scalars().all()
                users = await db.execute(select(User).where(User.is_active == True))
                users = users.scalars().all()
                for camera in cameras:
                    prev_status = camera.is_online
                    try:
                        async with CameraClient(base_url=camera.base_url) as client:
                            is_connected = await client.test_connection()
                        camera.is_online = is_connected
                        if is_connected:
                            camera.last_seen = datetime.utcnow()
                    except Exception:
                        camera.is_online = False
                    await db.commit()
                    # Notify on status change
                    if prev_status != camera.is_online:
                        await notification_service.send_camera_status_notification(camera, camera.is_online, users)
                        logger.info("Camera status changed", camera_id=camera.id, name=camera.name, is_online=camera.is_online)
            finally:
                break

# Singleton instance
camera_health_service = CameraHealthService()

async def start_camera_health_service():
    await camera_health_service.start()

async def stop_camera_health_service():
    await camera_health_service.stop() 