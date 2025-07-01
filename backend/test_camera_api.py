#!/usr/bin/env python3
"""
Test script to verify camera API integration
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.camera_client import CameraClient
import structlog

# Setup logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

async def test_camera_connection():
    """Test basic camera connection"""
    logger.info("Testing camera connection...")
    
    async with CameraClient() as client:
        try:
            # Test connection
            is_connected = await client.test_connection()
            logger.info("Camera connection test", result=is_connected)
            
            if not is_connected:
                logger.error("Failed to connect to camera")
                return False
            
            # Get system info
            system_info = await client.get_system_info()
            logger.info("System info retrieved", software_version=system_info.softwareVersion, name=system_info.name)
            
            # Get available streams
            streams = await client.get_streams()
            logger.info("Streams retrieved", count=len(streams))
            for name, stream in streams.items():
                logger.info("Stream", name=name, codec=stream.codec, fps=stream.fps)
            
            # Get events
            events = await client.get_events()
            logger.info("Events retrieved", count=len(events))
            
            # Get settings
            settings = await client.get_settings()
            logger.info("Settings retrieved", network_ip=settings.network_ip)
            
            return True
            
        except Exception as e:
            logger.error("Camera test failed", error=str(e))
            return False

async def test_event_operations():
    """Test event-related operations"""
    logger.info("Testing event operations...")
    
    async with CameraClient() as client:
        try:
            # Get events
            events = await client.get_events()
            logger.info("Events count", count=len(events))
            
            if events:
                # Test getting first event file
                first_event = events[0]
                logger.info("Testing event file download", filename=first_event.fileName)
                
                try:
                    file_data = await client.get_event_file(first_event.fileName)
                    logger.info("Event file downloaded", size=len(file_data))
                except Exception as e:
                    logger.warning("Failed to download event file", error=str(e))
            
            # Get active events
            active_events = await client.get_active_events()
            logger.info("Active events count", count=len(active_events))
            
            return True
            
        except Exception as e:
            logger.error("Event operations test failed", error=str(e))
            return False

async def test_settings_operations():
    """Test settings operations"""
    logger.info("Testing settings operations...")
    
    async with CameraClient() as client:
        try:
            # Get current settings
            settings = await client.get_settings()
            logger.info("Current settings retrieved", name=settings.name, network_ip=settings.network_ip)
            
            # Test getting system info
            system_info = await client.get_system_info()
            logger.info("System info", software_version=system_info.softwareVersion, uptime=system_info.uptime)
            
            # Test getting storage info
            storage_info = await client.get_storage_info()
            logger.info("Storage info", storage=storage_info)
            
            # Test getting firmware info
            firmware_info = await client.get_firmware_info()
            logger.info("Firmware info", firmware=firmware_info)
            
            return True
            
        except Exception as e:
            logger.error("Settings operations test failed", error=str(e))
            return False

async def main():
    """Run all camera tests"""
    logger.info("Starting camera API tests")
    
    tests = [
        ("Connection Test", test_camera_connection),
        ("Event Operations Test", test_event_operations),
        ("Settings Operations Test", test_settings_operations),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"Running {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            logger.info(f"{test_name} completed", success=result)
        except Exception as e:
            logger.error(f"{test_name} failed", error=str(e))
            results.append((test_name, False))
    
    # Summary
    logger.info("Test Summary")
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    logger.info("Overall result", success=all_passed)
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 