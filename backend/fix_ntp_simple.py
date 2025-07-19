import asyncio
from sqlalchemy import select
from app.core.database import get_db
from app.models.camera import Camera
from app.services.camera_client import CameraClient

async def fix_camera_ntp():
    """Fix NTP settings for all cameras"""
    async for db in get_db():
        try:
            # Get all cameras
            result = await db.execute(select(Camera))
            cameras = result.scalars().all()
            
            if not cameras:
                print("No cameras found in database")
                return
            
            # Your default gateway
            default_gateway = "192.168.86.1"
            print(f"Setting NTP server to: {default_gateway}")
            
            for camera in cameras:
                print(f"\nFixing camera: {camera.name} ({camera.ip_address})")
                
                try:
                    async with CameraClient(base_url=camera.base_url) as client:
                        # Get current settings
                        settings = await client.get_settings()
                        print(f"Current NTP server: {settings.network_ntp}")
                        
                        # Update NTP settings
                        settings.network_ntp = default_gateway
                        settings.network_ntp_ignore_server_sync = False
                        
                        # Apply settings
                        updated_settings = await client.update_settings(settings)
                        print(f"Updated NTP server: {updated_settings.network_ntp}")
                        
                        # Reboot camera to apply NTP changes
                        print("Rebooting camera to apply NTP changes...")
                        await client.reboot_system()
                        print("Camera reboot initiated")
                        
                        print("✅ NTP settings updated successfully")
                        
                except Exception as e:
                    print(f"❌ Error updating camera {camera.name}: {e}")
                    
        finally:
            break

if __name__ == "__main__":
    asyncio.run(fix_camera_ntp()) 