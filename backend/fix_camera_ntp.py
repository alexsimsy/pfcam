import asyncio
import subprocess
from sqlalchemy import select
from app.core.database import get_db
from app.models.camera import Camera
from app.services.camera_client import CameraClient

def get_default_gateway():
    """Get the default gateway IP address"""
    try:
        # Get default gateway using route command
        result = subprocess.run(['route', '-n', 'get', 'default'], 
                              capture_output=True, text=True, check=True)
        for line in result.stdout.split('\n'):
            if 'gateway:' in line:
                return line.split(':')[1].strip()
    except:
        pass
    
    # Fallback: try to get from docker network
    try:
        result = subprocess.run(['docker', 'network', 'inspect', 'bridge'], 
                              capture_output=True, text=True, check=True)
        # This is a simplified approach - you might need to parse JSON properly
        if 'Gateway' in result.stdout:
            # Extract gateway from output (simplified)
            lines = result.stdout.split('\n')
            for line in lines:
                if '"Gateway"' in line:
                    return line.split('"')[3]
    except:
        pass
    
    return "192.168.1.1"  # Common default gateway

async def check_and_fix_camera_ntp():
    """Check and fix NTP settings for all cameras"""
    async for db in get_db():
        try:
            # Get all cameras
            result = await db.execute(select(Camera))
            cameras = result.scalars().all()
            
            if not cameras:
                print("No cameras found in database")
                return
            
            default_gateway = get_default_gateway()
            print(f"Default gateway detected: {default_gateway}")
            
            for camera in cameras:
                print(f"\nChecking camera: {camera.name} ({camera.ip_address})")
                
                try:
                    async with CameraClient(base_url=camera.base_url) as client:
                        # Get current settings
                        settings = await client.get_settings()
                        print(f"Current NTP server: {settings.network_ntp}")
                        print(f"NTP ignore server sync: {settings.network_ntp_ignore_server_sync}")
                        
                        # Check if NTP needs updating
                        if settings.network_ntp != default_gateway:
                            print(f"Updating NTP server from {settings.network_ntp} to {default_gateway}")
                            
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
                        else:
                            print("NTP server is already correctly configured")
                            
                except Exception as e:
                    print(f"Error updating camera {camera.name}: {e}")
                    
        finally:
            break

if __name__ == "__main__":
    asyncio.run(check_and_fix_camera_ntp()) 