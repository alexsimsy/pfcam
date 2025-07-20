#!/bin/bash

# Quick Start Script for SIMSY Network VPN Setup
# This script automates the entire VPN server setup process

set -e

echo "=========================================="
echo "SIMSY Network VPN Server Quick Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root (use sudo)"
    exit 1
fi

# Get server IP
echo "Enter your server's public IP address:"
read SERVER_IP

if [ -z "$SERVER_IP" ]; then
    echo "Error: Server IP is required"
    exit 1
fi

echo ""
echo "Setting up OpenVPN server for SIMSY network..."
echo "Server IP: $SERVER_IP"
echo ""

# Update system
echo "1. Updating system packages..."
apt update && apt upgrade -y

# Install required packages
echo "2. Installing OpenVPN and dependencies..."
apt install -y openvpn easy-rsa ufw

# Create VPN directories
echo "3. Creating VPN directories..."
mkdir -p /etc/openvpn/easy-rsa
mkdir -p /etc/openvpn/ccd
mkdir -p /etc/openvpn/clients
mkdir -p /var/log/openvpn

# Copy easy-rsa files
cp -r /usr/share/easy-rsa/* /etc/openvpn/easy-rsa/

# Navigate to easy-rsa directory
cd /etc/openvpn/easy-rsa

# Initialize PKI
echo "4. Initializing PKI..."
./easyrsa init-pki

# Build CA
echo "5. Building Certificate Authority..."
echo "SIMSY" | ./easyrsa build-ca nopass

# Build server certificate
echo "6. Building server certificate..."
echo "yes" | ./easyrsa build-server-full server nopass

# Build Diffie-Hellman parameters
echo "7. Generating Diffie-Hellman parameters..."
./easyrsa gen-dh

# Generate HMAC key
echo "8. Generating HMAC key..."
openvpn --genkey secret ta.key

# Move certificates to OpenVPN directory
cp pki/ca.crt /etc/openvpn/
cp pki/issued/server.crt /etc/openvpn/
cp pki/private/server.key /etc/openvpn/
cp pki/dh.pem /etc/openvpn/
cp ta.key /etc/openvpn/

# Create server configuration
echo "9. Creating server configuration..."
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
echo "10. Enabling IP forwarding..."
echo 'net.ipv4.ip_forward=1' > /etc/sysctl.d/99-openvpn.conf
sysctl -p /etc/sysctl.d/99-openvpn.conf

# Configure firewall
echo "11. Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 1194/udp
ufw allow from 10.8.0.0/24 to any port 8000  # Backend API
ufw allow from 10.8.0.0/24 to any port 3000  # Frontend
ufw allow from 10.8.0.0/24 to any port 8554  # RTSP
ufw allow from 10.8.0.0/24 to any port 8888  # HLS
ufw --force enable

# Set proper permissions
chown -R nobody:nogroup /etc/openvpn
chmod 600 /etc/openvpn/*.key
chmod 644 /etc/openvpn/*.crt
chmod 644 /etc/openvpn/*.pem

# Start and enable OpenVPN service
echo "12. Starting OpenVPN service..."
systemctl start openvpn@openvpn
systemctl enable openvpn@openvpn

# Create a sample client
echo "13. Creating sample client configuration..."
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

# Create management script
echo "14. Creating management scripts..."
cat > /usr/local/bin/create-vpn-client << 'EOF'
#!/bin/bash
if [ $# -eq 0 ]; then
    echo "Usage: $0 <client_name>"
    echo "Example: $0 camera002"
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
echo "Remember to replace YOUR_SERVER_IP with $SERVER_IP"
EOF

chmod +x /usr/local/bin/create-vpn-client

# Create status script
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

echo ""
echo "=========================================="
echo "VPN Server Setup Complete!"
echo "=========================================="
echo ""
echo "Server Configuration:"
echo "- Server IP: $SERVER_IP"
echo "- VPN Subnet: 10.8.0.0/24"
echo "- Port: 1194 (UDP)"
echo "- Server Interface: 10.8.0.1"
echo ""
echo "Sample client configuration:"
echo "- File: /etc/openvpn/clients/camera001.ovpn"
echo "- Copy this file to your camera/router"
echo ""
echo "Management Commands:"
echo "- Create new client: create-vpn-client <name>"
echo "- Check status: vpn-status"
echo "- View logs: journalctl -u openvpn@openvpn -f"
echo ""
echo "Next Steps:"
echo "1. Copy camera001.ovpn to your camera/router"
echo "2. Import the configuration into OpenVPN client"
echo "3. Connect to the VPN server"
echo "4. Configure camera to use VPN IP for server communication"
echo "5. Test connectivity between camera and server"
echo ""
echo "For SIMSY network integration:"
echo "- Configure SIMSY to route traffic to $SERVER_IP:1194"
echo "- Set up dedicated IP subnet for VPN clients"
echo "- Configure QoS for camera traffic"
echo ""
echo "Security Notes:"
echo "- Firewall configured to allow only necessary traffic"
echo "- Certificates generated with strong encryption"
echo "- VPN traffic encrypted with AES-256-CBC"
echo "- HMAC authentication enabled"
echo ""
echo "Support: Contact SIMSY network administrator for assistance" 