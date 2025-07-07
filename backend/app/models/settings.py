from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base

class ApplicationSettings(Base):
    __tablename__ = "application_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Streaming settings
    live_quality_level = Column(Integer, default=50, nullable=False)
    recording_quality_level = Column(Integer, default=50, nullable=False)
    
    # Camera settings
    heater_level = Column(Integer, default=0, nullable=False)  # 0=off, 1=low, 2=med, 3=high
    picture_rotation = Column(Integer, default=90, nullable=False)  # 0, 90, 180, 270 degrees
    
    # Storage settings
    store_data_on_camera = Column(Boolean, default=True, nullable=False)
    auto_download_events = Column(Boolean, default=False, nullable=False)
    
    # Retention settings
    event_retention_days = Column(Integer, default=30, nullable=False)
    snapshot_retention_days = Column(Integer, default=7, nullable=False)
    
    # Mobile optimization settings
    mobile_data_saving = Column(Boolean, default=True, nullable=False)
    low_bandwidth_mode = Column(Boolean, default=False, nullable=False)
    
    # Event recording settings
    pre_event_recording_seconds = Column(Integer, default=10, nullable=False)
    post_event_recording_seconds = Column(Integer, default=10, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class CameraSettings(Base):
    __tablename__ = "camera_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    camera = relationship("Camera")
    
    # Settings data stored as JSON
    settings_data = Column(JSON, nullable=False)
    
    # Settings metadata
    settings_version = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def get_setting(self, key: str, default=None):
        """Get a specific setting value"""
        return self.settings_data.get(key, default)
    
    def set_setting(self, key: str, value):
        """Set a specific setting value"""
        if not self.settings_data:
            self.settings_data = {}
        self.settings_data[key] = value
    
    def update_settings(self, new_settings: dict):
        """Update multiple settings at once"""
        if not self.settings_data:
            self.settings_data = {}
        self.settings_data.update(new_settings) 