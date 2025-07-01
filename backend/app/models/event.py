from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Camera relationship
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    camera = relationship("Camera", back_populates="events")
    
    # User who downloaded/processed the event
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="events")
    
    # Event information from camera
    filename = Column(String, nullable=False, index=True)
    event_name = Column(String, index=True)
    triggered_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # File information
    file_size = Column(BigInteger)  # Size in bytes
    file_path = Column(String)  # Local storage path
    thumbnail_path = Column(String)  # Thumbnail path
    
    # File extensions
    video_extension = Column(String)  # .mp4, .avi, etc.
    thumbnail_extension = Column(String)  # .jpg, .png, etc.
    
    # Playback information
    playback_time = Column(Integer)  # Duration in seconds
    
    # Status
    is_downloaded = Column(Boolean, default=False)
    is_processed = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    
    # Additional metadata
    event_metadata = Column(JSON)  # Store additional event data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def get_file_url(self) -> str:
        """Get URL to download the event file"""
        return f"/api/v1/events/{self.id}/download"
    
    def get_thumbnail_url(self) -> str:
        """Get URL to view the event thumbnail"""
        return f"/api/v1/events/{self.id}/thumbnail"
    
    def get_playback_url(self) -> str:
        """Get URL to stream the event video"""
        return f"/api/v1/events/{self.id}/playback" 