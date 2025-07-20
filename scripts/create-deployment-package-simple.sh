#!/bin/bash

# Simple Event Cam Deployment Package Creator
# This is a minimal version for testing GitHub Actions

set -e

echo "🚀 Creating Simple Event Cam Deployment Package"

# Configuration
PACKAGE_NAME="event-cam-deployment"
VERSION="1.0.0"
BUILD_DIR="build"
PACKAGE_DIR="${BUILD_DIR}/${PACKAGE_NAME}-${VERSION}"

echo "📁 Creating build directory..."
rm -rf "${BUILD_DIR}"
mkdir -p "${PACKAGE_DIR}"

echo "📦 Copying essential files..."

# Copy only essential files that we know exist
if [ -f "scripts/hetzner-deploy.sh" ]; then
    cp scripts/hetzner-deploy.sh "${PACKAGE_DIR}/"
    echo "✅ Copied hetzner-deploy.sh"
fi

if [ -f "docker-compose.production.yml" ]; then
    cp docker-compose.production.yml "${PACKAGE_DIR}/"
    echo "✅ Copied docker-compose.production.yml"
fi

if [ -f "README.md" ]; then
    cp README.md "${PACKAGE_DIR}/"
    echo "✅ Copied README.md"
fi

# Create a simple README for the package
cat > "${PACKAGE_DIR}/PACKAGE_README.md" << EOF
# Event Cam Deployment Package v${VERSION}

This is a simplified deployment package for testing.

## Contents
- hetzner-deploy.sh: Main deployment script
- docker-compose.production.yml: Production configuration
- README.md: Project documentation

## Usage
1. Extract the package
2. Run: chmod +x hetzner-deploy.sh
3. Run: ./hetzner-deploy.sh

Created: $(date)
EOF

echo "📦 Creating package archive..."
cd "${BUILD_DIR}"
tar -czf "${PACKAGE_NAME}-${VERSION}.tar.gz" "${PACKAGE_NAME}-${VERSION}/"
echo "✅ Created ${PACKAGE_NAME}-${VERSION}.tar.gz"

echo "📝 Creating release notes..."
cat > "RELEASE_NOTES.md" << EOF
# Event Cam Deployment Package v${VERSION}

## What's Included
- Simplified deployment package for testing
- Essential deployment scripts
- Production Docker configuration

## Quick Start
1. Extract the package
2. Run: chmod +x hetzner-deploy.sh
3. Run: ./hetzner-deploy.sh

Created: $(date)
EOF

cd ..

echo "✅ Simple deployment package created successfully!"
echo "📁 Location: ${BUILD_DIR}/${PACKAGE_NAME}-${VERSION}"
echo "📦 Archive: ${BUILD_DIR}/${PACKAGE_NAME}-${VERSION}.tar.gz" 