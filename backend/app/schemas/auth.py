from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole

class Token(BaseModel):
    access_token: str
    token_type: str
    requires_mfa: bool = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    role: Optional[UserRole] = UserRole.VIEWER

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    mfa_enabled: bool
    email_notifications: bool
    is_active: bool
    is_verified: bool
    created_at: str
    last_login: Optional[str]

    class Config:
        from_attributes = True

class MFASetup(BaseModel):
    secret: str
    qr_code_url: str

class MFAToken(BaseModel):
    mfa_token: str
    temp_token: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email_notifications: Optional[bool] = None
    webhook_url: Optional[str] = None 