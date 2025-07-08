#!/bin/bash

# VPN and Application Test Script for SIMSY Network
# This script tests VPN connectivity and application functionality

set -e

echo "=========================================="
echo "SIMSY Network VPN and Application Test"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test functions
test_vpn_service() {
    echo -e "${YELLOW}Testing VPN Service...${NC}"
    
    if systemctl is-active --quiet openvpn@openvpn; then
        echo -e "${GREEN}✓ VPN service is running${NC}"
    else
        echo -e "${RED}✗ VPN service is not running${NC}"
        return 1
    fi
    
    if ip link show tun0 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ VPN interface (tun0) is active${NC}"
        ip addr show tun0 | grep inet
    else
        echo -e "${RED}✗ VPN interface (tun0) is not active${NC}"
        return 1
    fi
}

test_vpn_connectivity() {
    echo -e "${YELLOW}Testing VPN Connectivity...${NC}"
    
    # Check if VPN subnet is accessible
    if ping -c 1 -W 5 10.8.0.1 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ VPN server (10.8.0.1) is reachable${NC}"
    else
        echo -e "${RED}✗ VPN server (10.8.0.1) is not reachable${NC}"
        return 1
    fi
    
    # Check VPN status log
    if [ -f /var/log/openvpn/openvpn-status.log ]; then
        echo -e "${GREEN}✓ VPN status log exists${NC}"
        echo "Connected clients:"
        grep -E "^OpenVPN CLIENT LIST|^Common Name" /var/log/openvpn/openvpn-status.log || echo "No clients connected"
    else
        echo -e "${YELLOW}⚠ VPN status log not found${NC}"
    fi
}

test_application_services() {
    echo -e "${YELLOW}Testing Application Services...${NC}"
    
    # Test backend API
    if curl -s -f http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend API is responding${NC}"
    else
        echo -e "${RED}✗ Backend API is not responding${NC}"
        return 1
    fi
    
    # Test frontend
    if curl -s -f http://localhost:3000 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is responding${NC}"
    else
        echo -e "${RED}✗ Frontend is not responding${NC}"
        return 1
    fi
    
    # Test database
    if docker-compose -f docker-compose.production.yml exec -T postgres pg_isready -U pfcam >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Database is accessible${NC}"
    else
        echo -e "${RED}✗ Database is not accessible${NC}"
        return 1
    fi
}

test_network_routing() {
    echo -e "${YELLOW}Testing Network Routing...${NC}"
    
    # Check if VPN routes exist
    if ip route show | grep -q "10.8.0.0/24"; then
        echo -e "${GREEN}✓ VPN routes are configured${NC}"
        ip route show | grep "10.8.0.0/24"
    else
        echo -e "${RED}✗ VPN routes are not configured${NC}"
        return 1
    fi
    
    # Check IP forwarding
    if [ "$(cat /proc/sys/net/ipv4/ip_forward)" = "1" ]; then
        echo -e "${GREEN}✓ IP forwarding is enabled${NC}"
    else
        echo -e "${RED}✗ IP forwarding is not enabled${NC}"
        return 1
    fi
}

test_firewall_rules() {
    echo -e "${YELLOW}Testing Firewall Rules...${NC}"
    
    # Check if UFW is active
    if ufw status | grep -q "Status: active"; then
        echo -e "${GREEN}✓ UFW firewall is active${NC}"
        
        # Check VPN port
        if ufw status | grep -q "1194/udp"; then
            echo -e "${GREEN}✓ VPN port 1194/udp is allowed${NC}"
        else
            echo -e "${RED}✗ VPN port 1194/udp is not allowed${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠ UFW firewall is not active${NC}"
    fi
}

test_camera_connectivity() {
    echo -e "${YELLOW}Testing Camera Connectivity...${NC}"
    
    # Check if any cameras are connected via VPN
    if [ -f /var/log/openvpn/openvpn-status.log ]; then
        CONNECTED_CAMERAS=$(grep -c "^[0-9]" /var/log/openvpn/openvpn-status.log || echo "0")
        if [ "$CONNECTED_CAMERAS" -gt 0 ]; then
            echo -e "${GREEN}✓ $CONNECTED_CAMERAS camera(s) connected via VPN${NC}"
            
            # List connected cameras
            echo "Connected cameras:"
            grep "^[0-9]" /var/log/openvpn/openvpn-status.log | while read line; do
                CLIENT_IP=$(echo $line | awk '{print $1}')
                CLIENT_NAME=$(echo $line | awk '{print $2}')
                echo "  - $CLIENT_NAME ($CLIENT_IP)"
            done
        else
            echo -e "${YELLOW}⚠ No cameras currently connected via VPN${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Cannot check camera connectivity - no status log${NC}"
    fi
}

test_simsy_network() {
    echo -e "${YELLOW}Testing SIMSY Network Connectivity...${NC}"
    
    # Test basic internet connectivity
    if ping -c 1 -W 5 8.8.8.8 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Internet connectivity is working${NC}"
    else
        echo -e "${RED}✗ Internet connectivity is not working${NC}"
        return 1
    fi
    
    # Test DNS resolution
    if nslookup google.com >/dev/null 2>&1; then
        echo -e "${GREEN}✓ DNS resolution is working${NC}"
    else
        echo -e "${RED}✗ DNS resolution is not working${NC}"
        return 1
    fi
}

# Main test execution
main() {
    echo "Starting comprehensive system test..."
    echo ""
    
    TESTS_PASSED=0
    TESTS_FAILED=0
    
    # Run all tests
    test_vpn_service && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    echo ""
    
    test_vpn_connectivity && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    echo ""
    
    test_application_services && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    echo ""
    
    test_network_routing && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    echo ""
    
    test_firewall_rules && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    echo ""
    
    test_camera_connectivity && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    echo ""
    
    test_simsy_network && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    echo ""
    
    # Summary
    echo "=========================================="
    echo "Test Summary"
    echo "=========================================="
    echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed! System is ready for production.${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Configure cameras to connect via VPN"
        echo "2. Test video streaming functionality"
        echo "3. Verify event recording and storage"
        echo "4. Set up monitoring and alerts"
    else
        echo -e "${RED}❌ Some tests failed. Please review the issues above.${NC}"
        echo ""
        echo "Troubleshooting steps:"
        echo "1. Check VPN service status: sudo systemctl status openvpn@openvpn"
        echo "2. Review VPN logs: sudo tail -f /var/log/openvpn/openvpn.log"
        echo "3. Check application logs: docker-compose -f docker-compose.production.yml logs"
        echo "4. Verify firewall rules: sudo ufw status"
        echo "5. Test network connectivity: ping 10.8.0.1"
    fi
}

# Run main function
main 