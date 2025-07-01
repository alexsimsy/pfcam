# PFCAM Development Plan

## Executive Summary

This document outlines the comprehensive development plan for the PFCAM (Industrial Event Camera Management) system. The application will provide a secure, scalable platform for managing industrial event cameras deployed in remote locations via the SIMSY network.

## Project Overview

### Business Requirements
- **Security**: Isolated camera access via SIMSY network with WireGuard VPN
- **Scalability**: Per-customer Lightsail instances for security and performance
- **Reliability**: Robust event capture and storage with backup systems
- **Usability**: Modern web interface with role-based access control
- **Real-time**: Live streaming and immediate event notifications

### Technical Requirements
- **Backend**: FastAPI with PostgreSQL database
- **Frontend**: React with TypeScript and modern UI framework
- **Authentication**: JWT with multi-factor authentication
- **File Storage**: Local storage with S3 backup
- **Real-time**: WebSocket/SSE for live updates
- **Deployment**: Docker containers on AWS Lightsail

## Phase 1: Foundation (Weeks 1-2)

### 1.1 Project Setup and Infrastructure

#### Tasks:
- [ ] Initialize Git repository with proper branching strategy
- [ ] Set up development environment with Docker
- [ ] Create project structure for backend and frontend
- [ ] Configure CI/CD pipeline (GitHub Actions)
- [ ] Set up development database (PostgreSQL)

#### Deliverables:
- Complete project structure
- Docker development environment
- Basic CI/CD pipeline
- Development database setup

#### Technical Specifications:
```yaml
# docker-compose.yml structure
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/pfcam
    depends_on: [db]
  
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=pfcam
      - POSTGRES_USER=pfcam
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### 1.2 Camera API Integration

#### Tasks:
- [ ] Create camera client library (Python)
- [ ] Implement all API endpoints with error handling
- [ ] Add retry logic and connection pooling
- [ ] Create configuration management system
- [ ] Implement camera health monitoring

#### Deliverables:
- Complete camera API client
- Configuration management system
- Health monitoring service
- Error handling and logging

#### Technical Specifications:
```python
# Camera client structure
class CameraClient:
    def __init__(self, base_url: str, credentials: dict):
        self.base_url = base_url
        self.session = aiohttp.ClientSession()
    
    async def get_events(self, filters: dict = None) -> List[Event]:
        """Retrieve events with optional filtering"""
    
    async def download_event(self, filename: str) -> bytes:
        """Download event file (image/video)"""
    
    async def get_settings(self) -> Settings:
        """Get current camera settings"""
    
    async def update_settings(self, settings: Settings) -> Settings:
        """Update camera settings"""
    
    async def get_streams(self) -> Streams:
        """Get available video streams"""
    
    async def get_system_info(self) -> SystemInfo:
        """Get system information"""
```

### 1.3 Authentication System

#### Tasks:
- [ ] Implement JWT token authentication
- [ ] Add multi-factor authentication (TOTP)
- [ ] Create role-based access control
- [ ] Implement user management API
- [ ] Add session management

#### Deliverables:
- Complete authentication system
- User management API
- Role-based permissions
- MFA implementation

#### Technical Specifications:
```python
# User roles and permissions
class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"

class Permission(str, Enum):
    VIEW_EVENTS = "view_events"
    DOWNLOAD_EVENTS = "download_events"
    DELETE_EVENTS = "delete_events"
    MANAGE_SETTINGS = "manage_settings"
    MANAGE_USERS = "manage_users"
    VIEW_STREAMS = "view_streams"
    MANAGE_SYSTEM = "manage_system"

# Permission mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [p for p in Permission],
    UserRole.MANAGER: [
        Permission.VIEW_EVENTS,
        Permission.DOWNLOAD_EVENTS,
        Permission.MANAGE_SETTINGS,
        Permission.VIEW_STREAMS
    ],
    UserRole.VIEWER: [
        Permission.VIEW_EVENTS,
        Permission.VIEW_STREAMS
    ]
}
```

## Phase 2: Core Features (Weeks 3-4)

### 2.1 Event Management System

#### Tasks:
- [ ] Create event data models and database schema
- [ ] Implement event listing with filtering and pagination
- [ ] Add file download functionality
- [ ] Create real-time event monitoring
- [ ] Implement event metadata storage

#### Deliverables:
- Complete event management API
- Real-time event monitoring
- File download system
- Event search and filtering

#### Technical Specifications:
```sql
-- Event table schema
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER REFERENCES cameras(id),
    filename VARCHAR(255) NOT NULL,
    event_name VARCHAR(100),
    triggered_at TIMESTAMP NOT NULL,
    file_size BIGINT,
    file_path VARCHAR(500),
    thumbnail_path VARCHAR(500),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_events_camera_id ON events(camera_id);
CREATE INDEX idx_events_triggered_at ON events(triggered_at);
CREATE INDEX idx_events_event_name ON events(event_name);
```

### 2.2 Live Streaming Integration

#### Tasks:
- [ ] Integrate RTSP stream access
- [ ] Implement video player component
- [ ] Add snapshot capture functionality
- [ ] Create stream quality management
- [ ] Implement stream health monitoring

#### Deliverables:
- Live streaming functionality
- Video player component
- Snapshot system
- Stream monitoring

#### Technical Specifications:
```typescript
// Stream interface
interface Stream {
    name: string;
    codec: string;
    fps: number;
    resolution: {
        width: number;
        height: number;
    };
    url: {
        absolute: string;
        relative: string;
    };
    snapshot?: {
        url: {
            absolute: string;
            relative: string;
        };
    };
}

// Video player component
interface VideoPlayerProps {
    stream: Stream;
    autoPlay?: boolean;
    controls?: boolean;
    onError?: (error: Error) => void;
}
```

### 2.3 System Configuration Management

#### Tasks:
- [ ] Create settings management API
- [ ] Implement camera parameter controls
- [ ] Add network configuration interface
- [ ] Create system monitoring dashboard
- [ ] Implement configuration validation

#### Deliverables:
- Complete settings management system
- Camera control interface
- Network configuration
- System monitoring

#### Technical Specifications:
```python
# Settings model
class CameraSettings(BaseModel):
    # Network settings
    network_ip: str
    network_mask: str
    network_gateway: str
    network_dns: str
    network_dhcp: bool
    
    # Recording settings
    recording_seconds_pre_event: int
    recording_seconds_post_event: int
    recording_resolution_width: int
    recording_quality_level: int
    
    # Exposure settings
    exposure_iso: int
    exposure_shutter: int
    exposure_manual: bool
    
    # Focus settings
    focus_setpoint: int
    
    # Overlay settings
    overlay_datetime: bool
    overlay_name: bool
    overlay_background: bool
    
    # RTSP settings
    rtsp_port: int
    rtsp_path: str
    rtsp_fps: int
    rtsp_quality_level: int
```

## Phase 3: Advanced Features (Weeks 5-6)

### 3.1 Notification System

#### Tasks:
- [ ] Implement real-time alerts via WebSocket
- [ ] Create email notification system
- [ ] Add webhook integration
- [ ] Implement alert preferences
- [ ] Create notification templates

#### Deliverables:
- Real-time notification system
- Email notification service
- Webhook integration
- Alert management interface

#### Technical Specifications:
```python
# Notification system
class NotificationService:
    def __init__(self):
        self.email_service = EmailService()
        self.webhook_service = WebhookService()
        self.websocket_manager = WebSocketManager()
    
    async def send_event_notification(self, event: Event, users: List[User]):
        """Send notifications for new events"""
        for user in users:
            if user.email_notifications:
                await self.email_service.send_event_email(user, event)
            
            if user.webhook_url:
                await self.webhook_service.send_webhook(user.webhook_url, event)
            
            await self.websocket_manager.send_to_user(user.id, {
                "type": "event",
                "data": event.dict()
            })
```

### 3.2 Data Management and Storage

#### Tasks:
- [ ] Implement file storage optimization
- [ ] Create backup system
- [ ] Add data retention policies
- [ ] Implement data export functionality
- [ ] Create storage monitoring

#### Deliverables:
- Optimized file storage system
- Automated backup system
- Data retention management
- Export functionality

#### Technical Specifications:
```python
# Storage management
class StorageManager:
    def __init__(self, local_path: str, s3_bucket: str):
        self.local_path = local_path
        self.s3_bucket = s3_bucket
    
    async def store_event_file(self, event: Event, file_data: bytes) -> str:
        """Store event file locally and backup to S3"""
    
    async def cleanup_old_files(self, retention_days: int):
        """Remove files older than retention period"""
    
    async def backup_to_s3(self, file_path: str):
        """Backup file to S3"""
    
    async def get_storage_usage(self) -> StorageUsage:
        """Get current storage usage statistics"""
```

### 3.3 User Interface Development

#### Tasks:
- [ ] Create modern responsive design
- [ ] Implement dashboard with key metrics
- [ ] Add mobile-friendly interface
- [ ] Implement accessibility features
- [ ] Create user preference management

#### Deliverables:
- Complete user interface
- Responsive design
- Dashboard implementation
- Accessibility compliance

#### Technical Specifications:
```typescript
// Dashboard components
interface DashboardProps {
    user: User;
    cameras: Camera[];
    recentEvents: Event[];
    systemStats: SystemStats;
}

// Main layout structure
const AppLayout: React.FC = () => {
    return (
        <Layout>
            <Header>
                <Logo />
                <UserMenu />
                <Notifications />
            </Header>
            <Sidebar>
                <Navigation />
            </Sidebar>
            <Main>
                <Routes>
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/events" element={<Events />} />
                    <Route path="/cameras" element={<Cameras />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="/users" element={<Users />} />
                </Routes>
            </Main>
        </Layout>
    );
};
```

## Phase 4: Production Ready (Weeks 7-8)

### 4.1 Security Hardening

#### Tasks:
- [ ] Conduct security audit
- [ ] Implement penetration testing
- [ ] Configure SSL/TLS
- [ ] Add input validation and sanitization
- [ ] Implement rate limiting

#### Deliverables:
- Security audit report
- Penetration test results
- SSL/TLS configuration
- Security hardening documentation

### 4.2 Performance Optimization

#### Tasks:
- [ ] Optimize database queries
- [ ] Implement caching system
- [ ] Add file compression
- [ ] Conduct load testing
- [ ] Optimize frontend performance

#### Deliverables:
- Performance optimization report
- Caching implementation
- Load test results
- Performance monitoring

### 4.3 Deployment and Monitoring

#### Tasks:
- [ ] Set up AWS Lightsail environment
- [ ] Configure production database
- [ ] Implement monitoring and logging
- [ ] Create backup procedures
- [ ] Set up CI/CD for production

#### Deliverables:
- Production deployment
- Monitoring and logging system
- Backup procedures
- Deployment documentation

## Technical Architecture

### Backend Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   PostgreSQL    │    │   Redis Cache   │
│                 │    │                 │    │                 │
│ ├─ API Routes   │    │ ├─ Events       │    │ ├─ Sessions     │
│ ├─ Services     │    │ ├─ Users        │    │ ├─ Cache        │
│ ├─ Models       │    │ ├─ Cameras      │    │ └─ Queues       │
│ └─ Utils        │    │ └─ Settings     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   File Storage  │
                    │                 │
                    │ ├─ Local Files  │
                    │ └─ S3 Backup    │
                    └─────────────────┘
```

### Frontend Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │    │   Redux Store   │    │   API Client    │
│                 │    │                 │    │                 │
│ ├─ Components   │    │ ├─ Auth         │    │ ├─ Events       │
│ ├─ Pages        │    │ ├─ Events       │    │ ├─ Cameras      │
│ ├─ Hooks        │    │ ├─ Cameras      │    │ ├─ Settings     │
│ └─ Utils        │    │ └─ UI           │    │ └─ Streaming    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   WebSocket     │
                    │   Connection    │
                    │                 │
                    │ ├─ Real-time    │
                    │ └─ Notifications│
                    └─────────────────┘
```

## SSL Certificates and HTTPS Setup

### Why HTTPS?
- Modern browsers require HTTPS for many features and will block insecure requests (mixed content).
- HTTPS is required for secure user authentication, API calls, and production best practices.

### Local Development: Self-Signed Certificates
To enable HTTPS locally with nginx:

1. Generate self-signed certificates:
   ```sh
   mkdir -p nginx/ssl
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout nginx/ssl/privkey.pem \
     -out nginx/ssl/fullchain.pem \
     -subj "/CN=localhost"
   ```
   - This creates `privkey.pem` and `fullchain.pem` in `nginx/ssl`.
   - You can change `/CN=localhost` to your dev domain or local IP if needed.

2. Restart nginx:
   ```sh
   docker-compose restart nginx
   ```

3. Access your app at `https://localhost`. Accept the browser warning for self-signed certs.

### Production: Trusted Certificates
- Use a real SSL certificate from a trusted CA (e.g., Let's Encrypt).
- With Let's Encrypt, use [Certbot](https://certbot.eff.org/) to generate and renew certs for your domain.
- Place the certs at `nginx/ssl/fullchain.pem` and `nginx/ssl/privkey.pem`.
- Update DNS to point your domain to your server before running Certbot.

### Frontend/Backend Alignment
- Always use relative API URLs (e.g., `/api`) in `.env` for Vite/React.
- nginx proxies `/api` and `/ws` to the backend, handling HTTPS at the edge.
- For production, ensure all user-facing URLs are HTTPS.

## Risk Assessment and Mitigation

### Technical Risks
1. **Camera API Changes**: Monitor API documentation and implement versioning
2. **Network Connectivity**: Implement robust retry logic and fallback mechanisms
3. **Storage Limitations**: Implement data retention policies and monitoring
4. **Performance Issues**: Regular load testing and optimization

### Security Risks
1. **Unauthorized Access**: Implement strong authentication and authorization
2. **Data Breaches**: Encrypt sensitive data and implement audit logging
3. **Network Attacks**: Use VPN and implement network security measures

### Operational Risks
1. **System Downtime**: Implement monitoring and alerting
2. **Data Loss**: Regular backups and disaster recovery procedures
3. **Scalability Issues**: Design for horizontal scaling from the start

## Success Criteria

### Functional Requirements
- [ ] All camera API endpoints integrated
- [ ] Real-time event monitoring working
- [ ] Live streaming functional
- [ ] User authentication and authorization complete
- [ ] Notification system operational

### Performance Requirements
- [ ] Page load times < 2 seconds
- [ ] API response times < 500ms
- [ ] Support for 100+ concurrent users
- [ ] 99.9% uptime target

### Security Requirements
- [ ] All data encrypted in transit and at rest
- [ ] Multi-factor authentication working
- [ ] Role-based access control implemented
- [ ] Security audit passed

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | Weeks 1-2 | Project foundation, camera integration, authentication |
| Phase 2 | Weeks 3-4 | Event management, streaming, configuration |
| Phase 3 | Weeks 5-6 | Notifications, data management, UI |
| Phase 4 | Weeks 7-8 | Security, performance, deployment |

## Next Steps

1. **Immediate Actions**:
   - Set up development environment
   - Create project structure
   - Begin Phase 1 implementation

2. **Resource Requirements**:
   - 2-3 developers (backend/frontend)
   - DevOps engineer for deployment
   - Security specialist for audit

3. **Dependencies**:
   - Camera API documentation
   - AWS Lightsail access
   - SIMSY network configuration

This development plan provides a comprehensive roadmap for building the PFCAM system. Each phase builds upon the previous one, ensuring a solid foundation and systematic approach to development. 