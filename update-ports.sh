#!/bin/bash

echo "Updating existing PFCAM instance with new port configuration..."

# Stop the current containers
echo "Stopping current containers..."
docker-compose down

# Update firewall for new ports
echo "Updating firewall rules..."
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

# Rebuild and start with new configuration
echo "Starting containers with new port configuration..."
docker-compose up -d

echo ""
echo "=== UPDATE COMPLETE ==="
echo ""
echo "Your application is now accessible at:"
echo "  HTTP:  http://YOUR_SERVER_IP:8080"
echo "  HTTPS: https://YOUR_SERVER_IP:8443"
echo ""
echo "IMPORTANT: Update your router port forwarding:"
echo "  - Port 8080 → Your server's internal IP"
echo "  - Port 8443 → Your server's internal IP"
echo ""
echo "All existing data has been preserved!" 