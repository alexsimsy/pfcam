#!/bin/bash

# PFCAM Client Setup Script
# This script helps configure WireGuard clients on cameras and routers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to log messages
log() {
    echo -e "${2:-$GREEN}$1${NC}"
}

# Function to show usage
show_usage() {
    cat << EOF
PFCAM Client Setup Script

Usage: $0 [OPTIONS] COMMAND

Commands:
  camera    - Configure camera with WireGuard client
  router    - Configure router with WireGuard client
  generate  - Generate WireGuard client configuration
  test      - Test VPN connectivity

Options:
  -s, --server-ip IP     Server IP address
  -k, --server-key KEY   Server public key
  -c, --client-name NAME Client name (default: camera001)
  -i, --client-ip IP     Client IP address (default: 10.0.0.10)
  -h, --help            Show this help message

Examples:
  $0 camera -s 1.2.3.4 -k SERVER_PUBLIC_KEY
  $0 router -s 1.2.3.4 -k SERVER_PUBLIC_KEY -c router001 -i 10.0.0.20
  $0 generate -s 1.2.3.4 -k SERVER_PUBLIC_KEY -c camera002 -i 10.0.0.11
EOF
}

# Function to generate WireGuard client configuration
generate_client_config() {
    local server_ip="$1"
    local server_public_key="$2"
    local client_name="$3"
    local client_ip="$4"
    
    log "Generating WireGuard client configuration..." "$BLUE"
    
    # Generate client keys
    local client_private_key=$(wg genkey)
    local client_public_key=$(echo "$client_private_key" | wg pubkey)
    
    # Create client configuration
    cat > "${client_name}.conf" << EOF
[Interface]
PrivateKey = $client_private_key
Address = $client_ip/24
DNS = 8.8.8.8, 8.8.4.4

[Peer]
PublicKey = $server_public_key
Endpoint = $server_ip:51820
AllowedIPs = 10.0.0.0/24
PersistentKeepalive = 25
EOF
    
    # Generate QR code
    if command -v qrencode >/dev/null 2>&1; then
        log "Generating QR code..." "$YELLOW"
        qrencode -t ansiutf8 < "${client_name}.conf"
    fi
    
    log "✓ Client configuration generated: ${client_name}.conf" "$GREEN"
    log "Client public key: $client_public_key" "$CYAN"
    
    # Return client public key for server configuration
    echo "$client_public_key"
}

# Function to configure camera
configure_camera() {
    local server_ip="$1"
    local server_public_key="$2"
    local client_name="${3:-camera001}"
    local client_ip="${4:-10.0.0.10}"
    
    log "Configuring camera with WireGuard..." "$BLUE"
    
    # Generate client configuration
    local client_public_key=$(generate_client_config "$server_ip" "$server_public_key" "$client_name" "$client_ip")
    
    log "Camera configuration steps:" "$YELLOW"
    log "1. Copy ${client_name}.conf to camera" "$YELLOW"
    log "2. Install WireGuard on camera (if not already installed)" "$YELLOW"
    log "3. Import configuration file" "$YELLOW"
    log "4. Start WireGuard connection" "$YELLOW"
    log "5. Configure camera network settings:" "$YELLOW"
    log "   - Set static IP: $client_ip" "$YELLOW"
    log "   - Set gateway: 10.0.0.1" "$YELLOW"
    log "   - Set DNS: 8.8.8.8, 8.8.4.4" "$YELLOW"
    log ""
    log "6. Configure camera server settings:" "$YELLOW"
    log "   - Set server IP: 10.0.0.1" "$YELLOW"
    log "   - Configure API endpoints" "$YELLOW"
    log "   - Set up video streaming" "$YELLOW"
    log ""
    log "Server configuration needed:" "$CYAN"
    log "Add this peer to server WireGuard configuration:" "$CYAN"
    log "wg set wg0 peer $client_public_key allowed-ips $client_ip/32" "$CYAN"
}

# Function to configure router
configure_router() {
    local server_ip="$1"
    local server_public_key="$2"
    local client_name="${3:-router001}"
    local client_ip="${4:-10.0.0.20}"
    
    log "Configuring router with WireGuard..." "$BLUE"
    
    # Generate client configuration
    local client_public_key=$(generate_client_config "$server_ip" "$server_public_key" "$client_name" "$client_ip")
    
    log "Router configuration steps:" "$YELLOW"
    log "1. Copy ${client_name}.conf to router" "$YELLOW"
    log "2. Install WireGuard on router (if not already installed)" "$YELLOW"
    log "3. Import configuration file" "$YELLOW"
    log "4. Configure router routing:" "$YELLOW"
    log "   - Route camera traffic through VPN" "$YELLOW"
    log "   - Set up NAT for camera network" "$YELLOW"
    log "5. Start WireGuard connection" "$YELLOW"
    log ""
    log "Server configuration needed:" "$CYAN"
    log "Add this peer to server WireGuard configuration:" "$CYAN"
    log "wg set wg0 peer $client_public_key allowed-ips $client_ip/32" "$CYAN"
}

# Function to test VPN connectivity
test_connectivity() {
    local server_ip="$1"
    
    log "Testing VPN connectivity..." "$BLUE"
    
    # Test basic connectivity
    log "Testing ping to server..." "$YELLOW"
    if ping -c 3 "$server_ip" >/dev/null 2>&1; then
        log "✓ Ping successful" "$GREEN"
    else
        log "✗ Ping failed" "$RED"
    fi
    
    # Test application connectivity
    log "Testing application connectivity..." "$YELLOW"
    if curl -s "http://$server_ip:8000/health" >/dev/null 2>&1; then
        log "✓ Application health check successful" "$GREEN"
    else
        log "✗ Application health check failed" "$RED"
    fi
    
    # Test web interface
    log "Testing web interface..." "$YELLOW"
    if curl -s "http://$server_ip:3000" >/dev/null 2>&1; then
        log "✓ Web interface accessible" "$GREEN"
    else
        log "✗ Web interface not accessible" "$RED"
    fi
}

# Function to create installation script for camera
create_camera_install_script() {
    local client_name="$1"
    
    cat > "install-camera-${client_name}.sh" << 'EOF'
#!/bin/bash

# Camera WireGuard Installation Script
# This script installs and configures WireGuard on a camera device

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${2:-$GREEN}$1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log "Please run this script as root (use sudo)" "$RED"
    exit 1
fi

# Install WireGuard
log "Installing WireGuard..." "$BLUE"
apt update
apt install -y wireguard wireguard-tools

# Copy configuration file
log "Copying WireGuard configuration..." "$BLUE"
cp CAMERA_CONFIG_FILE /etc/wireguard/wg0.conf
chmod 600 /etc/wireguard/wg0.conf

# Enable and start WireGuard
log "Starting WireGuard..." "$BLUE"
systemctl enable wg-quick@wg0
systemctl start wg-quick@wg0

# Check status
log "Checking WireGuard status..." "$BLUE"
systemctl status wg-quick@wg0 --no-pager

log "✓ WireGuard installed and configured" "$GREEN"
log "Camera should now be connected to VPN" "$GREEN"
EOF
    
    # Replace placeholder with actual config file
    sed -i "s/CAMERA_CONFIG_FILE/${client_name}.conf/g" "install-camera-${client_name}.sh"
    chmod +x "install-camera-${client_name}.sh"
    
    log "✓ Camera installation script created: install-camera-${client_name}.sh" "$GREEN"
}

# Function to create installation script for router
create_router_install_script() {
    local client_name="$1"
    
    cat > "install-router-${client_name}.sh" << 'EOF'
#!/bin/bash

# Router WireGuard Installation Script
# This script installs and configures WireGuard on a router device

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${2:-$GREEN}$1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log "Please run this script as root (use sudo)" "$RED"
    exit 1
fi

# Install WireGuard
log "Installing WireGuard..." "$BLUE"
apt update
apt install -y wireguard wireguard-tools

# Copy configuration file
log "Copying WireGuard configuration..." "$BLUE"
cp ROUTER_CONFIG_FILE /etc/wireguard/wg0.conf
chmod 600 /etc/wireguard/wg0.conf

# Enable IP forwarding
log "Enabling IP forwarding..." "$BLUE"
echo 'net.ipv4.ip_forward=1' > /etc/sysctl.d/99-wireguard.conf
sysctl -p /etc/sysctl.d/99-wireguard.conf

# Configure iptables for routing
log "Configuring routing..." "$BLUE"
iptables -A FORWARD -i wg0 -j ACCEPT
iptables -A FORWARD -o wg0 -j ACCEPT
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Save iptables rules
iptables-save > /etc/iptables/rules.v4

# Enable and start WireGuard
log "Starting WireGuard..." "$BLUE"
systemctl enable wg-quick@wg0
systemctl start wg-quick@wg0

# Check status
log "Checking WireGuard status..." "$BLUE"
systemctl status wg-quick@wg0 --no-pager

log "✓ WireGuard installed and configured" "$GREEN"
log "Router should now be connected to VPN" "$GREEN"
EOF
    
    # Replace placeholder with actual config file
    sed -i "s/ROUTER_CONFIG_FILE/${client_name}.conf/g" "install-router-${client_name}.sh"
    chmod +x "install-router-${client_name}.sh"
    
    log "✓ Router installation script created: install-router-${client_name}.sh" "$GREEN"
}

# Main function
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -s|--server-ip)
                SERVER_IP="$2"
                shift 2
                ;;
            -k|--server-key)
                SERVER_PUBLIC_KEY="$2"
                shift 2
                ;;
            -c|--client-name)
                CLIENT_NAME="$2"
                shift 2
                ;;
            -i|--client-ip)
                CLIENT_IP="$2"
                shift 2
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            camera|router|generate|test)
                COMMAND="$1"
                shift
                ;;
            *)
                log "Unknown option: $1" "$RED"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Validate required parameters
    if [ -z "$COMMAND" ]; then
        log "Error: Command is required" "$RED"
        show_usage
        exit 1
    fi
    
    if [ "$COMMAND" != "test" ] && [ -z "$SERVER_IP" ]; then
        log "Error: Server IP is required" "$RED"
        show_usage
        exit 1
    fi
    
    if [ "$COMMAND" != "test" ] && [ -z "$SERVER_PUBLIC_KEY" ]; then
        log "Error: Server public key is required" "$RED"
        show_usage
        exit 1
    fi
    
    # Execute command
    case "$COMMAND" in
        camera)
            configure_camera "$SERVER_IP" "$SERVER_PUBLIC_KEY" "$CLIENT_NAME" "$CLIENT_IP"
            create_camera_install_script "${CLIENT_NAME:-camera001}"
            ;;
        router)
            configure_router "$SERVER_IP" "$SERVER_PUBLIC_KEY" "$CLIENT_NAME" "$CLIENT_IP"
            create_router_install_script "${CLIENT_NAME:-router001}"
            ;;
        generate)
            generate_client_config "$SERVER_IP" "$SERVER_PUBLIC_KEY" "${CLIENT_NAME:-camera001}" "${CLIENT_IP:-10.0.0.10}"
            ;;
        test)
            test_connectivity "$SERVER_IP"
            ;;
        *)
            log "Unknown command: $COMMAND" "$RED"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 