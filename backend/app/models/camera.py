from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base

class Camera(Base):
    __tablename__ = "cameras"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    ip_address = Column(String, nullable=False, unique=True)
    port = Column(Integer, default=80)
    base_url = Column(String, nullable=False)
    
    # Connection settings
    username = Column(String)
    password = Column(String)
    use_ssl = Column(Boolean, default=False)
    
    # Camera information
    model = Column(String)
    firmware_version = Column(String)
    serial_number = Column(String)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime(timezone=True))
    
    # Configuration
    settings = Column(JSON)  # Store camera settings as JSON
    camera_metadata = Column(JSON)  # Additional metadata
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    events = relationship("Event", back_populates="camera")
    
    def get_api_url(self) -> str:
        """Get the full API URL for this camera"""
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.ip_address}:{self.port}"
    
    def get_web_url(self) -> str:
        """Get the web interface URL for this camera"""
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.ip_address}:{self.port}"
    
    def update_status(self, is_online: bool):
        """Update camera online status"""
        self.is_online = is_online
        if is_online:
            from datetime import datetime
            self.last_seen = datetime.utcnow() 