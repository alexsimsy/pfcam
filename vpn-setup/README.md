# SIMSY Network VPN Server Setup

## Overview
This setup provides a VPN server for SIMSY's mobile network deployment, enabling secure communication between cameras and the application server through SIMSY's direct network routes.

## Architecture
```
Camera → Router with SIM → SIMSY Network → VPN → Ubuntu Server
```

## Prerequisites
- Ubuntu 20.04+ server
- Root or sudo access
- Public IP address (or port forwarding configured)
- SIMSY network connection established

## Installation Steps

### 1. Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install OpenVPN and Easy-RSA
```bash
sudo apt install openvpn easy-rsa -y
```

### 3. Set up Certificate Authority
```bash
# Create directory for certificates
sudo mkdir -p /etc/openvpn/easy-rsa
sudo cp -r /usr/share/easy-rsa/* /etc/openvpn/easy-rsa/

# Navigate to easy-rsa directory
cd /etc/openvpn/easy-rsa

# Initialize PKI
./easyrsa init-pki

# Build CA
./easyrsa build-ca nopass

# Build server certificate
./easyrsa build-server-full server nopass

# Build Diffie-Hellman parameters
./easyrsa gen-dh

# Generate HMAC key for additional security
openvpn --genkey secret ta.key
```

### 4. Configure OpenVPN Server
Create the server configuration file:

```bash
sudo nano /etc/openvpn/server.conf
```

Add the following configuration:

```conf
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
status openvpn-status.log
verb 3
explicit-exit-notify 1
```

### 5. Enable IP Forwarding
```bash
# Enable IP forwarding
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 6. Configure Firewall
```bash
# Allow OpenVPN traffic
sudo ufw allow 1194/udp

# Allow traffic from VPN subnet
sudo ufw allow from 10.8.0.0/24

# Enable UFW
sudo ufw enable
```

### 7. Start OpenVPN Service
```bash
# Start and enable OpenVPN
sudo systemctl start openvpn@server
sudo systemctl enable openvpn@server

# Check status
sudo systemctl status openvpn@server
```

## Client Configuration

### Generate Client Certificate
```bash
cd /etc/openvpn/easy-rsa
./easyrsa build-client-full client1 nopass
```

### Create Client Configuration
Create a client configuration file:

```bash
sudo nano /etc/openvpn/client1.ovpn
```

Add the following content (replace with your server's public IP):

```conf
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
```

## Integration with PFCAM Application

### 1. Update Docker Compose
Add VPN configuration to your docker-compose.yml:

```yaml
version: '3.8'

services:
  # ... existing services ...
  
  openvpn:
    image: kylemanna/openvpn:latest
    container_name: pfcam-openvpn
    ports:
      - "1194:1194/udp"
    volumes:
      - ./vpn-config:/etc/openvpn
      - ./vpn-data:/var/lib/openvpn
    cap_add:
      - NET_ADMIN
    restart: unless-stopped
    networks:
      - pfcam-network

networks:
  pfcam-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### 2. Network Configuration
Configure your application to use the VPN subnet:

```bash
# Add route for VPN clients to reach application
sudo ip route add 10.8.0.0/24 via 10.8.0.1 dev tun0
```

### 3. Camera Configuration
Configure cameras to connect to the VPN server:

1. Install OpenVPN client on camera/router
2. Upload client configuration file
3. Connect to VPN server
4. Configure camera to use VPN IP for server communication

## Security Considerations

### 1. Certificate Management
- Store certificates securely
- Rotate certificates regularly
- Use strong passphrases for production

### 2. Network Security
- Restrict VPN access to necessary IPs only
- Monitor VPN connections
- Use strong authentication

### 3. Firewall Rules
```bash
# Allow only necessary traffic
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 1194/udp
sudo ufw allow from 10.8.0.0/24 to any port 8000  # Backend API
sudo ufw allow from 10.8.0.0/24 to any port 3000  # Frontend
```

## Monitoring and Logs

### Check VPN Status
```bash
# View connected clients
sudo cat /var/log/openvpn/openvpn-status.log

# View logs
sudo journalctl -u openvpn@server -f
```

### Network Monitoring
```bash
# Check VPN interface
ip addr show tun0

# Check routing
ip route show

# Monitor traffic
sudo tcpdump -i tun0
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check firewall settings
   - Verify port 1194 is open
   - Check OpenVPN service status

2. **Certificate Errors**
   - Verify certificate paths
   - Check certificate validity
   - Regenerate certificates if needed

3. **Routing Issues**
   - Verify IP forwarding is enabled
   - Check routing table
   - Ensure proper subnet configuration

### Debug Commands
```bash
# Test OpenVPN configuration
sudo openvpn --config /etc/openvpn/server.conf --test-crypto

# Check service status
sudo systemctl status openvpn@server

# View detailed logs
sudo tail -f /var/log/openvpn/openvpn.log
```

## Production Deployment

### 1. SSL/TLS Configuration
For production, consider using SSL/TLS certificates:

```bash
# Install certbot
sudo apt install certbot

# Generate SSL certificate
sudo certbot certonly --standalone -d your-domain.com
```

### 2. High Availability
Consider setting up multiple VPN servers for redundancy:

- Load balancer for VPN connections
- Multiple VPN endpoints
- Automatic failover

### 3. Backup Strategy
```bash
# Backup VPN configuration
sudo tar -czf vpn-backup-$(date +%Y%m%d).tar.gz /etc/openvpn/

# Backup certificates
sudo cp -r /etc/openvpn/easy-rsa/pki /backup/vpn-certificates/
```

## SIMSY Network Integration

### 1. Network Configuration
Configure SIMSY to route traffic to your VPN server:

- Allocate dedicated IP subnet for VPN clients
- Configure routing tables
- Set up QoS for camera traffic

### 2. Camera Setup
Configure cameras to use SIMSY network:

- Set APN to SIMSY network
- Configure static IP if required
- Test connectivity through VPN

### 3. Performance Optimization
- Monitor bandwidth usage
- Optimize video streaming settings
- Configure QoS for critical traffic

## Support and Maintenance

### Regular Maintenance Tasks
1. Update OpenVPN packages monthly
2. Rotate certificates quarterly
3. Review logs for security issues
4. Monitor bandwidth usage
5. Test failover procedures

### Emergency Procedures
1. VPN server down: Check service status and logs
2. Certificate expired: Regenerate and distribute new certificates
3. Network issues: Verify SIMSY network connectivity
4. Security breach: Review logs and rotate credentials

## Contact Information
For SIMSY network support and VPN configuration assistance, contact your SIMSY network administrator. 

---

## ZeroTier Integration (Experimental)

ZeroTier provides a simple, flexible, and cross-platform virtual network for secure connectivity. This setup allows the PFCAM server to join a ZeroTier network using Docker.

### Prerequisites
- A ZeroTier account (https://my.zerotier.com/)
- A ZeroTier network created in your account
- The network ID (find this in the ZeroTier web UI)

### Running ZeroTier in Docker

1. Edit `docker-compose.zerotier.yml` and set your network ID:
   ```yaml
   environment:
     - ZEROTIER_NETWORK_ID=your_network_id_here
   ```

2. Start the ZeroTier container:
   ```bash
   docker compose -f docker-compose.zerotier.yml up -d
   ```

3. Authorize the server in the ZeroTier web UI (if your network is private).

4. (Optional) Check the container logs for status:
   ```bash
   docker logs zerotier
   ```

5. To join additional networks, use the ZeroTier CLI inside the container:
   ```bash
   docker exec -it zerotier zerotier-cli join <network_id>
   ```

### Notes
- The container uses `network_mode: host` and requires `NET_ADMIN` and `SYS_ADMIN` capabilities, as well as access to `/dev/net/tun`.
- Data is persisted in the `zerotier-one-data` Docker volume.
- You can manage network membership and see connected devices in the ZeroTier web UI.

### Troubleshooting
- If the container does not join the network, check the logs and ensure the network ID is correct.
- Make sure the server is authorized in the ZeroTier web UI.
- For more details, see the [ZeroTier Docker documentation](https://docs.zerotier.com/docker/). 