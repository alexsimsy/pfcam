#!/usr/bin/env python3
"""
Simple script to reset admin user credentials
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables explicitly
os.environ["DATABASE_URL"] = "postgresql://pfcam:pfcam@localhost:5432/pfcam"
os.environ["SECRET_KEY"] = "your-super-secret-key-for-development-only-32-chars"

from app.core.database import get_db
from app.models.user import User
from app.core.security import get_password_hash

async def reset_admin():
    """Reset admin user credentials"""
    async for db in get_db():
        try:
            # Check if admin user exists
            admin_user = await db.get(User, 1)  # Assuming admin has ID 1
            
            if admin_user:
                print(f"Found existing admin user: {admin_user.email}")
                # Update email and password
                admin_user.email = "admin@pfcam.com"
                admin_user.hashed_password = get_password_hash("admin123")
                await db.commit()
                print("✅ Admin credentials updated successfully!")
            else:
                print("No admin user found, creating new one...")
                # Create new admin user
                admin_user = User(
                    email="admin@pfcam.com",
                    hashed_password=get_password_hash("admin123"),
                    is_active=True,
                    is_superuser=True
                )
                db.add(admin_user)
                await db.commit()
                print("✅ Admin user created successfully!")
            
            print(f"Email: admin@pfcam.com")
            print(f"Password: admin123")
            break
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()
        finally:
            await db.close()

if __name__ == "__main__":
    print("Using database URL:", os.environ["DATABASE_URL"])
    asyncio.run(reset_admin()) 