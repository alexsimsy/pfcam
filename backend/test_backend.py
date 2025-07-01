#!/usr/bin/env python3
"""
Simple backend test script
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_backend():
    """Test if backend can start and connect to database"""
    print("Testing backend startup...")
    
    try:
        # Test database connection
        from app.core.database import engine
        async with engine.begin() as conn:
            print("✅ Database connection successful")
        
        # Test camera client
        from app.services.camera_client import CameraClient
        async with CameraClient() as client:
            is_connected = await client.test_connection()
            print(f"✅ Camera connection: {is_connected}")
        
        print("✅ Backend test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_backend())
    sys.exit(0 if success else 1) 