# Event Cam Deployment Guide

## 🚀 Quick Start Deployment

### Option 1: Automated Download (Recommended)

```bash
# Download the deployment package
curl -sSL https://raw.githubusercontent.com/alexsimsy/pfcam/main/scripts/download-deployment.sh | bash

# Or download manually and run
wget https://raw.githubusercontent.com/alexsimsy/pfcam/main/scripts/download-deployment.sh
chmod +x download-deployment.sh
./download-deployment.sh
```

### Option 2: Manual Download

1. Go to [GitHub Releases](https://github.com/alexsimsy/pfcam/releases)
2. Download the latest `event-cam-deployment-*.tar.gz`
3. Extract and run the deployment script

## 📋 Prerequisites

- **Server**: Ubuntu 20.04+ or Debian 11+
- **RAM**: 4GB+ (2GB minimum)
- **Storage**: 20GB+ available space
- **Access**: Root or sudo privileges
- **Network**: Internet access for downloads

## 🔧 Server Setup

### 1. Initial Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl wget git docker.io docker-compose
```

### 2. Download and Deploy

```bash
# Download deployment package
./download-deployment.sh

# Navigate to deployment directory
cd event-cam-deployment/event-cam-deployment-*

# Run deployment
./hetzner-deploy.sh
```

## 🔐 Security Features

### VPN Access
- WireGuard VPN for secure remote access
- Client certificate generation
- Network isolation

### SSL/TLS
- Automatic SSL certificate generation
- HTTPS enforcement
- Secure reverse proxy

### Authentication
- JWT-based authentication
- Role-based access control
- Secure credential management

## 📊 Monitoring

### System Monitoring
- Resource usage monitoring
- Automatic restart on failure
- Log aggregation

### Application Monitoring
- Real-time notification system
- WebSocket connection status
- Event capture monitoring

## 🔄 Updates

### Automatic Updates
```bash
# Check for updates
./update-ports.sh

# Restart services
docker compose restart
```

### Manual Updates
1. Download new deployment package
2. Backup current configuration
3. Run deployment script
4. Verify functionality

## 🆘 Troubleshooting

### Common Issues

**Port Conflicts**
```bash
# Check port usage
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443

# Update ports if needed
./update-ports.sh
```

**Docker Issues**
```bash
# Restart Docker
sudo systemctl restart docker

# Clean up containers
docker system prune -f
```

**VPN Connection Issues**
```bash
# Check VPN status
cd vpn-setup
./test-vpn.sh

# Recreate client
./create-client.sh
```

### Logs and Debugging

```bash
# View application logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f frontend

# Check system resources
./vpn-setup/monitor-4gb-ram.sh
```

## 📞 Support

### Documentation
- [Installation Guide](INSTALLATION_GUIDE.md)
- [Quick Start Guide](QUICKSTART.md)
- [VPN Setup Guide](vpn-setup/README.md)

### GitHub Resources
- [Issues](https://github.com/alexsimsy/pfcam/issues)
- [Releases](https://github.com/alexsimsy/pfcam/releases)
- [Documentation](https://github.com/alexsimsy/pfcam/tree/main/docs)

### Emergency Contacts
- Create GitHub issue for bugs
- Check logs for error details
- Review troubleshooting section

## 🔒 Security Best Practices

1. **Change Default Passwords**
   - Update admin password after first login
   - Use strong, unique passwords

2. **Network Security**
   - Use VPN for remote access
   - Configure firewall rules
   - Enable SSL/TLS

3. **Regular Updates**
   - Keep system packages updated
   - Monitor for security patches
   - Backup configurations regularly

4. **Access Control**
   - Limit admin access
   - Use role-based permissions
   - Monitor user activity

## 📈 Performance Optimization

### For 4GB RAM Servers
- Use `docker-compose.4gb-ram.yml`
- Monitor resource usage
- Optimize camera settings

### For High-Traffic Deployments
- Scale horizontally with load balancer
- Use dedicated database server
- Implement caching strategies

---

**Version**: 1.0.0  
**Last Updated**: 2025-07-20  
**Compatible with**: Event Cam v1.0.0+ 