# Event Cam Deployment Scripts

This package contains all the necessary scripts for deploying Event Cam to production servers.

## 🔐 Secure Download

These scripts are available through GitHub Releases for secure distribution.

### Download Instructions:
1. Go to the [GitHub Releases page](https://github.com/alexsimsy/pfcam/releases)
2. Download the latest release package
3. Extract and follow the deployment guide

## 📦 Package Contents

### Core Deployment Scripts
- `hetzner-deploy.sh` - Main deployment script for Hetzner servers
- `client-setup.sh` - Client-side setup and configuration
- `install-server.sh` - Server installation and setup

### VPN Setup
- `vpn-setup/` - Complete VPN configuration and management
- `create-client.sh` - VPN client creation
- `init-vpn.sh` - VPN initialization

### Configuration Files
- `docker-compose.production.yml` - Production Docker configuration
- `docker-compose.4gb-ram.yml` - Optimized for 4GB RAM servers
- `nginx/nginx.conf` - Nginx reverse proxy configuration
- `mediamtx.yml` - MediaMTX streaming configuration

### Documentation
- `INSTALLATION_GUIDE.md` - Complete installation guide
- `QUICKSTART.md` - Quick start instructions
- `DEPLOYMENT_GUIDE.md` - Detailed deployment guide

## 🚀 Quick Start

1. Download the latest release
2. Extract the package
3. Run: `chmod +x hetzner-deploy.sh`
4. Run: `./hetzner-deploy.sh`

## 🔧 Requirements

- Ubuntu 20.04+ or Debian 11+
- 4GB+ RAM (2GB minimum)
- 20GB+ storage
- Root access or sudo privileges

## 📞 Support

For deployment support, refer to the documentation or create an issue on GitHub.

## 🔒 Security

- Scripts are signed and verified through GitHub Releases
- Always verify the download checksum
- Use HTTPS for all downloads
- Keep deployment credentials secure

---

**Version**: 1.0.0  
**Last Updated**: 2025-07-20  
**Compatible with**: Event Cam v1.0.0+ 