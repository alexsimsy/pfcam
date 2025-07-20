from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum
import pyotp

from app.core.database import Base

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER)
    
    # MFA settings
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    webhook_url = Column(String)
    event_notifications = Column(Boolean, default=True)
    camera_status_notifications = Column(Boolean, default=True)
    system_alerts = Column(Boolean, default=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    events = relationship("Event", back_populates="user")
    
    def generate_mfa_secret(self) -> str:
        """Generate a new MFA secret for the user"""
        self.mfa_secret = pyotp.random_base32()
        return self.mfa_secret
    
    def verify_mfa_token(self, token: str) -> bool:
        """Verify MFA token"""
        if not self.mfa_enabled or not self.mfa_secret:
            return False
        
        totp = pyotp.TOTP(self.mfa_secret)
        return totp.verify(token)
    
    def get_mfa_qr_code_url(self) -> str:
        """Get QR code URL for MFA setup"""
        if not self.mfa_secret:
            return ""
        
        totp = pyotp.TOTP(self.mfa_secret)
        return totp.provisioning_uri(
            name=self.email,
            issuer_name="PFCAM"
        )
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        permissions = {
            UserRole.ADMIN: [
                "view_events", "download_events", "delete_events",
                "manage_events", "manage_settings", "manage_users", "view_streams",
                "manage_system", "view_cameras", "manage_cameras"
            ],
            UserRole.MANAGER: [
                "view_events", "download_events", "manage_settings",
                "view_streams", "view_cameras"
            ],
            UserRole.VIEWER: [
                "view_events", "view_streams", "view_cameras"
            ]
        }
        
        return permission in permissions.get(self.role, []) 