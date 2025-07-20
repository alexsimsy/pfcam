#!/bin/bash

# Event Cam Admin User Setup
# Secure admin user creation with customizable credentials

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}Event Cam Admin User Setup${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Warning: Running as root. Consider running as regular user.${NC}"
    echo ""
fi

# Function to generate secure password
generate_secure_password() {
    # Generate a secure random password
    openssl rand -base64 12 | tr -d "=+/" | cut -c1-16
}

# Function to validate email
validate_email() {
    local email=$1
    if [[ $email =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Function to validate password strength
validate_password() {
    local password=$1
    # Check if password is at least 8 characters and contains at least one number
    if [[ ${#password} -ge 8 && $password =~ [0-9] ]]; then
        return 0
    else
        return 1
    fi
}

echo -e "${YELLOW}Admin User Configuration${NC}"
echo "============================="

# Get admin email
while true; do
    echo -e "${BLUE}Enter admin email address:${NC}"
    read ADMIN_EMAIL
    
    if [ -z "$ADMIN_EMAIL" ]; then
        echo -e "${YELLOW}Using default email: admin@s-imsy.com${NC}"
        ADMIN_EMAIL="admin@s-imsy.com"
        break
    elif validate_email "$ADMIN_EMAIL"; then
        break
    else
        echo -e "${RED}Invalid email format. Please enter a valid email address.${NC}"
    fi
done

# Get admin username
echo -e "${BLUE}Enter admin username (default: admin):${NC}"
read ADMIN_USERNAME
ADMIN_USERNAME=${ADMIN_USERNAME:-admin}

# Get admin password
echo -e "${BLUE}Enter admin password (or press Enter to generate secure password):${NC}"
read -s ADMIN_PASSWORD

if [ -z "$ADMIN_PASSWORD" ]; then
    ADMIN_PASSWORD=$(generate_secure_password)
    echo -e "${YELLOW}Generated secure password: $ADMIN_PASSWORD${NC}"
else
    if ! validate_password "$ADMIN_PASSWORD"; then
        echo -e "${RED}Password must be at least 8 characters and contain at least one number.${NC}"
        echo -e "${YELLOW}Generating secure password instead...${NC}"
        ADMIN_PASSWORD=$(generate_secure_password)
        echo -e "${YELLOW}Generated secure password: $ADMIN_PASSWORD${NC}"
    fi
fi

# Get admin full name
echo -e "${BLUE}Enter admin full name (default: System Administrator):${NC}"
read ADMIN_FULL_NAME
ADMIN_FULL_NAME=${ADMIN_FULL_NAME:-System Administrator}

echo ""
echo -e "${GREEN}Configuration Summary:${NC}"
echo "Email: $ADMIN_EMAIL"
echo "Username: $ADMIN_USERNAME"
echo "Full Name: $ADMIN_FULL_NAME"
echo "Password: $ADMIN_PASSWORD"
echo ""

echo -e "${YELLOW}Press Enter to create admin user...${NC}"
read

# Create admin user using the backend script
echo -e "${YELLOW}Creating admin user...${NC}"

# Check if we're in a Docker environment
if [ -f "docker-compose.yml" ]; then
    echo -e "${BLUE}Detected Docker environment, using Docker commands${NC}"
    
    # Create a temporary Python script with the custom credentials
    cat > temp_admin_setup.py << EOF
#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent / "backend"))

from app.core.database import engine, Base
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import structlog

logger = structlog.get_logger()

async def create_custom_admin():
    """Create admin user with custom credentials"""
    try:
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            # Check if admin user already exists
            result = await session.execute(
                text("SELECT id FROM users WHERE email = '$ADMIN_EMAIL'")
            )
            if result.scalar_one_or_none():
                logger.info("Admin user already exists, updating credentials")
                # Update existing admin user
                admin_user = await session.execute(
                    text("SELECT * FROM users WHERE email = '$ADMIN_EMAIL'")
                ).scalar_one()
                admin_user.email = "$ADMIN_EMAIL"
                admin_user.username = "$ADMIN_USERNAME"
                admin_user.hashed_password = get_password_hash("$ADMIN_PASSWORD")
                admin_user.full_name = "$ADMIN_FULL_NAME"
                admin_user.role = UserRole.ADMIN
                admin_user.is_active = True
            else:
                # Create new admin user
                admin_user = User(
                    email="$ADMIN_EMAIL",
                    username="$ADMIN_USERNAME",
                    hashed_password=get_password_hash("$ADMIN_PASSWORD"),
                    full_name="$ADMIN_FULL_NAME",
                    role=UserRole.ADMIN,
                    is_active=True
                )
                session.add(admin_user)
            
            await session.commit()
            logger.info("Admin user created/updated successfully")
            
    except Exception as e:
        logger.error("Failed to create admin user", error=str(e))
        raise

async def main():
    await create_custom_admin()
    print("✅ Admin user created successfully!")

if __name__ == "__main__":
    asyncio.run(main())
EOF

    # Run the admin setup
    docker compose exec backend python temp_admin_setup.py
    
    # Clean up
    rm -f temp_admin_setup.py
    
else
    echo -e "${BLUE}Using direct Python execution${NC}"
    cd backend
    python3 -c "
import asyncio
import os
import sys
sys.path.append('.')
from app.core.database import engine, Base
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

async def create_custom_admin():
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        admin_user = User(
            email='$ADMIN_EMAIL',
            username='$ADMIN_USERNAME',
            hashed_password=get_password_hash('$ADMIN_PASSWORD'),
            full_name='$ADMIN_FULL_NAME',
            role=UserRole.ADMIN,
            is_active=True
        )
        session.add(admin_user)
        await session.commit()

asyncio.run(create_custom_admin())
"
    cd ..
fi

echo ""
echo -e "${GREEN}✅ Admin user created successfully!${NC}"
echo ""
echo -e "${BLUE}Admin User Details:${NC}"
echo "Email: $ADMIN_EMAIL"
echo "Username: $ADMIN_USERNAME"
echo "Full Name: $ADMIN_FULL_NAME"
echo "Password: $ADMIN_PASSWORD"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo "1. Save these credentials securely"
echo "2. Change the password after first login"
echo "3. Enable two-factor authentication if available"
echo ""
echo -e "${BLUE}You can now login to Event Cam with these credentials!${NC}" 