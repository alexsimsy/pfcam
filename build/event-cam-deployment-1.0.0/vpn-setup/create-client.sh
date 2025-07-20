#!/bin/bash

# OpenVPN Client Certificate Generator for SIMSY Network
# This script creates client certificates and configuration files

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <client_name> [server_ip]"
    echo "Example: $0 camera001 192.168.1.100"
    exit 1
fi

CLIENT_NAME=$1
SERVER_IP=${2:-"YOUR_SERVER_IP"}

echo "Creating OpenVPN client configuration for: $CLIENT_NAME"

# Navigate to easy-rsa directory
cd /etc/openvpn/easy-rsa

# Build client certificate
echo "Building client certificate for $CLIENT_NAME..."
echo "yes" | ./easyrsa build-client-full $CLIENT_NAME nopass

# Create client configuration directory
mkdir -p /etc/openvpn/clients

# Create client configuration file
cat > /etc/openvpn/clients/$CLIENT_NAME.ovpn << EOF
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
$(cat pki/issued/$CLIENT_NAME.crt)
</cert>
<key>
$(cat pki/private/$CLIENT_NAME.key)
</key>
<tls-auth>
$(cat /etc/openvpn/ta.key)
</tls-auth>
EOF

# Set proper permissions
chmod 600 /etc/openvpn/clients/$CLIENT_NAME.ovpn

echo "Client configuration created: /etc/openvpn/clients/$CLIENT_NAME.ovpn"
echo "Copy this file to your camera/router and import it into the OpenVPN client"
echo ""
echo "For cameras with OpenVPN client support:"
echo "1. Copy $CLIENT_NAME.ovpn to the camera"
echo "2. Import the configuration file"
echo "3. Connect to the VPN server"
echo "4. Configure camera to use VPN IP for server communication"
echo ""
echo "For routers with OpenVPN support:"
echo "1. Upload $CLIENT_NAME.ovpn to router"
echo "2. Configure OpenVPN client with this file"
echo "3. Set up routing for camera traffic through VPN"

# Create a summary file
cat > /etc/openvpn/clients/$CLIENT_NAME-summary.txt << EOF
Client Configuration Summary
============================
Client Name: $CLIENT_NAME
Server IP: $SERVER_IP
Server Port: 1194
Protocol: UDP
VPN Subnet: 10.8.0.0/24
Configuration File: $CLIENT_NAME.ovpn

Instructions:
1. Copy $CLIENT_NAME.ovpn to your device
2. Import into OpenVPN client
3. Connect to VPN server
4. Camera will receive IP from 10.8.0.0/24 range
5. Configure camera to communicate with server via VPN

Troubleshooting:
- Check firewall allows UDP port 1194
- Verify server IP is correct
- Ensure certificates are valid
- Check OpenVPN client logs for errors
EOF

echo "Summary file created: /etc/openvpn/clients/$CLIENT_NAME-summary.txt" 