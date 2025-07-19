import asyncio
from app.services.time_sync_service import TimeSyncService

async def test_time_sync():
    """Test the time sync service"""
    print("Testing Time Sync Service")
    print("=" * 50)
    
    # Create service with shorter intervals for testing (normally runs daily)
    service = TimeSyncService(check_interval=60, max_time_drift=30)  # 1 minute for testing
    
    try:
        print("Starting time sync service...")
        await service.start()
        
        # Let it run for a few minutes
        print("Service is running. Press Ctrl+C to stop...")
        await asyncio.sleep(180)  # Run for 3 minutes
        
    except KeyboardInterrupt:
        print("\nStopping service...")
    finally:
        await service.stop()
        print("Service stopped")

if __name__ == "__main__":
    asyncio.run(test_time_sync()) 