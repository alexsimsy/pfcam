#!/bin/bash

# PFCAM Hetzner Server Automated Deployment Script
# This script automates the complete setup of a Hetzner server for PFCAM deployment
# including WireGuard VPN, firewall configuration, and application deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/var/log/pfcam-deployment.log"

# Function to log messages
log() {
    echo -e "${2:-$GREEN}$1${NC}" | tee -a "$LOG_FILE"
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log "Please run this script as root (use sudo)" "$RED"
        exit 1
    fi
}

# Function to get user input with validation
get_input() {
    local prompt="$1"
    local required="${2:-false}"
    local default="$3"
    
    while true; do
        if [ -n "$default" ]; then
            read -p "$prompt [$default]: " input
            input="${input:-$default}"
        else
            read -p "$prompt: " input
        fi
        
        if [ "$required" = "true" ] && [ -z "$input" ]; then
            log "This field is required. Please try again." "$RED"
            continue
        fi
        
        echo "$input"
        break
    done
}

# Function to generate secure passwords
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to update system
update_system() {
    log "Updating system packages..." "$BLUE"
    apt update && apt upgrade -y
    apt install -y curl wget git unzip software-properties-common \
                   apt-transport-https ca-certificates gnupg lsb-release \
                   ufw fail2ban htop wireguard wireguard-tools \
                   qrencode resolvconf
}

# Function to install Docker
install_docker() {
    log "Installing Docker..." "$BLUE"
    
    # Remove old versions
    apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Add Docker GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    # Add current user to docker group
    usermod -aG docker $SUDO_USER
    
    log "✓ Docker installed successfully" "$GREEN"
}

# Function to configure WireGuard
setup_wireguard() {
    log "Setting up WireGuard VPN..." "$BLUE"
    
    # Generate server keys
    cd /etc/wireguard
    wg genkey | tee server_private.key | wg pubkey > server_public.key
    SERVER_PRIVATE_KEY=$(cat server_private.key)
    SERVER_PUBLIC_KEY=$(cat server_public.key)
    
    # Create server configuration
    cat > /etc/wireguard/wg0.conf << EOF
[Interface]
PrivateKey = $SERVER_PRIVATE_KEY
Address = 10.0.0.1/24
ListenPort = 51820
SaveConfig = true
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
EOF
    
    # Enable IP forwarding
    echo 'net.ipv4.ip_forward=1' > /etc/sysctl.d/99-wireguard.conf
    sysctl -p /etc/sysctl.d/99-wireguard.conf
    
    # Start WireGuard
    systemctl enable wg-quick@wg0
    systemctl start wg-quick@wg0
    
    log "✓ WireGuard server configured" "$GREEN"
    log "Server public key: $SERVER_PUBLIC_KEY" "$CYAN"
}

# Function to create WireGuard client
create_wireguard_client() {
    local client_name="$1"
    local client_ip="$2"
    
    log "Creating WireGuard client: $client_name" "$BLUE"
    
    # Generate client keys
    cd /etc/wireguard
    wg genkey | tee "${client_name}_private.key" | wg pubkey > "${client_name}_public.key"
    CLIENT_PRIVATE_KEY=$(cat "${client_name}_private.key")
    CLIENT_PUBLIC_KEY=$(cat "${client_name}_public.key")
    
    # Add client to server
    wg set wg0 peer "$CLIENT_PUBLIC_KEY" allowed-ips "$client_ip/32"
    
    # Create client configuration
    cat > "/etc/wireguard/${client_name}.conf" << EOF
[Interface]
PrivateKey = $CLIENT_PRIVATE_KEY
Address = $client_ip/24
DNS = 8.8.8.8, 8.8.4.4

[Peer]
PublicKey = $SERVER_PUBLIC_KEY
Endpoint = $SERVER_IP:51820
AllowedIPs = 10.0.0.0/24
PersistentKeepalive = 25
EOF
    
    # Generate QR code for mobile devices
    qrencode -t ansiutf8 < "/etc/wireguard/${client_name}.conf"
    
    log "✓ Client $client_name created" "$GREEN"
    log "Client config saved to: /etc/wireguard/${client_name}.conf" "$CYAN"
}

# Function to configure firewall
configure_firewall() {
    log "Configuring firewall..." "$BLUE"
    
    # Reset firewall
    ufw --force reset
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH
    ufw allow ssh
    
    # Allow WireGuard
    ufw allow 51820/udp
    
    # Allow application ports
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8000/tcp
    ufw allow 3000/tcp
    ufw allow 8554/tcp
    ufw allow 8888/tcp
    ufw allow 21/tcp
    ufw allow 30000:30009/tcp
    
    # Enable firewall
    ufw --force enable
    
    log "✓ Firewall configured" "$GREEN"
}

# Function to setup fail2ban
setup_fail2ban() {
    log "Setting up fail2ban..." "$BLUE"
    
    # Create fail2ban configuration
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3
EOF
    
    systemctl enable fail2ban
    systemctl start fail2ban
    
    log "✓ Fail2ban configured" "$GREEN"
}

# Function to deploy PFCAM application
deploy_pfcam() {
    log "Deploying PFCAM application..." "$BLUE"
    
    # Clone or update repository
    if [ ! -d "$PROJECT_DIR" ]; then
        log "Cloning PFCAM repository..." "$YELLOW"
        git clone https://github.com/your-repo/pfcam.git "$PROJECT_DIR"
    else
        log "Updating PFCAM repository..." "$YELLOW"
        cd "$PROJECT_DIR"
        git pull origin main
    fi
    
    cd "$PROJECT_DIR"
    
    # Create environment file
    cat > .env << EOF
# Server Configuration
SERVER_IP=$SERVER_IP
DOMAIN_NAME=$DOMAIN_NAME

# Database Configuration
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_DB=pfcam
POSTGRES_USER=pfcam

# Application Configuration
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
STORAGE_PATH=/app/storage

# FTP Configuration
FTP_PUBLIC_HOST=$SERVER_IP
FTP_USER_NAME=ftpuser
FTP_USER_PASS=$FTP_PASSWORD

# Frontend Configuration
VITE_API_BASE_URL=http://$SERVER_IP:8000
VITE_WS_URL=ws://$SERVER_IP:8000/ws

# Redis Configuration
REDIS_URL=redis://redis:6379

# Time Sync Configuration
TIME_SYNC_CHECK_INTERVAL=86400
TIME_SYNC_MAX_DRIFT=60
TIME_SYNC_CAMERA_DEFAULT_NTP=192.168.100.254

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF
    
    # Build and start application
    log "Building application containers..." "$YELLOW"
    docker compose build --no-cache
    
    log "Starting application..." "$YELLOW"
    docker compose up -d
    
    # Wait for services to be ready
    log "Waiting for services to be ready..." "$YELLOW"
    sleep 30
    
    # Check service status
    log "Checking service status..." "$BLUE"
    docker compose ps
    
    log "✓ PFCAM application deployed" "$GREEN"
}

# Function to setup monitoring
setup_monitoring() {
    log "Setting up monitoring..." "$BLUE"
    
    # Create monitoring script
    cat > /usr/local/bin/pfcam-monitor.sh << 'EOF'
#!/bin/bash

# PFCAM Monitoring Script
LOG_FILE="/var/log/pfcam-monitor.log"

echo "$(date): Starting PFCAM monitoring..." >> "$LOG_FILE"

# Check Docker services
cd /opt/pfcam
if ! docker compose ps | grep -q "Up"; then
    echo "$(date): Docker services down, restarting..." >> "$LOG_FILE"
    docker compose restart
fi

# Check WireGuard
if ! systemctl is-active --quiet wg-quick@wg0; then
    echo "$(date): WireGuard down, restarting..." >> "$LOG_FILE"
    systemctl restart wg-quick@wg0
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "$(date): Disk usage high: ${DISK_USAGE}%" >> "$LOG_FILE"
fi

# Check memory usage
MEM_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ "$MEM_USAGE" -gt 90 ]; then
    echo "$(date): Memory usage high: ${MEM_USAGE}%" >> "$LOG_FILE"
fi

echo "$(date): Monitoring complete" >> "$LOG_FILE"
EOF
    
    chmod +x /usr/local/bin/pfcam-monitor.sh
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/pfcam-monitor.sh") | crontab -
    
    log "✓ Monitoring configured" "$GREEN"
}

# Function to create deployment summary
create_summary() {
    log "Creating deployment summary..." "$BLUE"
    
    cat > /root/pfcam-deployment-summary.txt << EOF
PFCAM Hetzner Server Deployment Summary
=======================================

Deployment Date: $(date)
Server IP: $SERVER_IP
Domain: $DOMAIN_NAME

WireGuard Configuration:
- Server Public Key: $SERVER_PUBLIC_KEY
- VPN Subnet: 10.0.0.0/24
- VPN Port: 51820

Application Access:
- Web Interface: http://$SERVER_IP:3000
- API: http://$SERVER_IP:8000
- Health Check: http://$SERVER_IP:8000/health

Client Configurations:
- Camera Client: /etc/wireguard/camera001.conf
- Router Client: /etc/wireguard/router001.conf

Database Credentials:
- Database: pfcam
- User: pfcam
- Password: [See .env file]

FTP Credentials:
- User: ftpuser
- Password: $FTP_PASSWORD

Security:
- Firewall: UFW enabled
- Fail2ban: Active
- WireGuard: Active

Monitoring:
- Script: /usr/local/bin/pfcam-monitor.sh
- Logs: /var/log/pfcam-monitor.log
- Cron: Every 5 minutes

Next Steps:
1. Configure camera with WireGuard client
2. Configure router with WireGuard client
3. Test video streaming
4. Set up SSL certificates (optional)
5. Configure backup strategy

Support:
- Application logs: docker compose logs
- System logs: journalctl -u docker
- VPN logs: journalctl -u wg-quick@wg0
EOF
    
    log "✓ Deployment summary created: /root/pfcam-deployment-summary.txt" "$GREEN"
}

# Main deployment function
main() {
    log "==========================================" "$PURPLE"
    log "PFCAM Hetzner Server Automated Deployment" "$PURPLE"
    log "==========================================" "$PURPLE"
    log ""
    
    # Check if running as root
    check_root
    
    # Get server configuration
    log "Server Configuration" "$BLUE"
    log "===================" "$BLUE"
    
    SERVER_IP=$(get_input "Enter your server's public IP address" "true")
    DOMAIN_NAME=$(get_input "Enter your domain name (or press Enter to use IP only)" "false" "$SERVER_IP")
    
    # Generate secure passwords
    POSTGRES_PASSWORD=$(generate_password)
    SECRET_KEY=$(generate_password)
    FTP_PASSWORD=$(generate_password)
    
    log "Generated secure passwords:" "$CYAN"
    log "PostgreSQL: $POSTGRES_PASSWORD" "$CYAN"
    log "Secret Key: $SECRET_KEY" "$CYAN"
    log "FTP: $FTP_PASSWORD" "$CYAN"
    log ""
    
    # Confirm deployment
    log "Press Enter to start deployment..." "$YELLOW"
    read
    
    # Start deployment
    log "Starting deployment..." "$BLUE"
    
    update_system
    install_docker
    setup_wireguard
    configure_firewall
    setup_fail2ban
    deploy_pfcam
    setup_monitoring
    
    # Create clients
    create_wireguard_client "camera001" "10.0.0.10"
    create_wireguard_client "router001" "10.0.0.20"
    
    create_summary
    
    log "==========================================" "$GREEN"
    log "DEPLOYMENT COMPLETE!" "$GREEN"
    log "==========================================" "$GREEN"
    log ""
    log "Your PFCAM server is now ready!" "$GREEN"
    log ""
    log "Access your application at:" "$CYAN"
    log "  Web Interface: http://$SERVER_IP:3000" "$CYAN"
    log "  API: http://$SERVER_IP:8000" "$CYAN"
    log ""
    log "WireGuard clients created:" "$CYAN"
    log "  Camera: /etc/wireguard/camera001.conf" "$CYAN"
    log "  Router: /etc/wireguard/router001.conf" "$CYAN"
    log ""
    log "Deployment summary: /root/pfcam-deployment-summary.txt" "$CYAN"
    log ""
    log "Next steps:" "$YELLOW"
    log "1. Configure camera with WireGuard client" "$YELLOW"
    log "2. Configure router with WireGuard client" "$YELLOW"
    log "3. Test video streaming" "$YELLOW"
    log "4. Set up SSL certificates (optional)" "$YELLOW"
    log ""
}

# Run main function
main "$@" 