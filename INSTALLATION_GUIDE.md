# PFCAM Installation Guide - SIMSY Network Deployment

## Overview
This guide provides complete instructions for deploying the PFCAM camera management system with OpenVPN server for SIMSY's mobile network infrastructure.

## Architecture
```
Camera → Router with SIM → SIMSY Network → VPN → Ubuntu Server → PFCAM Application
```

## Table of Contents
1. [Server Requirements](#server-requirements)
2. [4GB RAM Optimizations](#4gb-ram-optimizations)
3. [Installation Process](#installation-process)
4. [Network Configuration](#network-configuration)
5. [Application Deployment](#application-deployment)
6. [Camera Configuration](#camera-configuration)
7. [Testing and Validation](#testing-and-validation)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance](#maintenance)

## Server Requirements

### Minimum Requirements (Demo/Test)
- **CPU**: 4 cores (Intel i5/AMD Ryzen 5 or better)
- **RAM**: 4GB DDR4 (minimum) / 8GB DDR4 (recommended)
- **Storage**: 100GB SSD
- **Network**: 1Gbps Ethernet
- **OS**: Ubuntu 20.04 LTS or 22.04 LTS

**Note**: 4GB RAM will work but requires careful resource management. See [4GB RAM Optimizations](#4gb-ram-optimizations) section below.

### Recommended Production
- **CPU**: 8 cores (Intel i7/AMD Ryzen 7 or better)
- **RAM**: 16GB DDR4
- **Storage**: 500GB NVMe SSD + 2TB HDD for video storage
- **Network**: 1Gbps Ethernet (or 10Gbps for high-traffic)
- **OS**: Ubuntu 22.04 LTS

### High-Performance (Multiple Customers)
- **CPU**: 16+ cores (Intel Xeon/AMD EPYC)
- **RAM**: 32GB+ DDR4
- **Storage**: 1TB NVMe SSD + 4TB+ HDD for video storage
- **Network**: 10Gbps Ethernet
- **OS**: Ubuntu 22.04 LTS

## 4GB RAM Optimizations

### Memory Usage Breakdown
With 4GB RAM, you'll need to carefully manage memory allocation:

- **Ubuntu System**: ~500MB
- **Docker Engine**: ~200MB
- **PostgreSQL**: ~512MB (reduced from default)
- **Redis**: ~128MB (reduced from default)
- **Backend API**: ~256MB
- **Frontend**: ~128MB
- **MediaMTX**: ~256MB
- **FTP Server**: ~64MB
- **OpenVPN**: ~64MB
- **Nginx**: ~64MB
- **System Buffer/Cache**: ~1.5GB
- **Available for applications**: ~500MB

### Docker Memory Limits
Add these memory limits to your `docker-compose.production.yml`:

```yaml
services:
  postgres:
    # ... existing config ...
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  redis:
    # ... existing config ...
    deploy:
      resources:
        limits:
          memory: 128M
        reservations:
          memory: 64M

  backend:
    # ... existing config ...
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M

  frontend:
    # ... existing config ...
    deploy:
      resources:
        limits:
          memory: 128M
        reservations:
          memory: 64M

  mediamtx:
    # ... existing config ...
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M

  ftp:
    # ... existing config ...
    deploy:
      resources:
        limits:
          memory: 64M
        reservations:
          memory: 32M
```

### PostgreSQL Optimizations
Create a custom PostgreSQL configuration for low memory:

```bash
# Create custom postgres config
sudo tee /opt/pfcam/postgres-low-memory.conf > /dev/null << 'EOF'
# Low memory PostgreSQL configuration for 4GB RAM
shared_buffers = 128MB
effective_cache_size = 512MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 2
max_parallel_workers_per_gather = 1
max_parallel_workers = 2
max_parallel_maintenance_workers = 1
EOF
```

Update your `docker-compose.production.yml`:

```yaml
services:
  postgres:
    # ... existing config ...
    volumes:
      - ./postgres-low-memory.conf:/etc/postgresql/postgresql.conf
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
```

### System Optimizations
Add these optimizations to your server:

```bash
# Create swap file (2GB)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Optimize system settings
sudo tee -a /etc/sysctl.conf > /dev/null << 'EOF'
# Memory optimizations
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
vm.overcommit_memory = 1

# Network optimizations
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
EOF

sudo sysctl -p
```

### Application Optimizations

#### Backend Optimizations
Add these environment variables to your `.env`:

```bash
# Add to .env file
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
UVICORN_WORKERS=1
UVICORN_WORKER_CLASS=sync
```

#### Frontend Optimizations
Update your frontend build for production:

```bash
# In your frontend Dockerfile, add:
ENV NODE_ENV=production
ENV GENERATE_SOURCEMAP=false
```

### Monitoring Memory Usage
Add these monitoring commands:

```bash
# Check memory usage
free -h
htop

# Check Docker memory usage
docker stats --no-stream

# Check specific container memory
docker stats postgres redis backend frontend mediamtx --no-stream

# Monitor memory in real-time
watch -n 1 'free -h && echo "---" && docker stats --no-stream'
```

### Performance Recommendations for 4GB RAM

1. **Limit concurrent cameras**: Start with 2-4 cameras maximum
2. **Reduce video quality**: Use lower resolution/bitrate for live streams
3. **Enable video compression**: Configure cameras for H.264/H.265 compression
4. **Monitor closely**: Set up alerts for memory usage > 90%
5. **Plan for upgrade**: Consider upgrading to 8GB RAM for production use

### Emergency Memory Management
If you run into memory issues:

```bash
# Clear Docker cache
docker system prune -f

# Restart services with memory limits
docker-compose -f docker-compose.production.yml restart

# Clear system cache
sudo sync && sudo echo 3 | sudo tee /proc/sys/vm/drop_caches

# Check what's using memory
ps aux --sort=-%mem | head -10
```

## Installation Process

### Step 1: Server Preparation

#### 1.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release ufw fail2ban htop
```

#### 1.2 Install Docker
```bash
# Remove old versions
sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add current user to docker group
sudo usermod -aG docker $USER
```

### Step 2: VPN Server Setup

#### 2.1 Install OpenVPN
```bash
sudo apt install -y openvpn easy-rsa

# Create VPN directories
sudo mkdir -p /etc/openvpn/easy-rsa
sudo mkdir -p /etc/openvpn/ccd
sudo mkdir -p /etc/openvpn/clients
sudo mkdir -p /var/log/openvpn

# Copy easy-rsa files
sudo cp -r /usr/share/easy-rsa/* /etc/openvpn/easy-rsa/
```

#### 2.2 Generate Certificates
```bash
# Navigate to easy-rsa directory
cd /etc/openvpn/easy-rsa

# Initialize PKI
./easyrsa init-pki

# Build CA
echo "SIMSY" | ./easyrsa build-ca nopass

# Build server certificate
echo "yes" | ./easyrsa build-server-full server nopass

# Build Diffie-Hellman parameters
./easyrsa gen-dh

# Generate HMAC key
sudo openvpn --genkey secret ta.key

# Move certificates to OpenVPN directory
sudo cp pki/ca.crt /etc/openvpn/
sudo cp pki/issued/server.crt /etc/openvpn/
sudo cp pki/private/server.key /etc/openvpn/
sudo cp pki/dh.pem /etc/openvpn/
sudo cp ta.key /etc/openvpn/
```

#### 2.3 Configure OpenVPN Server
```bash
# Create server configuration
sudo tee /etc/openvpn/openvpn.conf > /dev/null << 'EOF'
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
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Set proper permissions
sudo chown -R nobody:nogroup /etc/openvpn
sudo chmod 600 /etc/openvpn/*.key
sudo chmod 644 /etc/openvpn/*.crt
sudo chmod 644 /etc/openvpn/*.pem

# Start and enable OpenVPN service
sudo systemctl start openvpn@openvpn
sudo systemctl enable openvpn@openvpn
```

### Step 3: Firewall Configuration
```bash
# Reset UFW
sudo ufw --force reset

# Set defaults
sudo ufw default deny incoming
sudo ufw default allow outgoing

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
sudo ufw allow 21/tcp
sudo ufw allow 30000:30009/tcp

# Allow traffic from VPN subnet to application
sudo ufw allow from 10.8.0.0/24 to any port 8000
sudo ufw allow from 10.8.0.0/24 to any port 3000
sudo ufw allow from 10.8.0.0/24 to any port 8554
sudo ufw allow from 10.8.0.0/24 to any port 8888

# Enable UFW
sudo ufw --force enable
```

### Step 4: Create Management Scripts
```bash
# Create VPN client script
sudo tee /usr/local/bin/create-vpn-client > /dev/null << 'EOF'
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

sudo chmod +x /usr/local/bin/create-vpn-client

# Create VPN status script
sudo tee /usr/local/bin/vpn-status > /dev/null << 'EOF'
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

sudo chmod +x /usr/local/bin/vpn-status

# Create backup script
sudo tee /usr/local/bin/backup-pfcam > /dev/null << 'EOF'
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

sudo chmod +x /usr/local/bin/backup-pfcam
```

### Step 5: Create Sample Client
```bash
# Create sample client configuration
cd /etc/openvpn/easy-rsa
echo "yes" | ./easyrsa build-client-full camera001 nopass

# Get server IP
SERVER_IP=$(curl -s ifconfig.me)

# Create client configuration
sudo tee /etc/openvpn/clients/camera001.ovpn > /dev/null << EOF
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

sudo chmod 600 /etc/openvpn/clients/camera001.ovpn
```

## Network Configuration

### VPN Server Details
After installation, your VPN server will have these details:

- **Public IP**: `YOUR_SERVER_IP` (automatically detected or manually set)
- **VPN Protocol**: UDP
- **VPN Port**: 1194
- **VPN Subnet**: 10.8.0.0/24
- **VPN Server Interface**: 10.8.0.1

### Application Ports
- **Backend API**: `YOUR_SERVER_IP:8000`
- **Frontend Web**: `YOUR_SERVER_IP:3000`
- **RTSP Streaming**: `YOUR_SERVER_IP:8554`
- **HLS Streaming**: `YOUR_SERVER_IP:8888`
- **FTP Service**: `YOUR_SERVER_IP:21`

### SIMSY Network Configuration
Provide these details to SIMSY for network configuration:

```
SIMSY Network Configuration Request
==================================

Server Information:
- Public IP: [YOUR_SERVER_IP]
- VPN Port: 1194 (UDP)
- VPN Subnet: 10.8.0.0/24

Required Configuration:
1. APN: simsy.network
2. SIM Card Group: PFCAM-VPN-Group
3. Dedicated Subnet: [Allocated by SIMSY]
4. QoS Profile: Camera-High-Priority
5. Routing: Direct to [YOUR_SERVER_IP]

Application Ports:
- Backend API: [YOUR_SERVER_IP]:8000
- Frontend: [YOUR_SERVER_IP]:3000
- RTSP: [YOUR_SERVER_IP]:8554
- HLS: [YOUR_SERVER_IP]:8888
- FTP: [YOUR_SERVER_IP]:21

Expected Traffic:
- Number of cameras: [X]
- Estimated bandwidth per camera: [Y] Mbps
- Total expected bandwidth: [Z] Mbps

Contact Information:
- Technical Contact: [Name]
- Phone: [Number]
- Email: [Email]
```

## Application Deployment

### Step 1: Prepare Application Directory
```bash
# Create application directory
sudo mkdir -p /opt/pfcam
cd /opt/pfcam

# Copy application files
sudo cp -r /path/to/your/pfcam/* /opt/pfcam/

# Set ownership
sudo chown -R $USER:$USER /opt/pfcam
```

### Step 2: Configure Environment
```bash
# Create environment file
cat > .env << EOF
# SIMSY Network Production Environment Configuration
POSTGRES_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 64)
FTP_PUBLIC_HOST=$(curl -s ifconfig.me)
FTP_USER_NAME=ftpuser
FTP_USER_PASS=$(openssl rand -base64 16)
VITE_API_BASE_URL=http://$(curl -s ifconfig.me):8000
VITE_WS_URL=ws://$(curl -s ifconfig.me):8000/ws
VPN_SERVER_IP=$(curl -s ifconfig.me)
VPN_SUBNET=10.8.0.0/24
VPN_PORT=1194
SIMSY_APN=simsy.network
SIMSY_SUBNET=192.168.100.0/24
LOG_LEVEL=INFO
MONITORING_ENABLED=true
EOF

# Create necessary directories
mkdir -p vpn-config vpn-data vpn-logs vpn-monitor network-logs ftpdata
```

### Step 3: Deploy with Docker

#### For 4GB RAM Servers (Recommended)
```bash
# Deploy with 4GB RAM optimizations
docker-compose -f docker-compose.4gb-ram.yml up -d

# Check status
docker-compose -f docker-compose.4gb-ram.yml ps

# View logs
docker-compose -f docker-compose.4gb-ram.yml logs -f

# Monitor memory usage
sudo ./vpn-setup/monitor-4gb-ram.sh -s
```

#### For 8GB+ RAM Servers
```bash
# Deploy with standard configuration
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

## Camera Configuration

### Step 1: Create VPN Clients
```bash
# Create client for each camera/router
sudo create-vpn-client camera001
sudo create-vpn-client camera002
sudo create-vpn-client router001

# List created clients
ls -la /etc/openvpn/clients/
```

### Step 2: Router Setup (if using router with SIM)
1. **Install OpenVPN client** on router
2. **Upload client configuration** (`camera001.ovpn`)
3. **Configure OpenVPN client**:
   - Import configuration file
   - Set to auto-start
   - Configure routing for camera traffic

### Step 3: Camera Setup
1. **Configure camera network settings**:
   - Set static IP in VPN subnet (e.g., 10.8.0.10)
   - Set gateway to VPN server (10.8.0.1)
   - Configure DNS (8.8.8.8, 8.8.4.4)

2. **Configure camera server settings**:
   - Set server IP to VPN server (10.8.0.1)
   - Configure API endpoints
   - Set up video streaming

### Step 4: SIMSY Network Configuration
1. **Configure SIM card APN** to SIMSY network
2. **Set up routing** in SIMSY network
3. **Allocate dedicated IP subnet** for VPN clients
4. **Configure QoS** for camera traffic

## Testing and Validation

### Step 1: Test VPN Connectivity
```bash
# Check VPN service status
sudo vpn-status

# Test VPN server connectivity
ping 10.8.0.1

# Check connected clients
cat /var/log/openvpn/openvpn-status.log
```

### Step 2: Test Application Services
```bash
# Test backend API
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000

# Test database
docker-compose -f docker-compose.production.yml exec postgres pg_isready -U pfcam
```

### Step 3: Test Camera Connectivity
```bash
# From camera/router, test VPN connection
ping 10.8.0.1

# Test application connectivity
curl http://10.8.0.1:8000/health

# Test video streaming
curl http://10.8.0.1:8554
```

### Step 4: Comprehensive Testing Script
```bash
# Run comprehensive test
sudo ./vpn-setup/test-vpn.sh
```

## Troubleshooting

### Common Issues

#### VPN Connection Fails
```bash
# Check VPN service
sudo systemctl status openvpn@openvpn

# Check firewall
sudo ufw status

# Check logs
sudo tail -f /var/log/openvpn/openvpn.log

# Test configuration
sudo openvpn --config /etc/openvpn/openvpn.conf --test-crypto
```

#### Application Not Accessible
```bash
# Check application status
docker-compose -f docker-compose.production.yml ps

# Check application logs
docker-compose -f docker-compose.production.yml logs backend

# Test connectivity
curl http://localhost:8000/health

# Check firewall rules
sudo ufw status
```

#### Camera Cannot Connect
```bash
# Test network connectivity
ping 10.8.0.1

# Check routing
ip route show

# Test application
curl http://10.8.0.1:8000/health

# Check VPN interface
ip addr show tun0
```

### Emergency Procedures

#### VPN Server Down
```bash
sudo systemctl restart openvpn@openvpn
sudo vpn-status
```

#### Application Down
```bash
docker-compose -f docker-compose.production.yml restart
docker-compose -f docker-compose.production.yml logs -f
```

#### Network Issues
```bash
# Check SIMSY network connectivity
ping simsy.network

# Restart network services
sudo systemctl restart networking

# Check routing table
ip route show
```

## Maintenance

### Daily Tasks
```bash
# Check system status
sudo vpn-status
docker-compose -f docker-compose.production.yml ps

# Monitor logs
sudo tail -f /var/log/openvpn/openvpn.log
docker-compose -f docker-compose.production.yml logs -f
```

### Weekly Tasks
```bash
# Backup system
sudo backup-pfcam

# Update system packages
sudo apt update && sudo apt upgrade -y

# Review performance metrics
htop
df -h
free -h
```

### Monthly Tasks
```bash
# Rotate certificates (if needed)
cd /etc/openvpn/easy-rsa
./easyrsa renew server nopass

# Update security patches
sudo apt update && sudo apt upgrade -y

# Review firewall rules
sudo ufw status
```

### Quarterly Tasks
```bash
# Full system audit
sudo vpn-status
docker-compose -f docker-compose.production.yml ps
sudo ufw status
df -h
free -h

# Performance optimization
# Review and optimize based on usage patterns

# Security review
# Review logs and security configuration
```

## Management Commands Reference

### VPN Management
```bash
# Check VPN status
sudo vpn-status

# Create new client
sudo create-vpn-client <name>

# View VPN logs
sudo journalctl -u openvpn@openvpn -f

# Backup system
sudo backup-pfcam

# Test VPN configuration
sudo openvpn --config /etc/openvpn/openvpn.conf --test-crypto
```

### Application Management
```bash
# Check application status
docker-compose -f docker-compose.production.yml ps

# View application logs
docker-compose -f docker-compose.production.yml logs -f

# Restart services
docker-compose -f docker-compose.production.yml restart

# Update application
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d
```

### System Monitoring
```bash
# Check system resources
htop
df -h
free -h

# Monitor network
sudo tcpdump -i tun0
sudo netstat -tulpn

# Check firewall status
sudo ufw status

# Monitor VPN traffic
sudo tcpdump -i tun0 -n
```

## Security Considerations

### Firewall Rules
- **UDP 1194**: VPN traffic
- **TCP 8000**: Backend API
- **TCP 3000**: Frontend
- **TCP 8554**: RTSP streaming
- **TCP 8888**: HLS streaming
- **TCP 21**: FTP service

### VPN Security
- **Encryption**: AES-256-CBC
- **Authentication**: Certificate-based
- **HMAC**: Enabled
- **Perfect Forward Secrecy**: Enabled

### Network Security
- **IP forwarding**: Enabled for VPN routing
- **Firewall**: UFW configured with restrictive rules
- **Monitoring**: Comprehensive logging enabled
- **Backup**: Automated backup procedures

## Support Information

### SIMSY Network Support
- **Email**: [admin@simsy.network]
- **Phone**: [Contact Number]
- **Emergency**: [Emergency Number]

### Technical Support
- **Email**: [support@simsy.network]
- **Phone**: [Support Number]
- **Hours**: [Business Hours]

### File Locations
- **VPN Config**: `/etc/openvpn/openvpn.conf`
- **Client Configs**: `/etc/openvpn/clients/`
- **Application**: `/opt/pfcam/`
- **Environment**: `/opt/pfcam/.env`
- **Logs**: `/var/log/openvpn/`

## Performance Monitoring

### Key Metrics
- **VPN Connections**: Number of active clients
- **Bandwidth Usage**: Data transfer rates
- **Latency**: Network response times
- **CPU Usage**: Server resource utilization
- **Memory Usage**: Available RAM
- **Storage**: Disk space usage

### Monitoring Commands
```bash
# System resources
htop
df -h
free -h

# Network traffic
sudo tcpdump -i tun0
sudo netstat -tulpn

# VPN status
sudo vpn-status
cat /var/log/openvpn/openvpn-status.log

# Application status
docker-compose -f docker-compose.production.yml ps
docker-compose -f docker-compose.production.yml logs
```

This installation guide provides complete instructions for deploying the PFCAM system with SIMSY network integration. Follow each step carefully and test thoroughly before going live. 