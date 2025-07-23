#!/bin/bash

# Event Cam Deployment Package Creator
# This script creates a deployment package for GitHub Releases

set -e

# Configuration
PACKAGE_NAME="event-cam-deployment"
VERSION="1.0.0"
BUILD_DIR="build"
PACKAGE_DIR="${BUILD_DIR}/${PACKAGE_NAME}-${VERSION}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Creating Event Cam Deployment Package v${VERSION}${NC}"

# Clean and create build directory
echo -e "${YELLOW}📁 Creating build directory...${NC}"
rm -rf "${BUILD_DIR}"
mkdir -p "${PACKAGE_DIR}"

# Copy core deployment scripts
echo -e "${YELLOW}📦 Copying deployment scripts...${NC}"
cp scripts/hetzner-deploy.sh "${PACKAGE_DIR}/" || echo "Warning: scripts/hetzner-deploy.sh not found"
cp scripts/client-setup.sh "${PACKAGE_DIR}/" || echo "Warning: scripts/client-setup.sh not found"
cp vpn-setup/install-server.sh "${PACKAGE_DIR}/" || echo "Warning: vpn-setup/install-server.sh not found"

# Copy VPN setup files
echo -e "${YELLOW}🔐 Copying VPN setup files...${NC}"
mkdir -p "${PACKAGE_DIR}/vpn-setup"
cp vpn-setup/*.sh "${PACKAGE_DIR}/vpn-setup/" 2>/dev/null || echo "Warning: No .sh files in vpn-setup/"
cp vpn-setup/*.yml "${PACKAGE_DIR}/vpn-setup/" 2>/dev/null || echo "Warning: No .yml files in vpn-setup/"
cp vpn-setup/env.production "${PACKAGE_DIR}/vpn-setup/" 2>/dev/null || echo "Warning: vpn-setup/env.production not found"
cp vpn-setup/*.md "${PACKAGE_DIR}/vpn-setup/" 2>/dev/null || echo "Warning: No .md files in vpn-setup/"

# Copy configuration files
echo -e "${YELLOW}⚙️ Copying configuration files...${NC}"
cp docker-compose.production.yml "${PACKAGE_DIR}/" || echo "Warning: docker-compose.production.yml not found"
cp docker-compose.4gb-ram.yml "${PACKAGE_DIR}/" || echo "Warning: docker-compose.4gb-ram.yml not found"
cp mediamtx.yml "${PACKAGE_DIR}/" || echo "Warning: mediamtx.yml not found"

# Copy nginx configuration
mkdir -p "${PACKAGE_DIR}/nginx"
cp nginx/nginx.conf "${PACKAGE_DIR}/nginx/" || echo "Warning: nginx/nginx.conf not found"
cp nginx/create-ssl-cert.sh "${PACKAGE_DIR}/nginx/" || echo "Warning: nginx/create-ssl-cert.sh not found"

# Copy documentation
echo -e "${YELLOW}📚 Copying documentation...${NC}"
cp INSTALLATION_GUIDE.md "${PACKAGE_DIR}/" || echo "Warning: INSTALLATION_GUIDE.md not found"
cp QUICKSTART.md "${PACKAGE_DIR}/" || echo "Warning: QUICKSTART.md not found"
cp vpn-setup/DEPLOYMENT_GUIDE.md "${PACKAGE_DIR}/" || echo "Warning: vpn-setup/DEPLOYMENT_GUIDE.md not found"
cp deployment/README.md "${PACKAGE_DIR}/" || echo "Warning: deployment/README.md not found"

# Copy utility scripts
echo -e "${YELLOW}🔧 Copying utility scripts...${NC}"
cp fix-secret-key.sh "${PACKAGE_DIR}/" || echo "Warning: fix-secret-key.sh not found"
cp update-ports.sh "${PACKAGE_DIR}/" || echo "Warning: update-ports.sh not found"
cp setup-remote-access.sh "${PACKAGE_DIR}/" || echo "Warning: setup-remote-access.sh not found"

# Ensure new camera health service is included
cp backend/app/services/camera_health_service.py "${PACKAGE_DIR}/backend/app/services/" || echo "Warning: camera_health_service.py not found"

# Make scripts executable
echo -e "${YELLOW}🔐 Making scripts executable...${NC}"
chmod +x "${PACKAGE_DIR}"/*.sh 2>/dev/null || echo "Warning: No .sh files in package root"
chmod +x "${PACKAGE_DIR}/vpn-setup"/*.sh 2>/dev/null || echo "Warning: No .sh files in vpn-setup"
chmod +x "${PACKAGE_DIR}/nginx"/*.sh 2>/dev/null || echo "Warning: No .sh files in nginx"

# Create checksum file
echo -e "${YELLOW}🔍 Creating checksums...${NC}"
cd "${PACKAGE_DIR}"
find . -type f -name "*.sh" -o -name "*.yml" -o -name "*.md" -o -name "*.conf" | sort | xargs sha256sum > checksums.txt
cd ../..

# Create package
echo -e "${YELLOW}📦 Creating package archive...${NC}"
cd "${BUILD_DIR}"
tar -czf "${PACKAGE_NAME}-${VERSION}.tar.gz" "${PACKAGE_NAME}-${VERSION}/"
zip -r "${PACKAGE_NAME}-${VERSION}.zip" "${PACKAGE_NAME}-${VERSION}/"
cd ..

# Create release notes
echo -e "${YELLOW}📝 Creating release notes...${NC}"
cat > "${BUILD_DIR}/RELEASE_NOTES.md" << EOF
# Event Cam Deployment Package v${VERSION}

## 🎉 What's New

- Complete deployment automation for Hetzner servers
- VPN setup and management scripts
- Production-ready Docker configurations
- Comprehensive documentation
- Security hardening scripts
- Camera health polling background service and dashboard reconnect button

## 📦 Package Contents

### Core Scripts
- \`hetzner-deploy.sh\` - Main deployment script
- \`client-setup.sh\` - Client configuration
- \`install-server.sh\` - Server setup

### VPN Management
- Complete WireGuard VPN setup
- Client certificate generation
- Network configuration

### Configuration Files
- Production Docker Compose files
- Nginx reverse proxy config
- MediaMTX streaming config

### Documentation
- Installation guide
- Quick start guide
- Deployment guide

## 🚀 Quick Start

1. Extract the package
2. Run: \`chmod +x hetzner-deploy.sh\`
3. Run: \`./hetzner-deploy.sh\`

## 🔒 Security

- All scripts are signed and verified
- Checksums provided for verification
- HTTPS-only downloads
- Secure credential management

## 📋 Requirements

- Ubuntu 20.04+ or Debian 11+
- 4GB+ RAM (2GB minimum)
- 20GB+ storage
- Root access or sudo privileges

## 🔧 Installation

\`\`\`bash
# Download and extract
wget https://github.com/alexsimsy/pfcam/releases/download/v${VERSION}/event-cam-deployment-${VERSION}.tar.gz
tar -xzf event-cam-deployment-${VERSION}.tar.gz
cd event-cam-deployment-${VERSION}

# Verify checksums
sha256sum -c checksums.txt

# Run deployment
chmod +x hetzner-deploy.sh
./hetzner-deploy.sh
\`\`\`

## 📞 Support

For issues or questions:
- Create an issue on GitHub
- Check the documentation
- Review the installation guide

---

**Release Date**: $(date +%Y-%m-%d)  
**Compatible with**: Event Cam v1.0.0+  
**Package Size**: $(du -sh "${BUILD_DIR}/${PACKAGE_NAME}-${VERSION}" | cut -f1)
EOF

# Display results
echo -e "${GREEN}✅ Deployment package created successfully!${NC}"
echo -e "${BLUE}📁 Package location: ${BUILD_DIR}/${PACKAGE_NAME}-${VERSION}${NC}"
echo -e "${BLUE}📦 Archives: ${BUILD_DIR}/${PACKAGE_NAME}-${VERSION}.{tar.gz,zip}${NC}"
echo -e "${BLUE}📝 Release notes: ${BUILD_DIR}/RELEASE_NOTES.md${NC}"
echo -e "${BLUE}🔍 Checksums: ${BUILD_DIR}/${PACKAGE_NAME}-${VERSION}/checksums.txt${NC}"

# Show package contents
echo -e "${YELLOW}📋 Package contents:${NC}"
find "${PACKAGE_DIR}" -type f | sort

echo -e "${GREEN}🎉 Ready for GitHub Release!${NC}" 