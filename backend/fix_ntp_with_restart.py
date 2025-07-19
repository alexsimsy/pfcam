import asyncio
import time
from sqlalchemy import select
from app.core.database import get_db
from app.models.camera import Camera
from app.services.camera_client import CameraClient

async def wait_for_camera_online(base_url: str, max_wait: int = 120) -> bool:
    """Wait for camera to come back online after restart"""
    print(f"Waiting for camera to come back online... (max {max_wait} seconds)")
    
    for i in range(max_wait):
        try:
            async with CameraClient(base_url=base_url) as client:
                # Try to get system info
                system_info = await client.get_system_info()
                print(f"✅ Camera is back online! Uptime: {system_info.uptime}s")
                return True
        except Exception as e:
            if i % 10 == 0:  # Print status every 10 seconds
                print(f"⏳ Still waiting... ({i}/{max_wait}s) - {e}")
            await asyncio.sleep(1)
    
    print("❌ Camera did not come back online within timeout")
    return False

async def fix_camera_ntp_with_restart():
    """Fix NTP settings for all cameras with proper restart handling"""
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
                print(f"\n{'='*60}")
                print(f"Fixing camera: {camera.name} ({camera.ip_address})")
                print(f"{'='*60}")
                
                try:
                    async with CameraClient(base_url=camera.base_url) as client:
                        # Get current settings
                        print("📋 Getting current settings...")
                        settings = await client.get_settings()
                        print(f"Current NTP server: {settings.network_ntp}")
                        print(f"Current system time: {settings.network_ntp_ignore_server_sync}")
                        
                        # Check if update is needed
                        if settings.network_ntp == default_gateway:
                            print("✅ NTP server is already correctly configured")
                            continue
                        
                        # Create minimal NTP update
                        ntp_update = {
                            "network_ntp": default_gateway,
                            "network_ntp_ignore_server_sync": False
                        }
                        
                        print(f"🔄 Updating NTP settings: {ntp_update}")
                        
                        # Make direct API call
                        if not client.client:
                            raise RuntimeError("CameraClient not initialized")
                        
                        url = f"{client.base_url.rstrip('/')}/api/system/settings"
                        print(f"📡 Making PUT request to: {url}")
                        
                        response = await client.client.put(
                            url,
                            json=ntp_update,
                            timeout=30.0
                        )
                        
                        print(f"📊 Response status: {response.status_code}")
                        
                        if response.status_code == 200:
                            print("✅ NTP settings updated successfully")
                            
                            # Reboot camera to apply NTP changes
                            print("🔄 Rebooting camera to apply NTP changes...")
                            await client.reboot_system()
                            print("🚀 Camera reboot initiated")
                            
                            # Wait for camera to come back online
                            print("⏳ Waiting for camera restart...")
                            if await wait_for_camera_online(camera.base_url):
                                print("✅ Camera is back online with new NTP settings")
                                
                                # Verify the settings were applied
                                print("🔍 Verifying NTP settings...")
                                async with CameraClient(base_url=camera.base_url) as verify_client:
                                    verify_settings = await verify_client.get_settings()
                                    print(f"New NTP server: {verify_settings.network_ntp}")
                                    print(f"NTP ignore server sync: {verify_settings.network_ntp_ignore_server_sync}")
                                    
                                    if verify_settings.network_ntp == default_gateway:
                                        print("✅ NTP settings verified successfully!")
                                    else:
                                        print("❌ NTP settings verification failed")
                            else:
                                print("❌ Camera did not come back online")
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
    asyncio.run(fix_camera_ntp_with_restart()) 