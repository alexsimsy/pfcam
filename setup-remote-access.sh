#!/bin/bash

echo "Setting up remote access for PFCAM application..."
echo "Using ports 8080 (HTTP) and 8443 (HTTPS) to avoid ISP blocking"

# Configure firewall for alternative ports
echo "Configuring firewall..."
sudo ufw allow 8080/tcp
sudo ufw allow 8443/tcp

# Generate SSL certificates if they don't exist
if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
    echo "Generating SSL certificates..."
    chmod +x nginx/create-ssl-cert.sh
    ./nginx/create-ssl-cert.sh
else
    echo "SSL certificates already exist"
fi

# Restart the application
echo "Restarting application with new configuration..."
docker-compose down
docker-compose up -d

echo ""
echo "=== REMOTE ACCESS SETUP COMPLETE ==="
echo ""
echo "Your application is now accessible at:"
echo "  HTTP:  http://YOUR_SERVER_IP:8080"
echo "  HTTPS: https://YOUR_SERVER_IP:8443"
echo ""
echo "IMPORTANT: Configure your router to forward:"
echo "  - Port 8080 → Your server's internal IP"
echo "  - Port 8443 → Your server's internal IP"
echo ""
echo "Firewall status:"
sudo ufw status 