# SIMSY Network Production Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the PFCAM application with OpenVPN server for SIMSY's mobile network infrastructure.

## Architecture
```
Camera → Router with SIM → SIMSY Network → VPN → Ubuntu Server → PFCAM Application
```

## Prerequisites

### Server Requirements
- Ubuntu 20.04+ server
- Minimum 4GB RAM
- 50GB+ storage
- Public IP address
- Root or sudo access

### Network Requirements
- SIMSY network connection established
- Dedicated IP subnet allocated by SIMSY
- Port 1194 (UDP) accessible from internet
- Ports 80, 443, 8000, 3000, 8554, 8888 accessible

## Step 1: Server Preparation

### 1.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git docker.io docker-compose ufw
```

### 1.2 Configure Firewall
```bash
# Allow SSH
sudo ufw allow ssh

# Allow VPN traffic
sudo ufw allow 1194/udp

# Allow application ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 8554/tcp
sudo ufw allow 8888/tcp

# Enable firewall
sudo ufw enable
```

### 1.3 Install Docker
```bash
# Add Docker repository
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Add user to docker group
sudo usermod -aG docker $USER
```

## Step 2: Application Deployment

### 2.1 Clone Application
```bash
git clone <your-repository-url> pfcam
cd pfcam
```

### 2.2 Configure Environment
```bash
# Copy production environment file
cp vpn-setup/env.production .env

# Edit environment variables
nano .env
```

**Required Environment Variables:**
- `POSTGRES_PASSWORD`: Secure database password
- `SECRET_KEY`: Long, random secret key
- `FTP_PUBLIC_HOST`: Your server's public IP
- `FTP_USER_PASS`: Secure FTP password
- `VITE_API_BASE_URL`: Your domain or IP
- `VPN_SERVER_IP`: Your server's public IP

### 2.3 Deploy Application
```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Check service status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

## Step 3: VPN Server Setup

### 3.1 Initialize VPN Server
```bash
# Make scripts executable
chmod +x vpn-setup/init-vpn.sh
chmod +x vpn-setup/create-client.sh
chmod +x vpn-setup/quick-start.sh

# Run quick setup (if not using Docker)
sudo ./vpn-setup/quick-start.sh
```

### 3.2 Create Client Certificates
```bash
# Create client for camera/router
sudo ./vpn-setup/create-client.sh camera001 YOUR_SERVER_IP

# Create additional clients as needed
sudo ./vpn-setup/create-client.sh camera002 YOUR_SERVER_IP
sudo ./vpn-setup/create-client.sh router001 YOUR_SERVER_IP
```

### 3.3 Test VPN Connection
```bash
# Check VPN status
sudo vpn-status

# View connected clients
sudo cat /var/log/openvpn/openvpn-status.log
```

## Step 4: Camera Configuration

### 4.1 Router Setup (if using router with SIM)
1. **Install OpenVPN client** on router
2. **Upload client configuration** (`camera001.ovpn`)
3. **Configure OpenVPN client**:
   - Import configuration file
   - Set to auto-start
   - Configure routing for camera traffic

### 4.2 Camera Setup
1. **Configure camera network settings**:
   - Set static IP in VPN subnet (e.g., 10.8.0.10)
   - Set gateway to VPN server (10.8.0.1)
   - Configure DNS (8.8.8.8, 8.8.4.4)

2. **Configure camera server settings**:
   - Set server IP to VPN server (10.8.0.1)
   - Configure API endpoints
   - Set up video streaming

### 4.3 SIMSY Network Configuration
1. **Configure SIM card APN** to SIMSY network
2. **Set up routing** in SIMSY network
3. **Allocate dedicated IP subnet** for VPN clients
4. **Configure QoS** for camera traffic

## Step 5: Testing and Validation

### 5.1 Test VPN Connectivity
```bash
# From camera/router, test VPN connection
ping 10.8.0.1

# Test application connectivity
curl http://10.8.0.1:8000/health
```

### 5.2 Test Application Features
1. **Camera registration** via web interface
2. **Video streaming** through VPN
3. **Event recording** and storage
4. **FTP file transfer** functionality

### 5.3 Monitor Performance
```bash
# Check VPN performance
sudo vpn-status

# Monitor network traffic
sudo tcpdump -i tun0

# Check application logs
docker-compose -f docker-compose.production.yml logs -f backend
```

## Step 6: Production Hardening

### 6.1 SSL/TLS Configuration
```bash
# Install certbot
sudo apt install certbot

# Generate SSL certificate
sudo certbot certonly --standalone -d your-domain.com

# Configure nginx with SSL
sudo nano nginx/production.conf
```

### 6.2 Security Enhancements
```bash
# Update firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 1194/udp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow from 10.8.0.0/24 to any port 8000
sudo ufw allow from 10.8.0.0/24 to any port 3000

# Enable UFW
sudo ufw enable
```

### 6.3 Backup Configuration
```bash
# Create backup script
cat > /usr/local/bin/backup-pfcam << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/pfcam-$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup application data
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U pfcam pfcam > $BACKUP_DIR/database.sql
tar -czf $BACKUP_DIR/app-data.tar.gz ./backend/storage ./ftpdata

# Backup VPN configuration
tar -czf $BACKUP_DIR/vpn-config.tar.gz /etc/openvpn

# Backup certificates
cp -r /etc/openvpn/easy-rsa/pki $BACKUP_DIR/

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x /usr/local/bin/backup-pfcam
```

## Step 7: Monitoring and Maintenance

### 7.1 Set Up Monitoring
```bash
# Create monitoring script
cat > /usr/local/bin/monitor-pfcam << 'EOF'
#!/bin/bash
echo "=== PFCAM System Status ==="
echo "Date: $(date)"
echo ""

echo "=== Docker Services ==="
docker-compose -f docker-compose.production.yml ps
echo ""

echo "=== VPN Status ==="
sudo vpn-status
echo ""

echo "=== System Resources ==="
df -h
free -h
echo ""

echo "=== Network Status ==="
ip addr show tun0 2>/dev/null || echo "VPN interface not active"
echo ""
EOF

chmod +x /usr/local/bin/monitor-pfcam
```

### 7.2 Automated Maintenance
```bash
# Add to crontab
sudo crontab -e

# Add these lines:
0 2 * * * /usr/local/bin/backup-pfcam
*/5 * * * * /usr/local/bin/monitor-pfcam >> /var/log/pfcam-monitor.log
0 3 * * 0 docker system prune -f
```

## Troubleshooting

### Common Issues

1. **VPN Connection Fails**
   ```bash
   # Check VPN service
   sudo systemctl status openvpn@openvpn
   
   # Check firewall
   sudo ufw status
   
   # Check logs
   sudo tail -f /var/log/openvpn/openvpn.log
   ```

2. **Camera Cannot Connect**
   ```bash
   # Test network connectivity
   ping 10.8.0.1
   
   # Check routing
   ip route show
   
   # Test application
   curl http://10.8.0.1:8000/health
   ```

3. **Application Errors**
   ```bash
   # Check application logs
   docker-compose -f docker-compose.production.yml logs -f backend
   
   # Check database
   docker-compose -f docker-compose.production.yml exec postgres psql -U pfcam -d pfcam
   ```

### Emergency Procedures

1. **VPN Server Down**
   ```bash
   sudo systemctl restart openvpn@openvpn
   sudo vpn-status
   ```

2. **Application Down**
   ```bash
   docker-compose -f docker-compose.production.yml restart
   docker-compose -f docker-compose.production.yml logs -f
   ```

3. **Network Issues**
   ```bash
   # Check SIMSY network connectivity
   ping simsy.network
   
   # Restart network services
   sudo systemctl restart networking
   ```

## Support and Contact

For SIMSY network support and VPN configuration assistance:
- **SIMSY Network Administrator**: [Contact Information]
- **Technical Support**: [Contact Information]
- **Emergency Contact**: [Contact Information]

## Maintenance Schedule

- **Daily**: Monitor system status and logs
- **Weekly**: Review performance metrics and backup verification
- **Monthly**: Update system packages and security patches
- **Quarterly**: Rotate certificates and review security configuration
- **Annually**: Full system audit and capacity planning 