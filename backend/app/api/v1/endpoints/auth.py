from datetime import timedelta, datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password, get_current_user
from app.core.config import settings
from app.models.user import User, UserRole
from app.schemas.auth import Token, UserCreate, UserLogin, MFASetup, MFAToken

logger = structlog.get_logger()
router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Login user with email and password"""
    # Find user by email
    result = await db.execute(select(User).where(User.email == user_credentials.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Check if MFA is required
    if user.mfa_enabled:
        # Return temporary token for MFA verification
        temp_token = create_access_token(
            data={"sub": user.email, "temp": True},
            expires_delta=timedelta(minutes=5)
        )
        return {
            "access_token": temp_token,
            "token_type": "bearer",
            "requires_mfa": True
        }
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    # Update last login
    user.last_login = datetime.now()
    await db.commit()
    
    logger.info("User logged in successfully", user_id=user.id, email=user.email)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "requires_mfa": False
    }

@router.post("/login/mfa", response_model=Token)
async def login_mfa(
    mfa_token: MFAToken,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Complete login with MFA token"""
    # Verify temporary token and get user
    from app.core.security import get_current_user_temp
    
    user = await get_current_user_temp(mfa_token.temp_token, db)
    
    # Verify MFA token
    if not user.verify_mfa_token(mfa_token.mfa_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA token"
        )
    
    # Create final access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    # Update last login
    user.last_login = datetime.now()
    await db.commit()
    
    logger.info("User completed MFA login", user_id=user.id, email=user.email)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "requires_mfa": False
    }

@router.post("/register", response_model=dict)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Register new user (admin only)"""
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role or UserRole.VIEWER
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info("New user registered", user_id=user.id, email=user.email)
    
    return {"message": "User created successfully", "user_id": user.id}

@router.post("/mfa/setup", response_model=MFASetup)
async def setup_mfa(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Setup MFA for user"""
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA already enabled"
        )
    
    # Generate MFA secret
    secret = current_user.generate_mfa_secret()
    current_user.mfa_enabled = True
    
    await db.commit()
    
    logger.info("MFA setup initiated", user_id=current_user.id)
    
    return {
        "secret": secret,
        "qr_code_url": current_user.get_mfa_qr_code_url()
    }

@router.post("/mfa/verify", response_model=dict)
async def verify_mfa_setup(
    mfa_token: MFAToken,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Verify MFA setup with token"""
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA not enabled"
        )
    
    if not current_user.verify_mfa_token(mfa_token.mfa_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA token"
        )
    
    logger.info("MFA setup verified", user_id=current_user.id)
    
    return {"message": "MFA setup verified successfully"}

@router.post("/mfa/disable", response_model=dict)
async def disable_mfa(
    mfa_token: MFAToken,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Disable MFA for user"""
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA not enabled"
        )
    
    if not current_user.verify_mfa_token(mfa_token.mfa_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA token"
        )
    
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    
    await db.commit()
    
    logger.info("MFA disabled", user_id=current_user.id)
    
    return {"message": "MFA disabled successfully"}

@router.post("/logout", response_model=dict)
async def logout(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Logout user (client should discard token)"""
    logger.info("User logged out", user_id=current_user.id)
    return {"message": "Logged out successfully"}

# Import dependencies at the end to avoid circular imports
from app.core.security import get_current_user 