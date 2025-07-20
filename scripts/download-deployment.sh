#!/bin/bash

# Event Cam Deployment Package Downloader
# Secure download script for deployment packages

set -e

# Configuration
REPO="alexsimsy/pfcam"
LATEST_RELEASE_URL="https://api.github.com/repos/${REPO}/releases/latest"
DOWNLOAD_DIR="event-cam-deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Event Cam Deployment Package Downloader${NC}"
echo -e "${BLUE}============================================${NC}"

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo -e "${RED}❌ Error: curl is required but not installed${NC}"
    exit 1
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: jq not found, will download latest release${NC}"
    JQ_AVAILABLE=false
else
    JQ_AVAILABLE=true
fi

# Function to get latest release info
get_latest_release() {
    if [ "$JQ_AVAILABLE" = true ]; then
        local response=$(curl -s "$LATEST_RELEASE_URL")
        local version=$(echo "$response" | jq -r '.tag_name')
        local download_url=$(echo "$response" | jq -r '.assets[] | select(.name | contains("event-cam-deployment")) | select(.name | endswith(".tar.gz")) | .browser_download_url')
        echo "$version|$download_url"
    else
        echo "v1.0.0|https://github.com/${REPO}/releases/latest/download/event-cam-deployment-1.0.0.tar.gz"
    fi
}

# Function to download and verify package
download_package() {
    local version="$1"
    local download_url="$2"
    local filename="event-cam-deployment-${version#v}.tar.gz"
    
    echo -e "${YELLOW}📦 Downloading Event Cam Deployment Package ${version}...${NC}"
    
    # Create download directory
    mkdir -p "$DOWNLOAD_DIR"
    cd "$DOWNLOAD_DIR"
    
    # Download the package
    echo -e "${YELLOW}⬇️  Downloading from: ${download_url}${NC}"
    curl -L -o "$filename" "$download_url"
    
    if [ ! -f "$filename" ]; then
        echo -e "${RED}❌ Error: Failed to download package${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Download completed: ${filename}${NC}"
    
    # Extract the package
    echo -e "${YELLOW}📁 Extracting package...${NC}"
    tar -xzf "$filename"
    
    # Find the extracted directory
    local extracted_dir=$(find . -maxdepth 1 -type d -name "event-cam-deployment-*" | head -n 1)
    
    if [ -z "$extracted_dir" ]; then
        echo -e "${RED}❌ Error: Failed to extract package${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Package extracted to: ${extracted_dir}${NC}"
    
    # Verify checksums if available
    if [ -f "${extracted_dir}/checksums.txt" ]; then
        echo -e "${YELLOW}🔍 Verifying checksums...${NC}"
        cd "$extracted_dir"
        if sha256sum -c checksums.txt; then
            echo -e "${GREEN}✅ Checksums verified successfully${NC}"
        else
            echo -e "${RED}❌ Error: Checksum verification failed${NC}"
            exit 1
        fi
        cd ..
    else
        echo -e "${YELLOW}⚠️  No checksums file found, skipping verification${NC}"
    fi
    
    # Make scripts executable
    echo -e "${YELLOW}🔐 Making scripts executable...${NC}"
    find "$extracted_dir" -name "*.sh" -exec chmod +x {} \;
    
    echo -e "${GREEN}✅ Package ready for deployment!${NC}"
    echo -e "${BLUE}📁 Location: ${DOWNLOAD_DIR}/${extracted_dir}${NC}"
    echo -e "${BLUE}🚀 Next step: cd ${DOWNLOAD_DIR}/${extracted_dir} && ./hetzner-deploy.sh${NC}"
}

# Function to show available releases
show_releases() {
    echo -e "${YELLOW}📋 Available releases:${NC}"
    if [ "$JQ_AVAILABLE" = true ]; then
        local releases=$(curl -s "https://api.github.com/repos/${REPO}/releases" | jq -r '.[] | "\(.tag_name) - \(.published_at)"')
        echo "$releases"
    else
        echo -e "${YELLOW}Visit: https://github.com/${REPO}/releases${NC}"
    fi
}

# Main script logic
main() {
    # Parse command line arguments
    case "${1:-latest}" in
        "latest")
            echo -e "${YELLOW}🔍 Getting latest release information...${NC}"
            local release_info=$(get_latest_release)
            local version=$(echo "$release_info" | cut -d'|' -f1)
            local download_url=$(echo "$release_info" | cut -d'|' -f2)
            
            if [ "$download_url" = "null" ] || [ -z "$download_url" ]; then
                echo -e "${RED}❌ Error: No deployment package found in latest release${NC}"
                show_releases
                exit 1
            fi
            
            download_package "$version" "$download_url"
            ;;
        "list")
            show_releases
            ;;
        "help"|"-h"|"--help")
            echo -e "${BLUE}Usage: $0 [COMMAND]${NC}"
            echo -e "${BLUE}Commands:${NC}"
            echo -e "  latest  - Download latest release (default)"
            echo -e "  list    - Show available releases"
            echo -e "  help    - Show this help message"
            echo -e ""
            echo -e "${BLUE}Examples:${NC}"
            echo -e "  $0                    # Download latest release"
            echo -e "  $0 latest             # Download latest release"
            echo -e "  $0 list               # Show available releases"
            ;;
        *)
            echo -e "${RED}❌ Error: Unknown command '$1'${NC}"
            echo -e "${YELLOW}Use '$0 help' for usage information${NC}"
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 