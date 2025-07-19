from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
import structlog

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.models.user import User
from app.models.camera import Camera
from app.models.event import Event
from app.models.tag import Tag
from app.models.tag import event_tags

logger = structlog.get_logger()
router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_events"))
) -> Any:
    """Get dashboard statistics including camera counts, event counts, and events by tag"""
    
    try:
        # Camera statistics
        total_cameras = await db.execute(select(func.count(Camera.id)))
        total_count = total_cameras.scalar() or 0
        
        online_cameras = await db.execute(select(func.count(Camera.id)).where(Camera.is_online == True))
        online_count = online_cameras.scalar() or 0
        
        offline_count = total_count - online_count
        
        # Event statistics
        now = datetime.utcnow()
        twenty_four_hours_ago = now - timedelta(hours=24)
        
        # Total events (not deleted)
        total_events = await db.execute(
            select(func.count(Event.id)).where(Event.is_deleted == False)
        )
        total_events_count = total_events.scalar() or 0
        
        # Events in last 24 hours
        events_24h = await db.execute(
            select(func.count(Event.id)).where(
                and_(
                    Event.is_deleted == False,
                    Event.triggered_at >= twenty_four_hours_ago
                )
            )
        )
        events_24h_count = events_24h.scalar() or 0
        
        # Unviewed events (not played)
        unviewed_events = await db.execute(
            select(func.count(Event.id)).where(
                and_(
                    Event.is_deleted == False,
                    Event.is_played == False
                )
            )
        )
        unviewed_events_count = unviewed_events.scalar() or 0
        
        # Events by tag
        events_by_tag_query = await db.execute(
            select(
                Tag.name.label('tag_name'),
                Tag.color.label('tag_color'),
                func.count(Event.id).label('count')
            )
            .join(event_tags, Tag.id == event_tags.c.tag_id)
            .join(Event, event_tags.c.event_id == Event.id)
            .where(Event.is_deleted == False)
            .group_by(Tag.id, Tag.name, Tag.color)
            .order_by(func.count(Event.id).desc())
        )
        
        events_by_tag = [
            {
                "tag_name": row.tag_name,
                "tag_color": row.tag_color,
                "count": row.count
            }
            for row in events_by_tag_query.all()
        ]
        
        return {
            "cameras": {
                "total": total_count,
                "online": online_count,
                "offline": offline_count
            },
            "events": {
                "total": total_events_count,
                "last_24h": events_24h_count,
                "unviewed": unviewed_events_count
            },
            "events_by_tag": events_by_tag
        }
        
    except Exception as e:
        logger.error("Failed to get dashboard stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard statistics"
        ) 