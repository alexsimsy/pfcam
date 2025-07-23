#!/bin/bash

# VPN Choice Script for Event Cam
# Lets users choose between OpenVPN and WireGuard

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}Event Cam VPN Setup - Choose Your VPN${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

echo -e "${YELLOW}Please choose your VPN solution:${NC}"
echo ""
echo -e "${BLUE}1. OpenVPN (Recommended for Enterprise)${NC}"
echo "   ✅ Mature and battle-tested"
echo "   ✅ Certificate-based authentication"
echo "   ✅ Extensive configuration options"
echo "   ✅ Wide platform compatibility"
echo "   ⚠️  More complex setup"
echo ""
echo -e "${BLUE}2. WireGuard (Recommended for Modern)${NC}"
echo "   ✅ Simple and fast"
echo "   ✅ Modern cryptography"
echo "   ✅ Easy client setup"
echo "   ✅ Better performance"
echo "   ⚠️  Newer technology"
echo ""
echo -e "${BLUE}3. Exit${NC}"
echo ""

while true; do
    echo -e "${YELLOW}Enter your choice (1, 2, or 3):${NC}"
    read -r choice
    
    case $choice in
        1)
            echo ""
            echo -e "${GREEN}You selected OpenVPN${NC}"
            echo -e "${YELLOW}Starting OpenVPN setup...${NC}"
            echo ""
            
            # Check if OpenVPN script exists
            if [ -f "install-server.sh" ]; then
                chmod +x install-server.sh
                ./install-server.sh
            else
                echo -e "${RED}Error: OpenVPN setup script not found${NC}"
                exit 1
            fi
            break
            ;;
        2)
            echo ""
            echo -e "${GREEN}You selected WireGuard${NC}"
            echo -e "${YELLOW}Starting WireGuard setup...${NC}"
            echo ""
            
            # Check if WireGuard script exists
            if [ -f "wireguard-setup.sh" ]; then
                chmod +x wireguard-setup.sh
                ./wireguard-setup.sh
            else
                echo -e "${RED}Error: WireGuard setup script not found${NC}"
                exit 1
            fi
            break
            ;;
        3)
            echo ""
            echo -e "${YELLOW}Exiting VPN setup${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please enter 1, 2, or 3.${NC}"
            ;;
    esac
done

echo ""
echo -e "${GREEN}✅ VPN setup completed!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
if [ "$choice" = "1" ]; then
    echo "1. Create client certificates: ./create-client.sh"
    echo "2. Configure client devices with .ovpn files"
    echo "3. Test connectivity"
elif [ "$choice" = "2" ]; then
    echo "1. Create client configurations: ./create-wireguard-client.sh"
    echo "2. Import .conf files into WireGuard apps"
    echo "3. Test connectivity"
fi
echo ""
echo -e "${BLUE}Your Event Cam VPN is now ready!${NC}" 