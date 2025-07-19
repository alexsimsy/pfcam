import logging
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import Event
from app.models.snapshot import Snapshot
from app.models.settings import ApplicationSettings

logger = logging.getLogger(__name__)

async def cleanup_old_data(db: AsyncSession) -> dict:
    """
    Clean up old events and snapshots based on retention settings.
    Returns a dictionary with cleanup statistics.
    """
    try:
        # Get application settings
        settings_result = await db.execute(select(ApplicationSettings).limit(1))
        settings = settings_result.scalar_one_or_none()
        
        if not settings:
            logger.warning("No application settings found, skipping data cleanup")
            return {"events_deleted": 0, "snapshots_deleted": 0, "error": "No settings found"}
        
        if not settings.data_retention_enabled:
            logger.info("Data retention is disabled, skipping cleanup")
            return {"events_deleted": 0, "snapshots_deleted": 0, "retention_disabled": True}
        
        # Calculate cutoff dates
        event_cutoff = datetime.utcnow() - timedelta(days=settings.event_retention_days)
        snapshot_cutoff = datetime.utcnow() - timedelta(days=settings.snapshot_retention_days)
        
        logger.info(f"Cleaning up events older than {event_cutoff} and snapshots older than {snapshot_cutoff}")
        
        # Delete old events
        events_deleted = await db.execute(
            delete(Event).where(Event.created_at < event_cutoff)
        )
        events_deleted_count = events_deleted.rowcount
        
        # Delete old snapshots
        snapshots_deleted = await db.execute(
            delete(Snapshot).where(Snapshot.taken_at < snapshot_cutoff)
        )
        snapshots_deleted_count = snapshots_deleted.rowcount
        
        # Commit the changes
        await db.commit()
        
        logger.info(f"Data cleanup completed: {events_deleted_count} events, {snapshots_deleted_count} snapshots deleted")
        
        return {
            "events_deleted": events_deleted_count,
            "snapshots_deleted": snapshots_deleted_count,
            "event_cutoff": event_cutoff.isoformat(),
            "snapshot_cutoff": snapshot_cutoff.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during data cleanup: {str(e)}")
        await db.rollback()
        return {"events_deleted": 0, "snapshots_deleted": 0, "error": str(e)}

async def get_retention_stats(db: AsyncSession) -> dict:
    """
    Get statistics about data retention (count of items that would be deleted).
    """
    try:
        # Get application settings
        settings_result = await db.execute(select(ApplicationSettings).limit(1))
        settings = settings_result.scalar_one_or_none()
        
        if not settings:
            return {"error": "No settings found"}
        
        if not settings.data_retention_enabled:
            return {"retention_disabled": True}
        
        # Calculate cutoff dates
        event_cutoff = datetime.utcnow() - timedelta(days=settings.event_retention_days)
        snapshot_cutoff = datetime.utcnow() - timedelta(days=settings.snapshot_retention_days)
        
        # Count old events
        old_events_result = await db.execute(
            select(Event).where(Event.created_at < event_cutoff)
        )
        old_events_count = len(old_events_result.scalars().all())
        
        # Count old snapshots
        old_snapshots_result = await db.execute(
            select(Snapshot).where(Snapshot.taken_at < snapshot_cutoff)
        )
        old_snapshots_count = len(old_snapshots_result.scalars().all())
        
        return {
            "old_events_count": old_events_count,
            "old_snapshots_count": old_snapshots_count,
            "event_cutoff": event_cutoff.isoformat(),
            "snapshot_cutoff": snapshot_cutoff.isoformat(),
            "event_retention_days": settings.event_retention_days,
            "snapshot_retention_days": settings.snapshot_retention_days
        }
        
    except Exception as e:
        logger.error(f"Error getting retention stats: {str(e)}")
        return {"error": str(e)} 