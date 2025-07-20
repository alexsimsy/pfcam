# SIMSY Network PFCAM - Quick Reference

## 🖥️ Server Specifications

### Minimum Requirements
- **CPU**: 4 cores (Intel i5/AMD Ryzen 5)
- **RAM**: 8GB DDR4
- **Storage**: 100GB SSD
- **Network**: 1Gbps Ethernet
- **OS**: Ubuntu 20.04+ LTS

### Recommended Production
- **CPU**: 8 cores (Intel i7/AMD Ryzen 7)
- **RAM**: 16GB DDR4
- **Storage**: 500GB NVMe SSD + 2TB HDD
- **Network**: 1Gbps Ethernet
- **OS**: Ubuntu 22.04 LTS

## 🚀 Installation Steps

### 1. Server Setup
```bash
# Download and run installation script
wget https://raw.githubusercontent.com/your-repo/pfcam/main/vpn-setup/install-server.sh
chmod +x install-server.sh
sudo ./install-server.sh
```

### 2. Application Deployment
```bash
# Copy application files
cp -r /path/to/pfcam/* /opt/pfcam/

# Deploy with Docker
cd /opt/pfcam
docker-compose -f docker-compose.production.yml up -d
```

### 3. Create VPN Clients
```bash
# Create client for camera/router
sudo create-vpn-client camera001

# Create additional clients
sudo create-vpn-client camera002
sudo create-vpn-client router001
```

## 🌐 Network Configuration

### VPN Server Details
- **Protocol**: UDP
- **Port**: 1194
- **Subnet**: 10.8.0.0/24
- **Server Interface**: 10.8.0.1

### Application Ports
- **Backend API**: `SERVER_IP:8000`
- **Frontend**: `SERVER_IP:3000`
- **RTSP**: `SERVER_IP:8554`
- **HLS**: `SERVER_IP:8888`
- **FTP**: `SERVER_IP:21`

### SIMSY Network Requirements
- **APN**: simsy.network
- **Routing**: Direct to `SERVER_IP:1194`
- **QoS**: High priority for camera traffic
- **Subnet**: Dedicated IP range for VPN clients

## 🔧 Management Commands

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
```

### Application Management
```bash
# Check application status
docker-compose -f docker-compose.production.yml ps

# View application logs
docker-compose -f docker-compose.production.yml logs -f

# Restart services
docker-compose -f docker-compose.production.yml restart
```

### System Monitoring
```bash
# Check system resources
htop

# Monitor network
sudo tcpdump -i tun0

# Check firewall status
sudo ufw status
```

## 📋 SIMSY Network Configuration

### Required Information for SIMSY
```
Server IP: [YOUR_SERVER_IP]
VPN Port: 1194 (UDP)
VPN Subnet: 10.8.0.0/24

Application Ports:
- Backend: [SERVER_IP]:8000
- Frontend: [SERVER_IP]:3000
- RTSP: [SERVER_IP]:8554
- HLS: [SERVER_IP]:8888
- FTP: [SERVER_IP]:21

Expected Traffic:
- Number of cameras: [X]
- Bandwidth per camera: [Y] Mbps
- Total bandwidth: [Z] Mbps
```

### SIM Card Configuration
- **APN**: simsy.network
- **Authentication**: PAP/CHAP
- **Group**: PFCAM-VPN-Group
- **QoS**: Camera-High-Priority

## 🔐 Security Information

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

## 🚨 Troubleshooting

### Common Issues

**VPN Connection Fails**
```bash
# Check VPN service
sudo systemctl status openvpn@openvpn

# Check firewall
sudo ufw status

# Check logs
sudo tail -f /var/log/openvpn/openvpn.log
```

**Application Not Accessible**
```bash
# Check application status
docker-compose -f docker-compose.production.yml ps

# Check application logs
docker-compose -f docker-compose.production.yml logs backend

# Test connectivity
curl http://localhost:8000/health
```

**Camera Cannot Connect**
```bash
# Test VPN connectivity
ping 10.8.0.1

# Check routing
ip route show

# Test application
curl http://10.8.0.1:8000/health
```

## 📞 Support Information

### SIMSY Network Support
- **Email**: [admin@simsy.network]
- **Phone**: [Contact Number]
- **Emergency**: [Emergency Number]

### Technical Support
- **Email**: [support@simsy.network]
- **Phone**: [Support Number]
- **Hours**: [Business Hours]

## 📁 File Locations

### Configuration Files
- **VPN Config**: `/etc/openvpn/openvpn.conf`
- **Client Configs**: `/etc/openvpn/clients/`
- **Application**: `/opt/pfcam/`
- **Environment**: `/opt/pfcam/.env`
- **Network Info**: `/opt/pfcam/network-info.txt`

### Log Files
- **VPN Logs**: `/var/log/openvpn/`
- **Application Logs**: Docker containers
- **System Logs**: `/var/log/`

## 🔄 Maintenance Schedule

### Daily
- Check system status: `sudo vpn-status`
- Monitor application: `docker-compose ps`
- Review logs for errors

### Weekly
- Backup system: `sudo backup-pfcam`
- Update system packages
- Review performance metrics

### Monthly
- Rotate certificates (if needed)
- Update security patches
- Review firewall rules

### Quarterly
- Full system audit
- Performance optimization
- Security review

## 📊 Performance Monitoring

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
```

This quick reference provides all essential information for managing your SIMSY network PFCAM deployment. 