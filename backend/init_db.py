#!/usr/bin/env python3
"""
Database initialization script.
Creates database tables and initial admin user.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import engine, Base
from app.core.config import settings
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import structlog

logger = structlog.get_logger()

async def create_tables():
    """Create all database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise

async def create_admin_user():
    """Create initial admin user"""
    try:
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            # Check if admin user already exists
            result = await session.execute(
                text("SELECT id FROM users WHERE email = 'admin@pfcam.com'")
            )
            if result.scalar_one_or_none():
                logger.info("Admin user already exists")
                return
            
            # Create admin user
            admin_user = User(
                email="admin@pfcam.com",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True
            )
            
            session.add(admin_user)
            await session.commit()
            
            logger.info("Admin user created successfully", 
                       email=admin_user.email, 
                       username=admin_user.username)
            
    except Exception as e:
        logger.error("Failed to create admin user", error=str(e))
        raise

async def main():
    """Main initialization function"""
    logger.info("Starting database initialization")
    
    try:
        # Create tables
        await create_tables()
        
        # Create admin user
        await create_admin_user()
        
        logger.info("Database initialization completed successfully")
        
        print("\n" + "="*50)
        print("DATABASE INITIALIZATION COMPLETE")
        print("="*50)
        print("Admin user created:")
        print("  Email: admin@pfcam.com")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nPlease change the admin password after first login!")
        print("="*50)
        
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        print(f"ERROR: Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 