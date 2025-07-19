import asyncio
import time
import subprocess
from datetime import datetime, timedelta
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.config import settings
from app.models.camera import Camera
from app.services.camera_client import CameraClient

logger = structlog.get_logger()

class TimeSyncService:
    """Background service to monitor and fix camera time synchronization"""
    
    def __init__(self, check_interval: int = None, max_time_drift: int = None):
        """
        Initialize the time sync service
        
        Args:
            check_interval: How often to check cameras (seconds, default from config)
            max_time_drift: Maximum allowed time drift (seconds, default from config)
        """
        self.check_interval = check_interval or settings.TIME_SYNC_CHECK_INTERVAL
        self.max_time_drift = max_time_drift or settings.TIME_SYNC_MAX_DRIFT
        self.running = False
        self.task = None
        
    async def start(self):
        """Start the time sync service"""
        if self.running:
            logger.warning("Time sync service is already running")
            return
            
        self.running = True
        self.task = asyncio.create_task(self._run())
        logger.info("Time sync service started", 
                   check_interval=self.check_interval, 
                   max_drift=self.max_time_drift)
    
    async def stop(self):
        """Stop the time sync service"""
        if not self.running:
            return
            
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Time sync service stopped")
    
    async def _run(self):
        """Main service loop"""
        while self.running:
            try:
                await self._check_all_cameras()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in time sync service", error=str(e))
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _check_all_cameras(self):
        """Check time synchronization for all cameras"""
        async for db in get_db():
            try:
                cameras = await self._get_cameras(db)
                
                for camera in cameras:
                    try:
                        await self._check_camera_time(camera, db)
                    except Exception as e:
                        logger.error("Error checking camera time", 
                                   camera_id=camera.id, 
                                   camera_name=camera.name, 
                                   error=str(e))
            finally:
                break
    
    async def _get_cameras(self, db: AsyncSession) -> List[Camera]:
        """Get all active cameras from database"""
        result = await db.execute(select(Camera).where(Camera.is_active == True))
        return result.scalars().all()
    
    async def _check_camera_time(self, camera: Camera, db: AsyncSession):
        """Check and fix time synchronization for a single camera"""
        try:
            async with CameraClient(base_url=camera.base_url) as client:
                # Get current settings first to check NTP configuration
                settings = await client.get_settings()
                
                # Check if camera is using default NTP server
                if camera_settings.network_ntp == settings.TIME_SYNC_CAMERA_DEFAULT_NTP:
                    logger.info("Camera using default NTP server, checking time synchronization", 
                               camera_id=camera.id,
                               camera_name=camera.name,
                               ntp_server=camera_settings.network_ntp)
                    
                    # Get current system time
                    system_info = await client.get_system_info()
                    camera_time_str = system_info.systemTime
                    
                    # Parse camera time
                    try:
                        camera_time = datetime.fromisoformat(camera_time_str.replace('Z', '+00:00'))
                    except ValueError:
                        logger.warning("Invalid camera time format", 
                                     camera_id=camera.id, 
                                     time_str=camera_time_str)
                        return
                    
                    # Get current server time
                    server_time = datetime.utcnow()
                    
                    # Calculate time difference
                    time_diff = abs((camera_time - server_time).total_seconds())
                    
                    logger.info("Camera time check", 
                               camera_id=camera.id,
                               camera_name=camera.name,
                               camera_time=camera_time.isoformat(),
                               server_time=server_time.isoformat(),
                               time_diff=time_diff)
                    
                    # Check if time drift is too large
                    if time_diff > self.max_time_drift:
                        logger.warning("Camera time drift detected", 
                                     camera_id=camera.id,
                                     camera_name=camera.name,
                                     time_diff=time_diff,
                                     max_drift=self.max_time_drift)
                        
                        # Fix the time synchronization
                        await self._fix_camera_time(camera, client)
                    else:
                        logger.info("Camera time is synchronized, no action needed", 
                                   camera_id=camera.id,
                                   camera_name=camera.name,
                                   time_diff=time_diff)
                else:
                    logger.info("Camera using custom NTP server, skipping time check", 
                               camera_id=camera.id,
                               camera_name=camera.name,
                               ntp_server=camera_settings.network_ntp)
                    
        except Exception as e:
            logger.error("Error checking camera time", 
                       camera_id=camera.id,
                       camera_name=camera.name,
                       error=str(e))
    
    async def _fix_camera_time(self, camera: Camera, client: CameraClient):
        """Fix camera time synchronization"""
        try:
            logger.info("Fixing camera time synchronization", 
                       camera_id=camera.id,
                       camera_name=camera.name)
            
            # Get current settings
            camera_settings = await client.get_settings()
            
            # Get current default gateway dynamically
            default_gateway = await self._get_default_gateway()
            
            logger.info("Updating NTP server", 
                       camera_id=camera.id,
                       old_ntp=camera_settings.network_ntp,
                       new_ntp=default_gateway)
            
            # Update NTP settings
            ntp_update = {
                "network_ntp": default_gateway,
                "network_ntp_ignore_server_sync": False
            }
            
            # Make the update request
            if not client.client:
                raise RuntimeError("CameraClient not initialized")
            
            url = f"{client.base_url.rstrip('/')}/api/system/settings"
            response = await client.client.put(url, json=ntp_update, timeout=30.0)
            
            if response.status_code == 200:
                logger.info("NTP settings updated successfully", 
                           camera_id=camera.id,
                           camera_name=camera.name)
                
                # Reboot camera to apply changes
                logger.info("Rebooting camera to apply NTP changes", 
                           camera_id=camera.id,
                           camera_name=camera.name)
                
                await client.reboot_system()
                
                # Wait for camera to come back online
                await self._wait_for_camera_online(camera.base_url)
                
                logger.info("Camera time synchronization completed", 
                           camera_id=camera.id,
                           camera_name=camera.name)
            else:
                logger.error("Failed to update NTP settings", 
                           camera_id=camera.id,
                           status_code=response.status_code,
                           response=response.text)
                
        except Exception as e:
            logger.error("Error fixing camera time", 
                       camera_id=camera.id,
                       camera_name=camera.name,
                       error=str(e))
    
    async def _get_default_gateway(self) -> str:
        """Get the default gateway IP address dynamically"""
        try:
            # Try to get default gateway using route command
            result = subprocess.run(['route', '-n', 'get', 'default'], 
                                  capture_output=True, text=True, check=True)
            for line in result.stdout.split('\n'):
                if 'gateway:' in line:
                    gateway = line.split(':')[1].strip()
                    logger.info("Detected default gateway", gateway=gateway)
                    return gateway
        except Exception as e:
            logger.warning("Failed to detect default gateway using route command", error=str(e))
        
        try:
            # Fallback: try to get from docker network
            result = subprocess.run(['docker', 'network', 'inspect', 'bridge'], 
                                  capture_output=True, text=True, check=True)
            if 'Gateway' in result.stdout:
                # Extract gateway from output (simplified)
                lines = result.stdout.split('\n')
                for line in lines:
                    if '"Gateway"' in line:
                        gateway = line.split('"')[3]
                        logger.info("Detected default gateway from docker", gateway=gateway)
                        return gateway
        except Exception as e:
            logger.warning("Failed to detect default gateway from docker", error=str(e))
        
        # Final fallback
        fallback_gateway = "192.168.1.1"
        logger.warning("Using fallback default gateway", gateway=fallback_gateway)
        return fallback_gateway
    
    async def _wait_for_camera_online(self, base_url: str, max_wait: int = 120) -> bool:
        """Wait for camera to come back online after restart"""
        logger.info("Waiting for camera to come back online", base_url=base_url)
        
        for i in range(max_wait):
            try:
                async with CameraClient(base_url=base_url) as client:
                    system_info = await client.get_system_info()
                    logger.info("Camera is back online", 
                               base_url=base_url,
                               uptime=system_info.uptime)
                    return True
            except Exception as e:
                if i % 30 == 0:  # Log every 30 seconds
                    logger.info("Still waiting for camera", 
                               base_url=base_url,
                               wait_time=i,
                               max_wait=max_wait)
                await asyncio.sleep(1)
        
        logger.error("Camera did not come back online within timeout", 
                    base_url=base_url,
                    max_wait=max_wait)
        return False

# Global instance
time_sync_service = TimeSyncService()

async def start_time_sync_service():
    """Start the time sync service"""
    await time_sync_service.start()

async def stop_time_sync_service():
    """Stop the time sync service"""
    await time_sync_service.stop() 