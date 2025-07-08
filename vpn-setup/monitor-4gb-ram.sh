#!/bin/bash

# Memory Monitoring Script for 4GB RAM PFCAM Server
# This script monitors memory usage and provides alerts for low memory conditions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MEMORY_THRESHOLD_WARNING=80  # Percentage
MEMORY_THRESHOLD_CRITICAL=90 # Percentage
SWAP_THRESHOLD_WARNING=50    # Percentage
CHECK_INTERVAL=30            # Seconds

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}PFCAM 4GB RAM Memory Monitor${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# Function to get memory usage
get_memory_usage() {
    # Get total and used memory
    TOTAL_MEM=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    USED_MEM=$(free -m | awk 'NR==2{printf "%.0f", $3}')
    FREE_MEM=$(free -m | awk 'NR==2{printf "%.0f", $4}')
    AVAILABLE_MEM=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    
    # Calculate percentages
    MEMORY_USAGE_PERCENT=$((USED_MEM * 100 / TOTAL_MEM))
    
    # Get swap usage
    TOTAL_SWAP=$(free -m | awk 'NR==3{printf "%.0f", $2}')
    USED_SWAP=$(free -m | awk 'NR==3{printf "%.0f", $3}')
    SWAP_USAGE_PERCENT=$((USED_SWAP * 100 / TOTAL_SWAP))
}

# Function to get Docker memory usage
get_docker_memory() {
    echo -e "${YELLOW}Docker Container Memory Usage:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | head -10
    echo ""
}

# Function to get top memory processes
get_top_processes() {
    echo -e "${YELLOW}Top Memory Processes:${NC}"
    ps aux --sort=-%mem | head -6
    echo ""
}

# Function to check memory status
check_memory_status() {
    get_memory_usage
    
    echo -e "${BLUE}Memory Status - $(date)${NC}"
    echo "=================================="
    echo -e "Total Memory: ${GREEN}${TOTAL_MEM}MB${NC}"
    echo -e "Used Memory: ${YELLOW}${USED_MEM}MB${NC}"
    echo -e "Available Memory: ${GREEN}${AVAILABLE_MEM}MB${NC}"
    echo -e "Memory Usage: ${YELLOW}${MEMORY_USAGE_PERCENT}%${NC}"
    echo -e "Swap Usage: ${YELLOW}${SWAP_USAGE_PERCENT}%${NC}"
    echo ""
    
    # Check memory thresholds
    if [ $MEMORY_USAGE_PERCENT -ge $MEMORY_THRESHOLD_CRITICAL ]; then
        echo -e "${RED}⚠️  CRITICAL: Memory usage is ${MEMORY_USAGE_PERCENT}%${NC}"
        echo -e "${RED}   Immediate action required!${NC}"
        echo ""
        echo "Emergency actions:"
        echo "1. Clear Docker cache: docker system prune -f"
        echo "2. Restart services: docker-compose restart"
        echo "3. Clear system cache: sudo sync && sudo echo 3 | sudo tee /proc/sys/vm/drop_caches"
        echo ""
    elif [ $MEMORY_USAGE_PERCENT -ge $MEMORY_THRESHOLD_WARNING ]; then
        echo -e "${YELLOW}⚠️  WARNING: Memory usage is ${MEMORY_USAGE_PERCENT}%${NC}"
        echo -e "${YELLOW}   Consider optimizing or upgrading RAM${NC}"
        echo ""
    else
        echo -e "${GREEN}✅ Memory usage is normal (${MEMORY_USAGE_PERCENT}%)${NC}"
        echo ""
    fi
    
    # Check swap usage
    if [ $SWAP_USAGE_PERCENT -ge $SWAP_THRESHOLD_WARNING ]; then
        echo -e "${YELLOW}⚠️  WARNING: High swap usage (${SWAP_USAGE_PERCENT}%)${NC}"
        echo -e "${YELLOW}   System performance may be degraded${NC}"
        echo ""
    fi
}

# Function to show memory breakdown
show_memory_breakdown() {
    echo -e "${BLUE}Memory Breakdown:${NC}"
    echo "=================="
    
    # System memory
    SYSTEM_MEM=$(ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%mem | head -1 | awk '{print $4}')
    echo -e "System Processes: ${YELLOW}~${SYSTEM_MEM}%${NC}"
    
    # Docker memory
    DOCKER_MEM=$(docker stats --no-stream --format "{{.MemPerc}}" | sed 's/%//g' | awk '{sum+=$1} END {print sum}')
    echo -e "Docker Containers: ${YELLOW}~${DOCKER_MEM}%${NC}"
    
    # Available memory
    AVAILABLE_PERCENT=$((AVAILABLE_MEM * 100 / TOTAL_MEM))
    echo -e "Available Memory: ${GREEN}${AVAILABLE_PERCENT}%${NC}"
    echo ""
}

# Function to show optimization recommendations
show_recommendations() {
    echo -e "${BLUE}Optimization Recommendations:${NC}"
    echo "================================"
    
    if [ $MEMORY_USAGE_PERCENT -ge 80 ]; then
        echo -e "${RED}High Memory Usage Detected:${NC}"
        echo "1. Reduce number of concurrent cameras (max 2-4)"
        echo "2. Lower video quality settings"
        echo "3. Enable video compression (H.264/H.265)"
        echo "4. Consider upgrading to 8GB RAM"
        echo "5. Restart services to free memory"
        echo ""
    fi
    
    if [ $SWAP_USAGE_PERCENT -ge 50 ]; then
        echo -e "${YELLOW}High Swap Usage Detected:${NC}"
        echo "1. Increase swap file size"
        echo "2. Optimize PostgreSQL settings"
        echo "3. Reduce Redis memory limits"
        echo "4. Monitor for memory leaks"
        echo ""
    fi
    
    echo -e "${GREEN}General Recommendations:${NC}"
    echo "1. Monitor memory usage regularly"
    echo "2. Set up automated alerts"
    echo "3. Keep system updated"
    echo "4. Use memory-optimized Docker Compose"
    echo "5. Consider SSD for better performance"
    echo ""
}

# Function to perform emergency cleanup
emergency_cleanup() {
    echo -e "${RED}Performing Emergency Memory Cleanup...${NC}"
    echo "============================================="
    
    # Clear Docker cache
    echo "Clearing Docker cache..."
    docker system prune -f
    
    # Clear system cache
    echo "Clearing system cache..."
    sudo sync && sudo echo 3 | sudo tee /proc/sys/vm/drop_caches
    
    # Restart services
    echo "Restarting services..."
    docker-compose -f docker-compose.4gb-ram.yml restart
    
    echo -e "${GREEN}Cleanup completed!${NC}"
    echo ""
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -c, --continuous    Monitor continuously (default)"
    echo "  -s, --single        Single memory check"
    echo "  -e, --emergency     Perform emergency cleanup"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                  # Monitor continuously"
    echo "  $0 -s               # Single check"
    echo "  $0 -e               # Emergency cleanup"
    echo ""
}

# Main monitoring loop
monitor_continuously() {
    echo -e "${GREEN}Starting continuous memory monitoring...${NC}"
    echo -e "${GREEN}Press Ctrl+C to stop${NC}"
    echo ""
    
    while true; do
        clear
        check_memory_status
        show_memory_breakdown
        get_docker_memory
        get_top_processes
        show_recommendations
        
        echo -e "${BLUE}Next check in ${CHECK_INTERVAL} seconds...${NC}"
        sleep $CHECK_INTERVAL
    done
}

# Single check mode
single_check() {
    check_memory_status
    show_memory_breakdown
    get_docker_memory
    get_top_processes
    show_recommendations
}

# Parse command line arguments
case "${1:-}" in
    -s|--single)
        single_check
        ;;
    -e|--emergency)
        emergency_cleanup
        ;;
    -h|--help)
        show_help
        ;;
    -c|--continuous|"")
        monitor_continuously
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        show_help
        exit 1
        ;;
esac 