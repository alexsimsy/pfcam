#!/usr/bin/env python3
"""
Test script to verify camera API integration (simplified version)
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.camera_client import CameraClient

async def test_camera_connection():
    """Test basic camera connection"""
    print("Testing camera connection...")
    
    async with CameraClient() as client:
        try:
            # Test connection
            is_connected = await client.test_connection()
            print(f"Camera connection test: {is_connected}")
            
            if not is_connected:
                print("Failed to connect to camera")
                return False
            
            # Get system info
            system_info = await client.get_system_info()
            print(f"System info retrieved: {system_info.name} v{system_info.softwareVersion}")
            
            # Get available streams
            streams = await client.get_streams()
            print(f"Streams retrieved: {len(streams)} streams")
            for name, stream in streams.items():
                print(f"Stream {name}: {stream.codec}, {stream.fps}fps")
            
            # Get events
            events = await client.get_events()
            print(f"Events retrieved: {len(events)} events")
            
            # Get settings
            settings = await client.get_settings()
            print(f"Settings retrieved: IP {settings.network_ip}")
            
            return True
            
        except Exception as e:
            print(f"Camera test failed: {e}")
            return False

async def test_event_operations():
    """Test event-related operations"""
    print("Testing event operations...")
    
    async with CameraClient() as client:
        try:
            # Get events
            events = await client.get_events()
            print(f"Events count: {len(events)}")
            
            if events:
                # Test getting first event file
                first_event = events[0]
                print(f"Testing event file download: {first_event.fileName}")
                
                try:
                    file_data = await client.get_event_file(first_event.fileName)
                    print(f"Event file downloaded: {len(file_data)} bytes")
                except Exception as e:
                    print(f"Failed to download event file: {e}")
            
            # Get active events
            active_events = await client.get_active_events()
            print(f"Active events count: {len(active_events)}")
            
            return True
            
        except Exception as e:
            print(f"Event operations test failed: {e}")
            return False

async def test_settings_operations():
    """Test settings operations"""
    print("Testing settings operations...")
    
    async with CameraClient() as client:
        try:
            # Get current settings
            settings = await client.get_settings()
            print(f"Current settings retrieved: {settings.name}, IP {settings.network_ip}")
            
            # Test getting system info
            system_info = await client.get_system_info()
            print(f"System info: v{system_info.softwareVersion}, uptime {system_info.uptime}")
            
            # Test getting storage info
            storage_info = await client.get_storage_info()
            print(f"Storage info: {storage_info}")
            
            # Test getting firmware info
            firmware_info = await client.get_firmware_info()
            print(f"Firmware info: {firmware_info}")
            
            return True
            
        except Exception as e:
            print(f"Settings operations test failed: {e}")
            return False

async def main():
    """Run all camera tests"""
    print("Starting camera API tests")
    
    tests = [
        ("Connection Test", test_camera_connection),
        ("Event Operations Test", test_event_operations),
        ("Settings Operations Test", test_settings_operations),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            print(f"{test_name} completed: {'SUCCESS' if result else 'FAILED'}")
        except Exception as e:
            print(f"{test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\nTest Summary")
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    print(f"\nOverall result: {'SUCCESS' if all_passed else 'FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 