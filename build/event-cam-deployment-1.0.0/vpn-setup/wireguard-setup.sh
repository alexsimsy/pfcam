#!/bin/bash

# WireGuard VPN Setup for Event Cam
# Alternative to OpenVPN - modern, fast, simple

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}WireGuard VPN Setup for Event Cam${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run this script as root (use sudo)${NC}"
    exit 1
fi

# Get server configuration
echo -e "${YELLOW}WireGuard Server Configuration${NC}"
echo "====================================="

echo -e "${BLUE}Enter your server's public IP address:${NC}"
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

echo ""
echo -e "${GREEN}Configuration Summary:${NC}"
echo "Server IP: $SERVER_IP"
echo "WireGuard Port: $WG_PORT"
echo "VPN Subnet: $WG_SUBNET"
echo ""

echo -e "${YELLOW}Press Enter to continue with WireGuard installation...${NC}"
read

# Step 1: Install WireGuard
echo -e "${BLUE}Step 1: Installing WireGuard${NC}"
echo "================================"

echo -e "${YELLOW}Updating system packages...${NC}"
apt update

echo -e "${YELLOW}Installing WireGuard...${NC}"
apt install -y wireguard wireguard-tools

# Step 2: Generate WireGuard Keys
echo -e "${BLUE}Step 2: Generating WireGuard Keys${NC}"
echo "====================================="

# Create WireGuard directory
mkdir -p /etc/wireguard
cd /etc/wireguard

# Generate server keys
echo -e "${YELLOW}Generating server keys...${NC}"
wg genkey | tee server_private.key | wg pubkey > server_public.key

# Set proper permissions
chmod 600 server_private.key
chmod 644 server_public.key

# Step 3: Configure WireGuard Server
echo -e "${BLUE}Step 3: Configuring WireGuard Server${NC}"
echo "========================================="

# Create server configuration
cat > /etc/wireguard/wg0.conf << EOF
[Interface]
PrivateKey = $(cat server_private.key)
Address = ${WG_SUBNET/\/24/}.1/24
ListenPort = $WG_PORT
SaveConfig = true
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Enable IP forwarding
PostUp = echo 1 > /proc/sys/net/ipv4/ip_forward
PostDown = echo 0 > /proc/sys/net/ipv4/ip_forward
EOF

# Enable IP forwarding permanently
echo 'net.ipv4.ip_forward=1' > /etc/sysctl.d/99-wireguard.conf
sysctl -p /etc/sysctl.d/99-wireguard.conf

# Step 4: Configure Firewall
echo -e "${BLUE}Step 4: Configuring Firewall${NC}"
echo "================================="

# Allow WireGuard traffic
ufw allow $WG_PORT/udp

# Allow traffic from VPN subnet
ufw allow from ${WG_SUBNET}

# Enable UFW if not already enabled
ufw --force enable

# Step 5: Start WireGuard Service
echo -e "${BLUE}Step 5: Starting WireGuard Service${NC}"
echo "======================================"

# Enable and start WireGuard
systemctl enable wg-quick@wg0
systemctl start wg-quick@wg0

# Check status
systemctl status wg-quick@wg0

echo -e "${GREEN}✅ WireGuard server setup completed!${NC}"
echo ""
echo -e "${BLUE}Server Information:${NC}"
echo "Public IP: $SERVER_IP"
echo "WireGuard Port: $WG_PORT"
echo "VPN Subnet: $WG_SUBNET"
echo "Server Public Key: $(cat server_public.key)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Run: ./create-wireguard-client.sh to create client configurations"
echo "2. Distribute client configs to your devices"
echo "3. Test connectivity"
echo ""
echo -e "${BLUE}WireGuard is now ready for client connections!${NC}" 