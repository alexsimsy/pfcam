#!/bin/bash

# WireGuard Client Configuration Generator
# Creates client configs for WireGuard VPN

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}WireGuard Client Configuration Generator${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run this script as root (use sudo)${NC}"
    exit 1
fi

# Check if WireGuard is installed
if [ ! -f "/etc/wireguard/server_public.key" ]; then
    echo -e "${RED}Error: WireGuard server not configured. Run wireguard-setup.sh first.${NC}"
    exit 1
fi

# Get client configuration
echo -e "${YELLOW}Client Configuration${NC}"
echo "========================"

echo -e "${BLUE}Enter client name (e.g., phone, laptop, camera1):${NC}"
read CLIENT_NAME

if [ -z "$CLIENT_NAME" ]; then
    echo -e "${RED}Error: Client name is required${NC}"
    exit 1
fi

echo -e "${BLUE}Enter server public IP address:${NC}"
read SERVER_IP

if [ -z "$SERVER_IP" ]; then
    echo -e "${RED}Error: Server IP is required${NC}"
    exit 1
fi

echo -e "${BLUE}Enter WireGuard port (default: 51820):${NC}"
read WG_PORT
WG_PORT=${WG_PORT:-51820}

echo -e "${BLUE}Enter VPN subnet (default: 10.0.0.0/24):${NC}"
read WG_SUBNET
WG_SUBNET=${WG_SUBNET:-10.0.0.0/24}

# Calculate client IP (increment from .2)
CLIENT_IP="${WG_SUBNET/\/24/}.2"

echo ""
echo -e "${GREEN}Configuration Summary:${NC}"
echo "Client Name: $CLIENT_NAME"
echo "Server IP: $SERVER_IP"
echo "WireGuard Port: $WG_PORT"
echo "Client IP: $CLIENT_IP"
echo ""

echo -e "${YELLOW}Press Enter to generate client configuration...${NC}"
read

# Create client directory
mkdir -p /etc/wireguard/clients
cd /etc/wireguard

# Generate client keys
echo -e "${YELLOW}Generating client keys...${NC}"
wg genkey | tee clients/${CLIENT_NAME}_private.key | wg pubkey > clients/${CLIENT_NAME}_public.key

# Set proper permissions
chmod 600 clients/${CLIENT_NAME}_private.key
chmod 644 clients/${CLIENT_NAME}_public.key

# Create client configuration
echo -e "${YELLOW}Creating client configuration...${NC}"
cat > clients/${CLIENT_NAME}.conf << EOF
[Interface]
PrivateKey = $(cat clients/${CLIENT_NAME}_private.key)
Address = $CLIENT_IP/24
DNS = 8.8.8.8, 8.8.4.4

[Peer]
PublicKey = $(cat server_public.key)
Endpoint = $SERVER_IP:$WG_PORT
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOF

# Add client to server configuration
echo -e "${YELLOW}Adding client to server configuration...${NC}"
cat >> /etc/wireguard/wg0.conf << EOF

# Client: $CLIENT_NAME
[Peer]
PublicKey = $(cat clients/${CLIENT_NAME}_public.key)
AllowedIPs = $CLIENT_IP/32
EOF

# Reload WireGuard configuration
echo -e "${YELLOW}Reloading WireGuard configuration...${NC}"
wg syncconf wg0 <(wg-quick strip wg0)

# Create QR code for easy mobile setup
echo -e "${YELLOW}Generating QR code...${NC}"
if command -v qrencode &> /dev/null; then
    qrencode -t ansiutf8 < clients/${CLIENT_NAME}.conf
else
    echo -e "${YELLOW}Install qrencode for QR code generation: apt install qrencode${NC}"
fi

echo -e "${GREEN}✅ Client configuration created successfully!${NC}"
echo ""
echo -e "${BLUE}Client Information:${NC}"
echo "Name: $CLIENT_NAME"
echo "IP Address: $CLIENT_IP"
echo "Configuration File: /etc/wireguard/clients/${CLIENT_NAME}.conf"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Copy the configuration file to your device"
echo "2. Import into WireGuard app (mobile) or install WireGuard (desktop)"
echo "3. Connect to the VPN"
echo ""
echo -e "${BLUE}Configuration file contents:${NC}"
echo "=================================="
cat clients/${CLIENT_NAME}.conf
echo "=================================="
echo ""
echo -e "${GREEN}Client $CLIENT_NAME is now ready to connect!${NC}" 