#!/usr/bin/env python3
"""
Simple test script to verify camera API integration
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.camera_client import CameraClient

async def simple_test():
    """Simple test of camera client"""
    print("Testing camera client...")
    
    try:
        async with CameraClient() as client:
            print("✓ Camera client created successfully")
            
            # Test connection
            is_connected = await client.test_connection()
            print(f"✓ Connection test: {is_connected}")
            
            if is_connected:
                # Get events
                events = await client.get_events()
                print(f"✓ Found {len(events)} events")
                
                # Get system info
                system_info = await client.get_system_info()
                print(f"✓ System info: {system_info.name} v{system_info.softwareVersion}")
                
                # Get settings
                settings = await client.get_settings()
                print(f"✓ Settings: IP {settings.network_ip}")
                
                print("✓ All tests passed!")
                return True
            else:
                print("✗ Connection failed")
                return False
                
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(simple_test())
    sys.exit(0 if success else 1) 