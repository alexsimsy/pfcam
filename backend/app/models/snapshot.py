from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    camera = relationship("Camera")
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    taken_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def get_download_url(self) -> str:
        return f"/api/v1/streams/snapshots/{self.id}/download" 