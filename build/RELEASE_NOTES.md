# Event Cam Deployment Package v1.0.0

## 🎉 What's New

- Complete deployment automation for Hetzner servers
- VPN setup and management scripts
- Production-ready Docker configurations
- Comprehensive documentation
- Security hardening scripts

## 📦 Package Contents

### Core Scripts
- `hetzner-deploy.sh` - Main deployment script
- `client-setup.sh` - Client configuration
- `install-server.sh` - Server setup

### VPN Management
- Complete WireGuard VPN setup
- Client certificate generation
- Network configuration

### Configuration Files
- Production Docker Compose files
- Nginx reverse proxy config
- MediaMTX streaming config

### Documentation
- Installation guide
- Quick start guide
- Deployment guide

## 🚀 Quick Start

1. Extract the package
2. Run: `chmod +x hetzner-deploy.sh`
3. Run: `./hetzner-deploy.sh`

## 🔒 Security

- All scripts are signed and verified
- Checksums provided for verification
- HTTPS-only downloads
- Secure credential management

## 📋 Requirements

- Ubuntu 20.04+ or Debian 11+
- 4GB+ RAM (2GB minimum)
- 20GB+ storage
- Root access or sudo privileges

## 🔧 Installation

```bash
# Download and extract
wget https://github.com/alexsimsy/pfcam/releases/download/v1.0.0/event-cam-deployment-1.0.0.tar.gz
tar -xzf event-cam-deployment-1.0.0.tar.gz
cd event-cam-deployment-1.0.0

# Verify checksums
sha256sum -c checksums.txt

# Run deployment
chmod +x hetzner-deploy.sh
./hetzner-deploy.sh
```

## 📞 Support

For issues or questions:
- Create an issue on GitHub
- Check the documentation
- Review the installation guide

---

**Release Date**: 2025-07-20  
**Compatible with**: Event Cam v1.0.0+  
**Package Size**: 228K
