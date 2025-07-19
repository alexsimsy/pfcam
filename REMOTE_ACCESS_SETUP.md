# Remote Access Setup

## Overview
This setup enables remote access to the PFCAM frontend using alternative ports (8080/8443) to avoid ISP blocking of standard ports (80/443).

## Port Configuration
- **HTTP:** Port 8080
- **HTTPS:** Port 8443
- **VPN:** Port 1194 (UDP) - for camera communication

## Quick Setup

### 1. Run the Setup Script
```bash
chmod +x setup-remote-access.sh
./setup-remote-access.sh
```

### 2. Configure Router Port Forwarding
In your router's admin panel, set up port forwarding:
- **External Port 8080** → **Internal IP:YOUR_SERVER_IP:8080**
- **External Port 8443** → **Internal IP:YOUR_SERVER_IP:8443**

### 3. Access Your Application
Once configured, access your application from any remote browser:
- **HTTP:** `http://YOUR_PUBLIC_IP:8080`
- **HTTPS:** `https://YOUR_PUBLIC_IP:8443`

## Manual Setup Steps

### Server Firewall Configuration
```bash
sudo ufw allow 8080/tcp
sudo ufw allow 8443/tcp
sudo ufw status
```

### Generate SSL Certificates
```bash
chmod +x nginx/create-ssl-cert.sh
./nginx/create-ssl-cert.sh
```

### Restart Application
```bash
docker-compose down
docker-compose up -d
```

## Security Notes
- Self-signed certificates are used for HTTPS (browser will show security warning)
- For production, replace with proper SSL certificates from Let's Encrypt
- VPN connection (port 1194) remains separate for secure camera communication

## Troubleshooting
- **Can't access from outside:** Check router port forwarding
- **SSL warning:** Normal with self-signed certificates, click "Advanced" → "Proceed"
- **Connection refused:** Verify firewall rules and docker-compose is running 