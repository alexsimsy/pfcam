#!/bin/bash

# Complete Server Installation Script for SIMSY Network PFCAM Deployment
# This script installs everything needed for the VPN server and PFCAM application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}SIMSY Network PFCAM Server Installation${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run this script as root (use sudo)${NC}"
    exit 1
fi

# Get server configuration
echo -e "${YELLOW}Server Configuration${NC}"
echo "=========================="

echo -e "${BLUE}Enter your server's public IP address:${NC}"
read SERVER_IP

if [ -z "$SERVER_IP" ]; then
    echo -e "${RED}Error: Server IP is required${NC}"
    exit 1
fi

echo -e "${BLUE}Enter your domain name (or press Enter to use IP only):${NC}"
read DOMAIN_NAME

echo -e "${BLUE}Enter a secure password for PostgreSQL:${NC}"
read -s POSTGRES_PASSWORD

if [ -z "$POSTGRES_PASSWORD" ]; then
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    echo -e "${YELLOW}Generated PostgreSQL password: $POSTGRES_PASSWORD${NC}"
fi

echo -e "${BLUE}Enter a secure secret key for the application:${NC}"
read -s SECRET_KEY

if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(openssl rand -base64 64)
    echo -e "${YELLOW}Generated secret key${NC}"
fi

echo -e "${BLUE}Enter FTP password:${NC}"
read -s FTP_PASSWORD

if [ -z "$FTP_PASSWORD" ]; then
    FTP_PASSWORD=$(openssl rand -base64 16)
    echo -e "${YELLOW}Generated FTP password: $FTP_PASSWORD${NC}"
fi

echo ""
echo -e "${GREEN}Configuration Summary:${NC}"
echo "Server IP: $SERVER_IP"
echo "Domain: ${DOMAIN_NAME:-$SERVER_IP}"
echo "PostgreSQL Password: [HIDDEN]"
echo "Secret Key: [HIDDEN]"
echo "FTP Password: [HIDDEN]"
echo ""

echo -e "${YELLOW}Press Enter to continue with installation...${NC}"
read

# Step 1: System Update and Basic Setup
echo -e "${BLUE}Step 1: System Update and Basic Setup${NC}"
echo "=========================================="

echo -e "${YELLOW}Updating system packages...${NC}"
apt update && apt upgrade -y

echo -e "${YELLOW}Installing essential packages...${NC}"
apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release ufw fail2ban htop

# Step 2: Install Docker
echo -e "${BLUE}Step 2: Docker Installation${NC}"
echo "=============================="

echo -e "${YELLOW}Installing Docker...${NC}"

# Remove old versions
apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Add current user to docker group
usermod -aG docker $SUDO_USER

echo -e "${GREEN}✓ Docker installed successfully${NC}"

# Step 3: Install OpenVPN
echo -e "${BLUE}Step 3: OpenVPN Installation${NC}"
echo "================================"

echo -e "${YELLOW}Installing OpenVPN...${NC}"
apt install -y openvpn easy-rsa

# Create VPN directories
mkdir -p /etc/openvpn/easy-rsa
mkdir -p /etc/openvpn/ccd
mkdir -p /etc/openvpn/clients
mkdir -p /var/log/openvpn

# Copy easy-rsa files
cp -r /usr/share/easy-rsa/* /etc/openvpn/easy-rsa/

# Navigate to easy-rsa directory
cd /etc/openvpn/easy-rsa

# Initialize PKI
echo -e "${YELLOW}Initializing PKI...${NC}"
./easyrsa init-pki

# Build CA
echo -e "${YELLOW}Building Certificate Authority...${NC}"
echo "SIMSY" | ./easyrsa build-ca nopass

# Build server certificate
echo -e "${YELLOW}Building server certificate...${NC}"
echo "yes" | ./easyrsa build-server-full server nopass

# Build Diffie-Hellman parameters
echo -e "${YELLOW}Generating Diffie-Hellman parameters...${NC}"
./easyrsa gen-dh

# Generate HMAC key
echo -e "${YELLOW}Generating HMAC key...${NC}"
openvpn --genkey secret ta.key

# Move certificates to OpenVPN directory
cp pki/ca.crt /etc/openvpn/
cp pki/issued/server.crt /etc/openvpn/
cp pki/private/server.key /etc/openvpn/
cp pki/dh.pem /etc/openvpn/
cp ta.key /etc/openvpn/

# Create server configuration
echo -e "${YELLOW}Creating server configuration...${NC}"
cat > /etc/openvpn/openvpn.conf << EOF
port 1194
proto udp
dev tun
ca ca.crt
cert server.crt
key server.key
dh dh.pem
auth SHA256
server 10.8.0.0 255.255.255.0
ifconfig-pool-persist ipp.txt
push "redirect-gateway def1 bypass-dhcp"
push "dhcp-option DNS 8.8.8.8"
push "dhcp-option DNS 8.8.4.4"
keepalive 10 120
tls-auth ta.key 0
cipher AES-256-CBC
user nobody
group nogroup
persist-key
persist-tun
status /var/log/openvpn/openvpn-status.log
log /var/log/openvpn/openvpn.log
verb 3
explicit-exit-notify 1
client-config-dir ccd
route 10.8.0.0 255.255.255.0
EOF

# Enable IP forwarding
echo -e "${YELLOW}Enabling IP forwarding...${NC}"
echo 'net.ipv4.ip_forward=1' > /etc/sysctl.d/99-openvpn.conf
sysctl -p /etc/sysctl.d/99-openvpn.conf

# Set proper permissions
chown -R nobody:nogroup /etc/openvpn
chmod 600 /etc/openvpn/*.key
chmod 644 /etc/openvpn/*.crt
chmod 644 /etc/openvpn/*.pem

# Start and enable OpenVPN service
systemctl start openvpn@openvpn
systemctl enable openvpn@openvpn

echo -e "${GREEN}✓ OpenVPN installed and configured${NC}"

# Step 4: Configure Firewall
echo -e "${BLUE}Step 4: Firewall Configuration${NC}"
echo "================================="

echo -e "${YELLOW}Configuring UFW firewall...${NC}"

# Reset UFW
ufw --force reset

# Set defaults
ufw default deny incoming
ufw default allow outgoing

# Allow SSH
ufw allow ssh

# Allow VPN traffic
ufw allow 1194/udp

# Allow application ports
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
ufw allow 3000/tcp
ufw allow 8554/tcp
ufw allow 8888/tcp
ufw allow 21/tcp
ufw allow 30000:30009/tcp

# Allow traffic from VPN subnet to application
ufw allow from 10.8.0.0/24 to any port 8000
ufw allow from 10.8.0.0/24 to any port 3000
ufw allow from 10.8.0.0/24 to any port 8554
ufw allow from 10.8.0.0/24 to any port 8888

# Enable UFW
ufw --force enable

echo -e "${GREEN}✓ Firewall configured${NC}"

# Step 5: Create Application Directory
echo -e "${BLUE}Step 5: Application Setup${NC}"
echo "============================="

# Create application directory
mkdir -p /opt/pfcam
cd /opt/pfcam

# Create environment file
echo -e "${YELLOW}Creating environment configuration...${NC}"
cat > .env << EOF
# SIMSY Network Production Environment Configuration
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
SECRET_KEY=$SECRET_KEY
FTP_PUBLIC_HOST=$SERVER_IP
FTP_USER_NAME=ftpuser
FTP_USER_PASS=$FTP_PASSWORD
VITE_API_BASE_URL=http://$SERVER_IP:8000
VITE_WS_URL=ws://$SERVER_IP:8000/ws
VPN_SERVER_IP=$SERVER_IP
VPN_SUBNET=10.8.0.0/24
VPN_PORT=1194
SIMSY_APN=simsy.network
SIMSY_SUBNET=192.168.100.0/24
LOG_LEVEL=INFO
MONITORING_ENABLED=true
EOF

# Create necessary directories
mkdir -p vpn-config vpn-data vpn-logs vpn-monitor network-logs ftpdata

echo -e "${GREEN}✓ Application directory created${NC}"

# Step 6: Create Management Scripts
echo -e "${BLUE}Step 6: Management Scripts${NC}"
echo "=============================="

# Create VPN client script
cat > /usr/local/bin/create-vpn-client << 'EOF'
#!/bin/bash
if [ $# -eq 0 ]; then
    echo "Usage: $0 <client_name>"
    echo "Example: $0 camera001"
    exit 1
fi

CLIENT_NAME=$1
cd /etc/openvpn/easy-rsa
echo "yes" | ./easyrsa build-client-full $CLIENT_NAME nopass

cat > /etc/openvpn/clients/$CLIENT_NAME.ovpn << CLIENTCONF
client
dev tun
proto udp
remote YOUR_SERVER_IP 1194
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
auth SHA256
cipher AES-256-CBC
verb 3
<ca>
$(cat pki/ca.crt)
</ca>
<cert>
$(cat pki/issued/$CLIENT_NAME.crt)
</cert>
<key>
$(cat pki/private/$CLIENT_NAME.key)
</key>
<tls-auth>
$(cat /etc/openvpn/ta.key)
</tls-auth>
CLIENTCONF

chmod 600 /etc/openvpn/clients/$CLIENT_NAME.ovpn
echo "Client configuration created: /etc/openvpn/clients/$CLIENT_NAME.ovpn"
echo "Remember to replace YOUR_SERVER_IP with the actual server IP"
EOF

chmod +x /usr/local/bin/create-vpn-client

# Create VPN status script
cat > /usr/local/bin/vpn-status << 'EOF'
#!/bin/bash
echo "OpenVPN Server Status"
echo "===================="
echo ""
echo "Service Status:"
systemctl status openvpn@openvpn --no-pager -l
echo ""
echo "Connected Clients:"
if [ -f /var/log/openvpn/openvpn-status.log ]; then
    cat /var/log/openvpn/openvpn-status.log
else
    echo "No status log found"
fi
echo ""
echo "VPN Interface:"
ip addr show tun0 2>/dev/null || echo "VPN interface not active"
echo ""
echo "Routing Table:"
ip route show | grep 10.8.0.0 || echo "No VPN routes found"
EOF

chmod +x /usr/local/bin/vpn-status

# Create backup script
cat > /usr/local/bin/backup-pfcam << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/pfcam-$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup VPN configuration
tar -czf $BACKUP_DIR/vpn-config.tar.gz /etc/openvpn

# Backup certificates
cp -r /etc/openvpn/easy-rsa/pki $BACKUP_DIR/

# Backup application data (if exists)
if [ -d "/opt/pfcam" ]; then
    tar -czf $BACKUP_DIR/app-data.tar.gz /opt/pfcam
fi

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x /usr/local/bin/backup-pfcam

echo -e "${GREEN}✓ Management scripts created${NC}"

# Step 7: Create Sample Client
echo -e "${BLUE}Step 7: Create Sample Client${NC}"
echo "================================"

echo -e "${YELLOW}Creating sample client configuration...${NC}"
cd /etc/openvpn/easy-rsa
echo "yes" | ./easyrsa build-client-full camera001 nopass

# Create client configuration
cat > /etc/openvpn/clients/camera001.ovpn << EOF
client
dev tun
proto udp
remote $SERVER_IP 1194
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
auth SHA256
cipher AES-256-CBC
verb 3
<ca>
$(cat pki/ca.crt)
</ca>
<cert>
$(cat pki/issued/camera001.crt)
</cert>
<key>
$(cat pki/private/camera001.key)
</key>
<tls-auth>
$(cat /etc/openvpn/ta.key)
</tls-auth>
EOF

chmod 600 /etc/openvpn/clients/camera001.ovpn

echo -e "${GREEN}✓ Sample client created${NC}"

# Step 8: Final Configuration
echo -e "${BLUE}Step 8: Final Configuration${NC}"
echo "================================"

# Create network information file
cat > /opt/pfcam/network-info.txt << EOF
SIMSY Network Configuration
==========================

Server Information:
- Public IP: $SERVER_IP
- VPN Server: $SERVER_IP:1194 (UDP)
- VPN Subnet: 10.8.0.0/24
- VPN Server Interface: 10.8.0.1

Application Ports:
- Backend API: $SERVER_IP:8000
- Frontend: $SERVER_IP:3000
- RTSP Streaming: $SERVER_IP:8554
- HLS Streaming: $SERVER_IP:8888
- FTP: $SERVER_IP:21

VPN Client Configuration:
- Sample client: /etc/openvpn/clients/camera001.ovpn
- Copy this file to your camera/router
- Import into OpenVPN client
- Connect to VPN server

SIMSY Network Setup:
1. Configure SIM card APN to: simsy.network
2. Set up routing in SIMSY network to: $SERVER_IP
3. Allocate dedicated IP subnet for VPN clients
4. Configure QoS for camera traffic

Management Commands:
- Create new client: create-vpn-client <name>
- Check VPN status: vpn-status
- Backup system: backup-pfcam
- View logs: journalctl -u openvpn@openvpn -f

Security Notes:
- Firewall configured to allow only necessary traffic
- VPN traffic encrypted with AES-256-CBC
- Certificate-based authentication enabled
- HMAC authentication enabled

Support Information:
- Contact SIMSY network administrator for network configuration
- Check logs in /var/log/openvpn/ for VPN issues
- Application logs available via Docker Compose
EOF

echo -e "${GREEN}✓ Network information saved to /opt/pfcam/network-info.txt${NC}"

# Step 9: Installation Complete
echo -e "${BLUE}Step 9: Installation Complete${NC}"
echo "================================="

echo -e "${GREEN}🎉 Server installation completed successfully!${NC}"
echo ""
echo -e "${YELLOW}Server Configuration Summary:${NC}"
echo "================================"
echo "Server IP: $SERVER_IP"
echo "VPN Subnet: 10.8.0.0/24"
echo "VPN Port: 1194 (UDP)"
echo "VPN Server Interface: 10.8.0.1"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "============="
echo "1. Copy application files to /opt/pfcam/"
echo "2. Deploy PFCAM application:"
echo "   cd /opt/pfcam"
echo "   docker-compose -f docker-compose.production.yml up -d"
echo ""
echo "3. Configure SIMSY network:"
echo "   - Route traffic to $SERVER_IP:1194"
echo "   - Allocate IP subnet for VPN clients"
echo "   - Configure QoS for camera traffic"
echo ""
echo "4. Configure cameras:"
echo "   - Copy /etc/openvpn/clients/camera001.ovpn to camera/router"
echo "   - Import into OpenVPN client"
echo "   - Connect to VPN server"
echo "   - Configure camera to use 10.8.0.1 as server"
echo ""
echo -e "${YELLOW}Management Commands:${NC}"
echo "======================="
echo "- Create VPN client: create-vpn-client <name>"
echo "- Check VPN status: vpn-status"
echo "- Backup system: backup-pfcam"
echo "- View VPN logs: journalctl -u openvpn@openvpn -f"
echo ""
echo -e "${YELLOW}Network Information:${NC}"
echo "========================="
echo "Detailed network configuration saved to: /opt/pfcam/network-info.txt"
echo ""
echo -e "${GREEN}✅ Installation completed! Ready for SIMSY network integration.${NC}" 