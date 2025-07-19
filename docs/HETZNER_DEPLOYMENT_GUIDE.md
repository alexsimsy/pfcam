# PFCAM Hetzner Server Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying PFCAM on Hetzner servers with automated WireGuard VPN setup, firewall configuration, and application deployment.

## Architecture

```
Camera → Cellular Router → WireGuard VPN → Hetzner Server → PFCAM Application
```

## Prerequisites

### Hetzner Server Requirements
- **OS**: Ubuntu 22.04 LTS (recommended)
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 50GB+ SSD
- **CPU**: 2+ cores
- **Network**: Public IP address
- **Root access**: Required for deployment

### Network Requirements
- **WireGuard Port**: 51820/UDP (for VPN)
- **Application Ports**: 80, 443, 8000, 3000, 8554, 8888, 21, 30000-30009
- **SSH Access**: Port 22 (for deployment)

## Deployment Process

### Step 1: Server Preparation

#### 1.1 Create Hetzner Server
1. **Log into Hetzner Cloud Console**
2. **Create new server**:
   - **Name**: `pfcam-server-001`
   - **Location**: Choose closest to your customers
   - **Image**: Ubuntu 22.04
   - **Type**: CX21 (4GB RAM) or CX31 (8GB RAM)
   - **Network**: Default network
   - **SSH Key**: Add your SSH key for secure access

#### 1.2 Access Server
```bash
# SSH into your server
ssh root@YOUR_SERVER_IP

# Update system
apt update && apt upgrade -y
```

### Step 2: Automated Deployment

#### 2.1 Download Deployment Script
```bash
# Create scripts directory
mkdir -p /opt/pfcam/scripts
cd /opt/pfcam/scripts

# Download deployment script (you'll need to upload this to your server)
# Option 1: Upload via SCP
scp hetzner-deploy.sh root@YOUR_SERVER_IP:/opt/pfcam/scripts/

# Option 2: Create script directly on server
nano hetzner-deploy.sh
# Paste the script content
```

#### 2.2 Run Automated Deployment
```bash
# Make script executable
chmod +x hetzner-deploy.sh

# Run deployment
./hetzner-deploy.sh
```

**The script will:**
- ✅ Update system packages
- ✅ Install Docker and Docker Compose
- ✅ Configure WireGuard VPN server
- ✅ Set up firewall (UFW) with all required ports
- ✅ Configure fail2ban for security
- ✅ Deploy PFCAM application
- ✅ Set up monitoring and health checks
- ✅ Generate client configurations
- ✅ Create deployment summary

### Step 3: Client Configuration

#### 3.1 Camera Setup
```bash
# On your local machine, use the client setup script
./scripts/client-setup.sh camera -s YOUR_SERVER_IP -k SERVER_PUBLIC_KEY

# This will generate:
# - camera001.conf (WireGuard configuration)
# - install-camera-camera001.sh (Installation script)
```

#### 3.2 Router Setup
```bash
# Generate router configuration
./scripts/client-setup.sh router -s YOUR_SERVER_IP -k SERVER_PUBLIC_KEY -c router001 -i 10.0.0.20

# This will generate:
# - router001.conf (WireGuard configuration)
# - install-router-router001.sh (Installation script)
```

#### 3.3 Install on Camera
```bash
# Copy files to camera
scp camera001.conf root@CAMERA_IP:/tmp/
scp install-camera-camera001.sh root@CAMERA_IP:/tmp/

# SSH into camera and run installation
ssh root@CAMERA_IP
cd /tmp
chmod +x install-camera-camera001.sh
./install-camera-camera001.sh
```

#### 3.4 Install on Router
```bash
# Copy files to router
scp router001.conf root@ROUTER_IP:/tmp/
scp install-router-router001.sh root@ROUTER_IP:/tmp/

# SSH into router and run installation
ssh root@ROUTER_IP
cd /tmp
chmod +x install-router-router001.sh
./install-router-router001.sh
```

### Step 4: Server Configuration

#### 4.1 Add Clients to WireGuard
```bash
# SSH into server
ssh root@YOUR_SERVER_IP

# Add camera to WireGuard
wg set wg0 peer CAMERA_PUBLIC_KEY allowed-ips 10.0.0.10/32

# Add router to WireGuard
wg set wg0 peer ROUTER_PUBLIC_KEY allowed-ips 10.0.0.20/32

# Save configuration
wg-quick save wg0
```

#### 4.2 Configure Camera Network Settings
1. **Access camera web interface**
2. **Network Settings**:
   - **IP Address**: 10.0.0.10
   - **Subnet Mask**: 255.255.255.0
   - **Gateway**: 10.0.0.1
   - **DNS**: 8.8.8.8, 8.8.4.4

3. **Server Settings**:
   - **Server IP**: 10.0.0.1
   - **API Port**: 8000
   - **FTP Server**: 10.0.0.1
   - **FTP Port**: 21

#### 4.3 Configure Router Settings
1. **Access router admin interface**
2. **WireGuard Settings**:
   - Import `router001.conf`
   - Enable auto-start
   - Set routing for camera traffic

3. **Network Settings**:
   - Configure NAT for camera network
   - Route camera traffic through VPN

### Step 5: Testing and Validation

#### 5.1 Test VPN Connectivity
```bash
# From camera, test VPN connection
ping 10.0.0.1

# From router, test VPN connection
ping 10.0.0.1

# Test application connectivity
curl http://10.0.0.1:8000/health
```

#### 5.2 Test Application Features
1. **Web Interface**: http://YOUR_SERVER_IP:3000
2. **API Health**: http://YOUR_SERVER_IP:8000/health
3. **Camera Registration**: Via web interface
4. **Video Streaming**: Test live video feed
5. **Event Recording**: Test motion detection
6. **FTP Upload**: Test file transfer

#### 5.3 Monitor System Status
```bash
# Check all services
docker compose ps

# Check WireGuard status
systemctl status wg-quick@wg0

# Check firewall status
ufw status

# Check monitoring logs
tail -f /var/log/pfcam-monitor.log
```

## Security Configuration

### Firewall Rules
The deployment script automatically configures UFW with:
- **SSH**: Port 22 (from anywhere)
- **WireGuard**: Port 51820/UDP (from anywhere)
- **Application**: Ports 80, 443, 8000, 3000, 8554, 8888, 21, 30000-30009
- **Default**: Deny all other incoming traffic

### Fail2ban Protection
- **SSH Protection**: 3 failed attempts = 1 hour ban
- **Web Protection**: 3 failed attempts = 1 hour ban
- **Log Monitoring**: Automatic threat detection

### WireGuard Security
- **Key-based authentication**: No passwords
- **Encrypted traffic**: AES-256 encryption
- **Perfect forward secrecy**: Session keys
- **No metadata leakage**: Minimal logging

## Monitoring and Maintenance

### Automated Monitoring
The deployment includes a monitoring script that runs every 5 minutes:
- **Docker Services**: Auto-restart if down
- **WireGuard**: Auto-restart if down
- **Disk Space**: Alert if >90%
- **Memory Usage**: Alert if >90%

### Log Management
```bash
# Application logs
docker compose logs -f

# System logs
journalctl -u docker
journalctl -u wg-quick@wg0

# Monitoring logs
tail -f /var/log/pfcam-monitor.log

# Deployment logs
tail -f /var/log/pfcam-deployment.log
```

### Backup Strategy
```bash
# Create backup script
cat > /usr/local/bin/pfcam-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/pfcam/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup database
docker compose exec -T postgres pg_dump -U pfcam pfcam > "$BACKUP_DIR/db_$DATE.sql"

# Backup configuration files
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" /etc/wireguard /opt/pfcam/.env

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/pfcam-backup.sh

# Add to crontab (daily backup at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/pfcam-backup.sh") | crontab -
```

## Troubleshooting

### Common Issues

#### 1. WireGuard Connection Issues
```bash
# Check WireGuard status
systemctl status wg-quick@wg0

# Check WireGuard interface
ip addr show wg0

# Check WireGuard peers
wg show

# Check firewall
ufw status
```

#### 2. Application Not Starting
```bash
# Check Docker services
docker compose ps

# Check application logs
docker compose logs backend
docker compose logs frontend

# Check system resources
free -h
df -h
```

#### 3. Camera Not Connecting
```bash
# Test VPN connectivity
ping 10.0.0.1

# Test application connectivity
curl http://10.0.0.1:8000/health

# Check camera configuration
# Verify IP settings and server configuration
```

#### 4. Performance Issues
```bash
# Check system resources
htop
iotop
nethogs

# Check Docker resource usage
docker stats

# Check application performance
docker compose logs backend | grep -i error
```

### Recovery Procedures

#### Complete System Recovery
```bash
# Stop all services
docker compose down

# Restart WireGuard
systemctl restart wg-quick@wg0

# Restart Docker
systemctl restart docker

# Start application
docker compose up -d

# Check status
docker compose ps
systemctl status wg-quick@wg0
```

#### Database Recovery
```bash
# Restore from backup
docker compose exec -T postgres psql -U pfcam pfcam < /opt/pfcam/backups/db_YYYYMMDD_HHMMSS.sql
```

## Scaling and Multi-Site Deployment

### Multiple Servers
For multiple customer sites, repeat the deployment process for each server:
1. **Create new Hetzner server**
2. **Run automated deployment script**
3. **Configure unique client IPs** (10.0.0.x, 10.0.1.x, etc.)
4. **Deploy client configurations**

### Load Balancing
For high-availability deployments:
1. **Use Hetzner Load Balancer**
2. **Configure multiple application instances**
3. **Set up database replication**
4. **Implement shared storage**

## Cost Optimization

### Hetzner Pricing (Monthly)
- **CX21 (4GB RAM)**: €5.83/month
- **CX31 (8GB RAM)**: €11.66/month
- **CX41 (16GB RAM)**: €23.32/month

### Bandwidth Costs
- **Included**: 20TB/month
- **Additional**: €0.01/GB

### Storage Costs
- **Local Storage**: Included with server
- **Block Storage**: €0.0049/GB/month

## Support and Maintenance

### Regular Maintenance Tasks
1. **Weekly**: Check system logs and performance
2. **Monthly**: Update system packages
3. **Quarterly**: Review security configurations
4. **Annually**: Plan for capacity upgrades

### Support Contacts
- **Technical Issues**: Check logs and monitoring
- **Hetzner Support**: Via Cloud Console
- **Application Support**: Review documentation

## Conclusion

This automated deployment process significantly reduces the time and complexity of deploying PFCAM on Hetzner servers. The complete setup can be accomplished in under 30 minutes, with minimal manual intervention required.

### Key Benefits
- ✅ **Fully Automated**: One script handles everything
- ✅ **Secure by Default**: Firewall, fail2ban, WireGuard
- ✅ **Production Ready**: Monitoring, logging, backups
- ✅ **Scalable**: Easy to deploy multiple instances
- ✅ **Cost Effective**: Optimized for Hetzner infrastructure

### Next Steps
1. **Test deployment** on a development server
2. **Customize configurations** for your specific needs
3. **Deploy to production** servers
4. **Monitor and maintain** deployed systems
5. **Scale as needed** for additional customers

---

*This deployment guide provides a complete solution for automated PFCAM deployment on Hetzner servers, enabling rapid scaling and consistent deployments across multiple customer sites.* 