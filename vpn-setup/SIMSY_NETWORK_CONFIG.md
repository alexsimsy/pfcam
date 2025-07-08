# SIMSY Network Configuration Guide

## Overview
This guide provides the specific network configuration details needed to integrate your VPN server with the SIMSY mobile network infrastructure.

## Network Architecture
```
Camera → Router with SIM → SIMSY Network → VPN → Ubuntu Server → PFCAM Application
```

## Required Network Configuration

### 1. VPN Server Details
After running the installation script, you'll have these details:

**Server Information:**
- **Public IP**: `YOUR_SERVER_IP` (provided during installation)
- **VPN Protocol**: UDP
- **VPN Port**: 1194
- **VPN Subnet**: 10.8.0.0/24
- **VPN Server Interface**: 10.8.0.1

**Application Ports:**
- **Backend API**: `YOUR_SERVER_IP:8000`
- **Frontend Web**: `YOUR_SERVER_IP:3000`
- **RTSP Streaming**: `YOUR_SERVER_IP:8554`
- **HLS Streaming**: `YOUR_SERVER_IP:8888`
- **FTP Service**: `YOUR_SERVER_IP:21`

### 2. SIMSY Network Configuration

#### 2.1 APN Configuration
Configure SIM cards to use the SIMSY network APN:
```
APN: simsy.network
Username: [as provided by SIMSY]
Password: [as provided by SIMSY]
Authentication: PAP/CHAP
```

#### 2.2 Routing Configuration
Set up routing in the SIMSY network to direct traffic to your VPN server:

**Primary Route:**
```
Destination: YOUR_SERVER_IP/32
Gateway: [SIMSY network gateway]
Interface: [SIMSY network interface]
Protocol: UDP
Port: 1194
```

**VPN Client Subnet Route:**
```
Destination: 10.8.0.0/24
Gateway: YOUR_SERVER_IP
Interface: [SIMSY network interface]
```

#### 2.3 QoS Configuration
Configure Quality of Service for camera traffic:

**High Priority Traffic:**
- **RTSP Video Streams**: Port 8554
- **HLS Video Streams**: Port 8888
- **VPN Control Traffic**: Port 1194

**Medium Priority Traffic:**
- **API Communication**: Port 8000
- **Web Interface**: Port 3000

**Low Priority Traffic:**
- **FTP File Transfer**: Port 21
- **General Internet**: All other traffic

### 3. SIM Card Group Configuration

#### 3.1 Dedicated IP Subnet
Allocate a dedicated IP subnet for VPN clients:
```
Subnet: 192.168.100.0/24 (or as allocated by SIMSY)
Gateway: 192.168.100.1
DNS: 8.8.8.8, 8.8.4.4
```

#### 3.2 SIM Card Assignment
Assign SIM cards to the VPN group:
```
Group Name: PFCAM-VPN-Group
SIM Cards: [List of assigned SIM card numbers]
Subnet: 192.168.100.0/24
QoS Profile: Camera-High-Priority
```

### 4. Network Security Configuration

#### 4.1 Firewall Rules
Configure SIMSY network firewall to allow:
```
Inbound Rules:
- UDP 1194 from ANY to YOUR_SERVER_IP (VPN)
- TCP 8000 from 10.8.0.0/24 to YOUR_SERVER_IP (API)
- TCP 3000 from 10.8.0.0/24 to YOUR_SERVER_IP (Web)
- TCP 8554 from 10.8.0.0/24 to YOUR_SERVER_IP (RTSP)
- TCP 8888 from 10.8.0.0/24 to YOUR_SERVER_IP (HLS)
- TCP 21 from 10.8.0.0/24 to YOUR_SERVER_IP (FTP)

Outbound Rules:
- Allow all traffic from VPN subnet (10.8.0.0/24)
- Allow DNS queries (UDP 53)
- Allow NTP synchronization (UDP 123)
```

#### 4.2 Access Control Lists
Configure ACLs for SIM card groups:
```
ACL Name: PFCAM-Camera-Access
Description: Access control for PFCAM camera traffic
Rules:
- Permit UDP 1194 to YOUR_SERVER_IP (VPN)
- Permit TCP 8000 to YOUR_SERVER_IP (API)
- Permit TCP 8554 to YOUR_SERVER_IP (RTSP)
- Permit TCP 8888 to YOUR_SERVER_IP (HLS)
- Permit TCP 21 to YOUR_SERVER_IP (FTP)
- Deny all other traffic
```

### 5. Monitoring and Logging

#### 5.1 Network Monitoring
Configure monitoring for:
- **VPN Connection Status**: Monitor UDP 1194 traffic
- **Camera Connectivity**: Monitor connections from 10.8.0.0/24
- **Bandwidth Usage**: Track data usage per SIM card
- **QoS Performance**: Monitor latency and packet loss

#### 5.2 Alert Configuration
Set up alerts for:
- **VPN Connection Failures**: When UDP 1194 traffic stops
- **High Bandwidth Usage**: When data usage exceeds thresholds
- **Network Latency**: When latency exceeds acceptable levels
- **SIM Card Offline**: When SIM cards lose connectivity

### 6. Configuration Checklist

#### 6.1 Pre-Deployment Checklist
- [ ] VPN server installed and configured
- [ ] Server IP address confirmed and accessible
- [ ] SIM cards allocated to VPN group
- [ ] APN configured on all SIM cards
- [ ] Routing rules configured in SIMSY network
- [ ] QoS policies applied
- [ ] Firewall rules configured
- [ ] Monitoring and alerts set up

#### 6.2 Post-Deployment Checklist
- [ ] VPN connections established from cameras
- [ ] Application accessible via VPN
- [ ] Video streaming working
- [ ] Event recording functional
- [ ] FTP file transfer working
- [ ] Monitoring showing normal traffic patterns
- [ ] Alerts configured and tested

### 7. Troubleshooting Guide

#### 7.1 VPN Connection Issues
**Symptoms**: Cameras cannot connect to VPN
**Diagnosis Steps**:
1. Check SIM card connectivity to SIMSY network
2. Verify APN configuration
3. Test routing to VPN server
4. Check firewall rules
5. Verify VPN server status

**Solutions**:
- Ensure SIM cards are in correct group
- Verify APN settings
- Check routing table in SIMSY network
- Review firewall configuration
- Restart VPN service if needed

#### 7.2 Application Access Issues
**Symptoms**: VPN connected but application not accessible
**Diagnosis Steps**:
1. Test connectivity to application ports
2. Check application service status
3. Verify firewall rules for application ports
4. Check application logs

**Solutions**:
- Ensure application services are running
- Verify firewall allows traffic to application ports
- Check application configuration
- Review application logs for errors

#### 7.3 Performance Issues
**Symptoms**: Slow video streaming or high latency
**Diagnosis Steps**:
1. Check bandwidth usage
2. Monitor QoS performance
3. Test network latency
4. Review server resource usage

**Solutions**:
- Adjust QoS policies
- Optimize video quality settings
- Scale server resources if needed
- Review network routing

### 8. Contact Information

For SIMSY network configuration assistance:

**SIMSY Network Administrator:**
- Email: [admin@simsy.network]
- Phone: [Contact Number]
- Support Hours: [Business Hours]

**Emergency Contact:**
- Phone: [Emergency Number]
- Available: 24/7 for critical issues

**Technical Support:**
- Email: [support@simsy.network]
- Phone: [Support Number]
- Support Hours: [Business Hours]

### 9. Network Information Template

Use this template to provide network configuration details:

```
SIMSY Network Configuration Request
==================================

Customer: [Customer Name]
Project: PFCAM Camera System
Date: [Date]

Server Information:
- Public IP: [YOUR_SERVER_IP]
- VPN Port: 1194 (UDP)
- VPN Subnet: 10.8.0.0/24

Required Configuration:
1. APN: simsy.network
2. SIM Card Group: PFCAM-VPN-Group
3. Dedicated Subnet: [Allocated by SIMSY]
4. QoS Profile: Camera-High-Priority
5. Routing: Direct to [YOUR_SERVER_IP]

Application Ports:
- Backend API: [YOUR_SERVER_IP]:8000
- Frontend: [YOUR_SERVER_IP]:3000
- RTSP: [YOUR_SERVER_IP]:8554
- HLS: [YOUR_SERVER_IP]:8888
- FTP: [YOUR_SERVER_IP]:21

Expected Traffic:
- Number of cameras: [X]
- Estimated bandwidth per camera: [Y] Mbps
- Total expected bandwidth: [Z] Mbps

Contact Information:
- Technical Contact: [Name]
- Phone: [Number]
- Email: [Email]
```

This configuration ensures secure, reliable communication between your cameras and the PFCAM application through the SIMSY network infrastructure. 