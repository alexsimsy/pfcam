# PFCAM - Industrial Event Camera Management System

## Quickstart (Development)

**Requirements:**
- Docker & Docker Compose
- (Optional) Node.js & Python 3.11+ for local dev

**To start everything for development:**
```sh
git clone <repo-url>
cd pfcam
cp frontend/.env.example frontend/.env   # or create .env as below
docker-compose up --build
```

**Frontend .env example:**
```
VITE_API_URL=http://backend:8000
VITE_WS_URL=ws://backend:8000/ws
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- Nginx (if enabled): [http://localhost](http://localhost)

---

## Architecture Overview

- **nginx** (optional, for production): Reverse proxy for frontend and backend
- **frontend**: React + Vite app (Dockerized, uses VITE_API_URL to talk to backend)
- **backend**: FastAPI app (Dockerized, serves API and websocket)
- **postgres**: Database
- **redis**: For caching, background jobs, etc.

**Docker Compose handles all networking.**  
- Internal service names: `backend`, `frontend`, `postgres`, `redis`
- Nginx proxies `/api/` to backend, all else to frontend

---

## Production Deployment

**Requirements:**
- Linux server (Ubuntu 22.04+ recommended)
- Docker & Docker Compose
- Domain name (optional, for SSL)
- (Optional) WireGuard for secure camera access

**Steps:**
1. Clone repo and set up `.env` files as above.
2. Edit `docker-compose.yml` for production (set strong secrets, configure volumes for persistent storage).
3. (Optional) Set up SSL certificates and update `nginx/nginx.conf` for HTTPS.
4. Run:
   ```sh
   docker-compose up --build -d
   ```
5. Point your domain to the server's IP.

**Default admin login:**  
- Email: `admin@s-imsy.com`  
- Password: `admin123`  
(You should change this after first login.)

---

## Troubleshooting

- If the frontend cannot reach the backend, check that `VITE_API_URL` in `.env` is set to `http://backend:8000` (for Docker Compose).
- If nginx fails to start, ensure `nginx/nginx.conf` is a file, not a directory, and uses the correct structure (see above).
- For local dev without Docker, set `VITE_API_URL=http://localhost:8000` in `.env`.

---

## Overview

PFCAM is a comprehensive management application for industrial event cameras designed to capture images and videos of key events. The system operates with triggers (digital signals or API triggers) and is designed for remote deployment using the SIMSY network for secure, isolated access.

## Architecture

### Network Architecture
- **Camera**: Industrial event camera with web GUI and REST API
- **Connectivity**: Cellular routers connecting to SIMSY network
- **Server**: AWS Lightsail instance per customer for security isolation
- **Network**: WireGuard VPN connection to SIMSY mobile network
- **Access**: IP-based camera access through secure tunnel

### Camera API Endpoints
The camera provides a comprehensive REST API with the following key endpoints:

#### Events Management
- `GET /events` - List all events with filtering and sorting
- `DELETE /events` - Delete all events
- `GET /events/{fileName}` - Download specific event file
- `DELETE /events/{fileName}` - Delete specific event
- `GET /events/active` - List active events
- `DELETE /events/active` - Stop all active events
- `GET /sse/recordings` - Server-sent events for real-time notifications

#### System Management
- `GET /system` - System information
- `GET /system/settings` - Current settings
- `PUT /system/settings` - Update settings
- `DELETE /system/settings` - Reset to defaults
- `GET /system/storage` - Storage information
- `GET /system/firmware` - Firmware information
- `POST /system/reboot` - Reboot system
- `GET /system/datetime` - Date/time settings
- `GET /system/timezones` - Available timezones

#### Streaming
- `GET /streams` - Available video streams (HD, RTSP)
- RTSP streams for real-time viewing
- Snapshot endpoints for still images

#### Camera Controls
- `GET /system/exposure` - Exposure settings
- `PUT /system/exposure` - Update exposure
- `GET /system/focus` - Focus settings
- `PUT /system/focus` - Update focus
- `GET /system/overlay` - Overlay settings
- `PUT /system/overlay` - Update overlay

## Features

### Core Functionality
1. **Event Management**
   - Real-time event monitoring
   - Automatic download of images/videos
   - Event filtering and search
   - Bulk operations
   - Event tagging and categorization
   - Tag-based filtering and organization

2. **Live Streaming**
   - RTSP stream access
   - HD stream viewing
   - Snapshot capture
   - Real-time monitoring
   - Video playback with authentication
   - Blob-based video streaming

3. **Tag Management System**
   - Create, edit, and delete custom tags
   - Color-coded tag organization
   - Tag assignment to events
   - Bulk tag operations
   - Tag usage statistics
   - Tag-based event filtering

4. **System Configuration**
   - Camera settings management
   - Network configuration
   - Recording parameters
   - Exposure and focus controls

5. **User Management**
   - Multi-factor authentication
   - Role-based access control (Admin, Manager, Viewer)
   - User permissions management
   - Session management

6. **Notifications**
   - Real-time event alerts
   - Email notifications
   - SMS alerts (optional)
   - Webhook integration

7. **Data Management**
   - Secure file storage
   - Backup and retention policies
   - Data export capabilities
   - Storage monitoring
   - File extension handling for proper downloads

## Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **Authentication**: JWT with MFA
- **File Storage**: Local storage with S3 backup
- **Real-time**: WebSocket/SSE for notifications
- **API Documentation**: OpenAPI/Swagger

### Frontend
- **Framework**: React with TypeScript
- **UI Library**: Material-UI or Ant Design
- **State Management**: Redux Toolkit
- **Real-time**: WebSocket client
- **Video Player**: Video.js or similar
- **Charts**: Chart.js or D3.js

### Infrastructure
- **Hosting**: AWS Lightsail
- **Database**: PostgreSQL on Lightsail
- **File Storage**: Local + S3
- **Monitoring**: CloudWatch
- **Security**: WireGuard VPN

## Development Plan

### Phase 1: Foundation (Week 1-2)
1. **Project Setup**
   - Initialize FastAPI backend
   - Set up PostgreSQL database
   - Create basic project structure
   - Implement Docker configuration

2. **Camera API Integration**
   - Create camera client library
   - Implement all API endpoints
   - Add error handling and retry logic
   - Create configuration management

3. **Authentication System**
   - JWT token implementation
   - MFA support (TOTP)
   - Role-based permissions
   - User management API

### Phase 2: Core Features (Week 3-4) ✅ COMPLETED
1. **Event Management** ✅
   - Event listing and filtering ✅
   - File download functionality ✅
   - Real-time event monitoring ✅
   - Event metadata storage ✅
   - Event tagging and categorization ✅
   - Tag-based filtering and organization ✅

2. **Live Streaming** ✅
   - RTSP stream integration ✅
   - Video player implementation ✅
   - Snapshot capture ✅
   - Stream quality management ✅
   - Video playback with authentication ✅
   - Blob-based video streaming ✅

3. **Tag Management System** ✅
   - Create, edit, and delete custom tags ✅
   - Color-coded tag organization ✅
   - Tag assignment to events ✅
   - Bulk tag operations ✅
   - Tag usage statistics ✅

4. **System Configuration** ✅
   - Settings management UI ✅
   - Camera parameter controls ✅
   - Network configuration ✅
   - System monitoring ✅

### Phase 3: Advanced Features (Week 5-6)
1. **Notification System**
   - Real-time alerts
   - Email notifications
   - Webhook integration
   - Alert preferences

2. **Data Management**
   - File storage optimization
   - Backup system
   - Retention policies
   - Data export

3. **User Interface**
   - Modern responsive design
   - Dashboard implementation
   - Mobile-friendly interface
   - Accessibility features

### Phase 4: Production Ready (Week 7-8)
1. **Security Hardening**
   - Security audit
   - Penetration testing
   - SSL/TLS configuration
   - Input validation

2. **Performance Optimization**
   - Database optimization
   - Caching implementation
   - File compression
   - Load testing

3. **Deployment**
   - AWS Lightsail setup
   - CI/CD pipeline
   - Monitoring and logging
   - Backup procedures

## Project Structure

```
pfcam/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── utils/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── docs/
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Docker and Docker Compose

### Development Setup
1. Clone the repository
2. Set up environment variables
3. Run `docker-compose up -d`
4. Access the application at `http://localhost:3000`

## Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key
- `CAMERA_BASE_URL`: Camera API base URL
- `S3_BUCKET`: S3 bucket for file storage
- `SMTP_SERVER`: Email server configuration

### Camera Configuration
- IP address management
- Network settings
- Recording parameters
- Trigger configuration

## Security Considerations

1. **Network Security**
   - WireGuard VPN for secure communication
   - Isolated customer environments
   - No direct internet access for cameras

2. **Application Security**
   - JWT authentication with MFA
   - Role-based access control
   - Input validation and sanitization
   - HTTPS enforcement

3. **Data Security**
   - Encrypted file storage
   - Secure backup procedures
   - Data retention policies
   - Audit logging

## Monitoring and Maintenance

1. **System Monitoring**
   - Camera connectivity status
   - Storage usage monitoring
   - Performance metrics
   - Error tracking

2. **Backup and Recovery**
   - Automated backups
   - Disaster recovery procedures
   - Data retention policies
   - System restore capabilities

## Support and Documentation

- API documentation (Swagger/OpenAPI)
- User manual
- Admin guide
- Troubleshooting guide
- Contact support information

## License

[License information to be added]

## Quick SSL/HTTPS Setup

- For local development, generate self-signed certs:
  ```sh
  mkdir -p nginx/ssl
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/privkey.pem \
    -out nginx/ssl/fullchain.pem \
    -subj "/CN=localhost"
  docker-compose restart nginx
  ```
  Then access your app at `https://localhost` (accept browser warning).

- For production, use a real SSL cert (e.g., Let's Encrypt) and place it in `nginx/ssl/`.

- Always use relative API URLs (e.g., `/api`) in your frontend `.env` for best HTTPS compatibility.

See `docs/DEVELOPMENT_PLAN.md` for full details. 