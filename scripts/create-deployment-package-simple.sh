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

# Copy VPN setup files
echo "📦 Copying VPN setup files..."
mkdir -p "${PACKAGE_DIR}/vpn-setup"

# Copy OpenVPN files
if [ -f "vpn-setup/install-server.sh" ]; then
    cp vpn-setup/install-server.sh "${PACKAGE_DIR}/vpn-setup/"
    echo "✅ Copied OpenVPN server setup"
fi

if [ -f "vpn-setup/create-client.sh" ]; then
    cp vpn-setup/create-client.sh "${PACKAGE_DIR}/vpn-setup/"
    echo "✅ Copied OpenVPN client setup"
fi

if [ -f "vpn-setup/docker-compose.vpn.yml" ]; then
    cp vpn-setup/docker-compose.vpn.yml "${PACKAGE_DIR}/vpn-setup/"
    echo "✅ Copied OpenVPN Docker config"
fi

# Copy WireGuard files
if [ -f "vpn-setup/wireguard-setup.sh" ]; then
    cp vpn-setup/wireguard-setup.sh "${PACKAGE_DIR}/vpn-setup/"
    echo "✅ Copied WireGuard server setup"
fi

if [ -f "vpn-setup/create-wireguard-client.sh" ]; then
    cp vpn-setup/create-wireguard-client.sh "${PACKAGE_DIR}/vpn-setup/"
    echo "✅ Copied WireGuard client setup"
fi

if [ -f "vpn-setup/docker-compose.wireguard.yml" ]; then
    cp vpn-setup/docker-compose.wireguard.yml "${PACKAGE_DIR}/vpn-setup/"
    echo "✅ Copied WireGuard Docker config"
fi

# Copy VPN choice script
if [ -f "vpn-setup/choose-vpn.sh" ]; then
    cp vpn-setup/choose-vpn.sh "${PACKAGE_DIR}/vpn-setup/"
    echo "✅ Copied VPN choice script"
fi

# Copy admin setup script
if [ -f "scripts/setup-admin.sh" ]; then
    cp scripts/setup-admin.sh "${PACKAGE_DIR}/"
    echo "✅ Copied admin setup script"
fi

# Create a simple README for the package
cat > "${PACKAGE_DIR}/PACKAGE_README.md" << EOF
# Event Cam Deployment Package v${VERSION}

Complete deployment package with dual VPN support.

## Contents
- hetzner-deploy.sh: Main deployment script
- docker-compose.production.yml: Production configuration
- README.md: Project documentation
- vpn-setup/: VPN configuration files

## VPN Options
This package includes both VPN solutions:

### OpenVPN (Enterprise)
- Mature and battle-tested
- Certificate-based authentication
- Extensive configuration options
- Wide platform compatibility

### WireGuard (Modern)
- Simple and fast
- Modern cryptography
- Easy client setup
- Better performance

## Usage
1. Extract the package
2. Run: chmod +x hetzner-deploy.sh
3. Run: ./hetzner-deploy.sh
4. Choose your VPN: cd vpn-setup && ./choose-vpn.sh
5. Setup admin user: ./setup-admin.sh (optional - custom credentials)

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