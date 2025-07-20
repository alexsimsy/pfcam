#!/bin/bash

# OpenVPN Initialization Script for SIMSY Network
# This script sets up OpenVPN server with certificates and configuration

set -e

echo "Initializing OpenVPN server for SIMSY network..."

# Create necessary directories
mkdir -p /etc/openvpn/easy-rsa
mkdir -p /etc/openvpn/ccd
mkdir -p /var/log/openvpn

# Copy easy-rsa files
cp -r /usr/share/easy-rsa/* /etc/openvpn/easy-rsa/

# Navigate to easy-rsa directory
cd /etc/openvpn/easy-rsa

# Initialize PKI
echo "Initializing PKI..."
./easyrsa init-pki

# Build CA (non-interactive)
echo "Building Certificate Authority..."
echo "SIMSY" | ./easyrsa build-ca nopass

# Build server certificate
echo "Building server certificate..."
echo "yes" | ./easyrsa build-server-full server nopass

# Build Diffie-Hellman parameters
echo "Generating Diffie-Hellman parameters..."
./easyrsa gen-dh

# Generate HMAC key for additional security
echo "Generating HMAC key..."
openvpn --genkey secret ta.key

# Move certificates to OpenVPN directory
cp pki/ca.crt /etc/openvpn/
cp pki/issued/server.crt /etc/openvpn/
cp pki/private/server.key /etc/openvpn/
cp pki/dh.pem /etc/openvpn/
cp ta.key /etc/openvpn/

# Create server configuration
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
echo 'net.ipv4.ip_forward=1' > /etc/sysctl.d/99-openvpn.conf
sysctl -p /etc/sysctl.d/99-openvpn.conf

# Set proper permissions
chown -R nobody:nogroup /etc/openvpn
chmod 600 /etc/openvpn/*.key
chmod 644 /etc/openvpn/*.crt
chmod 644 /etc/openvpn/*.pem

echo "OpenVPN server initialization complete!"
echo "Server IP: 10.8.0.1"
echo "Subnet: 10.8.0.0/24"
echo "Port: 1194 (UDP)"

# Create a sample client configuration template
cat > /etc/openvpn/client-template.ovpn << EOF
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
# Paste CA certificate here
</ca>
<cert>
# Paste client certificate here
</cert>
<key>
# Paste client key here
</key>
<tls-auth>
# Paste TLS auth key here
</tls-auth>
EOF

echo "Client template created at /etc/openvpn/client-template.ovpn"
echo "Remember to replace YOUR_SERVER_IP with your actual server IP address" 