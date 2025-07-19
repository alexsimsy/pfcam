from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import require_permission
from app.models.tag import Tag
from app.models.event import Event
from app.models.user import User
from app.schemas.tags import TagCreate, TagUpdate, TagResponse, TagList, EventTagAssignment, TagUsage

router = APIRouter()

@router.get("/", response_model=TagList)
async def list_tags(
    limit: int = Query(100, le=200, description="Number of tags to return"),
    offset: int = Query(0, ge=0, description="Number of tags to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_events"))
) -> Any:
    """List all tags with usage statistics"""
    
    # Get tags with usage count
    query = select(
        Tag,
        func.count(Event.id).label('usage_count')
    ).outerjoin(Tag.events).group_by(Tag.id).order_by(desc('usage_count'), Tag.name)
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    tags_with_usage = result.all()
    
    # Process results
    tags = []
    for tag_row in tags_with_usage:
        tag = tag_row[0]
        usage_count = tag_row[1] or 0
        tags.append(TagResponse.from_orm(tag))
    
    # Get total count
    count_result = await db.execute(select(func.count(Tag.id)))
    total_count = count_result.scalar()
    
    return TagList(
        tags=tags,
        total=total_count
    )

@router.post("/", response_model=TagResponse)
async def create_tag(
    tag_data: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_system"))
) -> Any:
    """Create a new tag"""
    
    # Check if tag already exists
    existing_tag = await db.execute(select(Tag).where(Tag.name == tag_data.name))
    if existing_tag.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag with this name already exists"
        )
    
    # Create new tag
    tag = Tag(**tag_data.dict())
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    
    return TagResponse.from_orm(tag)

@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_events"))
) -> Any:
    """Get specific tag details"""
    
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    return TagResponse.from_orm(tag)

@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_system"))
) -> Any:
    """Update a tag"""
    
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    # Check if new name conflicts with existing tag
    if tag_data.name and tag_data.name != tag.name:
        existing_tag = await db.execute(select(Tag).where(Tag.name == tag_data.name))
        if existing_tag.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag with this name already exists"
            )
    
    # Update tag
    update_data = tag_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)
    
    await db.commit()
    await db.refresh(tag)
    
    return TagResponse.from_orm(tag)

@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_system"))
) -> Any:
    """Delete a tag (removes from all events)"""
    
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    # Remove tag from all events (association table will be cleaned up automatically)
    await db.delete(tag)
    await db.commit()
    
    return {"message": "Tag deleted successfully"}

@router.post("/assign", response_model=dict)
async def assign_tags_to_event(
    assignment: EventTagAssignment,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("manage_events"))
) -> Any:
    """Assign tags to an event"""
    
    # Get the event with tags eagerly loaded
    event_result = await db.execute(
        select(Event)
        .options(selectinload(Event.tags))
        .where(Event.id == assignment.event_id)
    )
    event = event_result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Get the tags
    if assignment.tag_ids:
        tags_result = await db.execute(select(Tag).where(Tag.id.in_(assignment.tag_ids)))
        tags = tags_result.scalars().all()
        
        if len(tags) != len(assignment.tag_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more tags not found"
            )
    else:
        tags = []
    
    # Clear existing tags and assign new ones
    event.tags = tags
    await db.commit()
    
    return {"message": f"Assigned {len(tags)} tags to event"}

@router.get("/usage/stats", response_model=List[TagUsage])
async def get_tag_usage_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("view_events"))
) -> Any:
    """Get tag usage statistics"""
    
    query = select(
        Tag,
        func.count(Event.id).label('usage_count')
    ).outerjoin(Tag.events).group_by(Tag.id).order_by(desc('usage_count'), Tag.name)
    
    result = await db.execute(query)
    tags_with_usage = result.all()
    
    usage_stats = []
    for tag_row in tags_with_usage:
        tag = tag_row[0]
        usage_count = tag_row[1] or 0
        usage_stats.append(TagUsage(
            tag=TagResponse.from_orm(tag),
            usage_count=usage_count
        ))
    
    return usage_stats 