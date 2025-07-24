#!/bin/bash

# Event Cam Deployment Package Downloader
# Securely downloads and extracts the latest deployment package from GitHub Releases

set -e

REPO="alexsimsy/pfcam"
DOWNLOAD_DIR="event-cam-deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Event Cam Deployment Package Downloader${NC}"
echo -e "${BLUE}============================================${NC}"

# Check for required tools
if ! command -v curl &> /dev/null; then
    echo -e "${RED}❌ Error: curl is required but not installed${NC}"
    exit 1
fi

if ! command -v tar &> /dev/null; then
    echo -e "${RED}❌ Error: tar is required but not installed${NC}"
    exit 1
fi

# Try to get the latest release info using GitHub API and jq
if command -v jq &> /dev/null; then
    LATEST_RELEASE_URL="https://api.github.com/repos/${REPO}/releases/latest"
    response=$(curl -s "$LATEST_RELEASE_URL")
    version=$(echo "$response" | jq -r '.tag_name')
    download_url=$(echo "$response" | jq -r '.assets[] | select(.name | contains("event-cam-deployment")) | select(.name | endswith(".tar.gz")) | .browser_download_url')
else
    # Fallback: Use the default latest release URL
    version="latest"
    download_url="https://github.com/${REPO}/releases/latest/download/event-cam-deployment-1.0.0.tar.gz"
fi

if [ -z "$download_url" ] || [ "$download_url" = "null" ]; then
    echo -e "${RED}❌ Error: Could not find a deployment package to download.${NC}"
    exit 1
fi

echo -e "${YELLOW}⬇️  Downloading deployment package...${NC}"
mkdir -p "$DOWNLOAD_DIR"
cd "$DOWNLOAD_DIR"

curl -L -o package.tar.gz "$download_url"

echo -e "${YELLOW}📦 Extracting package...${NC}"
tar -xzf package.tar.gz
rm package.tar.gz

# Find the extracted directory
extracted_dir=$(find . -maxdepth 1 -type d -name 'event-cam-deployment-*' | head -n 1 | sed 's|^./||')

if [ -z "$extracted_dir" ]; then
    echo -e "${RED}❌ Error: Could not find extracted deployment directory.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Deployment package downloaded and extracted to: ${DOWNLOAD_DIR}/${extracted_dir}${NC}"
echo -e "${BLUE}🚀 Next step: cd ${DOWNLOAD_DIR}/${extracted_dir} && ./hetzner-deploy.sh${NC}" 