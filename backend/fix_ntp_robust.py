import asyncio
import json
from sqlalchemy import select
from app.core.database import get_db
from app.models.camera import Camera
from app.services.camera_client import CameraClient

async def fix_camera_ntp_robust():
    """Fix NTP settings for all cameras with robust error handling"""
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
                        print("Getting current settings...")
                        settings = await client.get_settings()
                        print(f"Current NTP server: {settings.network_ntp}")
                        
                        # Create a minimal settings update with just NTP
                        ntp_update = {
                            "network_ntp": default_gateway,
                            "network_ntp_ignore_server_sync": False
                        }
                        
                        print(f"Updating NTP settings: {ntp_update}")
                        
                        # Try direct API call instead of using the model
                        if not client.client:
                            raise RuntimeError("CameraClient not initialized")
                        
                        # Make direct PUT request
                        url = f"{client.base_url.rstrip('/')}/api/system/settings"
                        print(f"Making PUT request to: {url}")
                        
                        response = await client.client.put(
                            url,
                            json=ntp_update,
                            timeout=30.0
                        )
                        
                        print(f"Response status: {response.status_code}")
                        print(f"Response headers: {dict(response.headers)}")
                        
                        if response.status_code == 200:
                            try:
                                result = response.json()
                                print(f"Response JSON: {result}")
                            except:
                                print(f"Response text: {response.text}")
                            
                            print("✅ NTP settings updated successfully")
                            
                            # Reboot camera to apply NTP changes
                            print("Rebooting camera to apply NTP changes...")
                            await client.reboot_system()
                            print("Camera reboot initiated")
                        else:
                            print(f"❌ Failed to update NTP settings. Status: {response.status_code}")
                            print(f"Response: {response.text}")
                        
                except Exception as e:
                    print(f"❌ Error updating camera {camera.name}: {e}")
                    import traceback
                    traceback.print_exc()
                    
        finally:
            break

if __name__ == "__main__":
    asyncio.run(fix_camera_ntp_robust()) 