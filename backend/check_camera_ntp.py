import asyncio
from sqlalchemy import select
from app.core.database import get_db
from app.models.camera import Camera
from app.services.camera_client import CameraClient

async def check_camera_ntp():
    """Check NTP settings for all cameras"""
    async for db in get_db():
        try:
            # Get all cameras
            result = await db.execute(select(Camera))
            cameras = result.scalars().all()
            
            if not cameras:
                print("No cameras found in database")
                return
            
            print("=== Camera NTP Settings Check ===\n")
            
            for camera in cameras:
                print(f"Camera: {camera.name}")
                print(f"IP Address: {camera.ip_address}")
                print(f"Base URL: {camera.base_url}")
                
                try:
                    async with CameraClient(base_url=camera.base_url) as client:
                        # Get current settings
                        settings = await client.get_settings()
                        print(f"NTP Server: {settings.network_ntp}")
                        print(f"NTP Ignore Server Sync: {settings.network_ntp_ignore_server_sync}")
                        
                        # Get system info for current time
                        system_info = await client.get_system_info()
                        print(f"System Time: {system_info.systemTime}")
                        print(f"Timezone: {system_info.timezone}")
                        
                        # Get datetime settings
                        datetime_info = await client.get_datetime()
                        print(f"DateTime Info: {datetime_info}")
                        
                except Exception as e:
                    print(f"Error connecting to camera: {e}")
                
                print("-" * 50)
                    
        finally:
            break

if __name__ == "__main__":
    asyncio.run(check_camera_ntp()) 