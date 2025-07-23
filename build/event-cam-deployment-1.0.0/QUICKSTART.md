# PFCAM Quick Start Guide

## Prerequisites

- Docker and Docker Compose installed
- Python 3.8+ (for local development)
- PostgreSQL (for local development)

## Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pfcam
   ```

2. **Start the application**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Admin Interface: http://localhost:3000 (when frontend is ready)

4. **Default credentials**
   - Username: `admin`
   - Password: `admin123`
   - Email: `admin@pfcam.local`

## Local Development Setup

### 1. Database Setup

The application uses PostgreSQL. You can either:

**Option A: Use Docker for database only**
```bash
docker-compose up postgres -d
```

**Option B: Install PostgreSQL locally**
```bash
# macOS
brew install postgresql
brew services start postgresql

# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

Create the database:
```bash
createdb pfcam
```

### 2. Backend Setup

1. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Initialize database**
   ```bash
   # Run migrations
   python manage_db.py migrate
   
   # Initialize database with admin user
   python init_db.py
   ```

4. **Start the backend**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### 3. Test the API

1. **Get an access token**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "admin", "password": "admin123"}'
   ```

2. **Test camera connection**
   ```bash
   # First, add a camera
   curl -X POST "http://localhost:8000/api/v1/cameras" \
        -H "Authorization: Bearer YOUR_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
          "name": "Test Camera",
          "ip_address": "192.168.86.33",
          "base_url": "http://192.168.86.33"
        }'
   ```

3. **List events**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/events" \
        -H "Authorization: Bearer YOUR_TOKEN"
   ```

## API Endpoints Overview

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - Logout

### Users
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

### Cameras
- `GET /api/v1/cameras` - List cameras
- `POST /api/v1/cameras` - Add camera
- `GET /api/v1/cameras/{id}/status` - Camera status
- `POST /api/v1/cameras/{id}/test` - Test connection

### Events
- `GET /api/v1/events` - List events
- `GET /api/v1/events/{id}/download` - Download event file
- `POST /api/v1/events/sync` - Sync events from camera

### Settings
- `GET /api/v1/settings/{camera_id}` - Get camera settings
- `PUT /api/v1/settings/{camera_id}` - Update settings

### Streams
- `GET /api/v1/streams/{camera_id}` - Get camera streams
- `GET /api/v1/streams/{camera_id}/rtsp/info` - RTSP stream info

## Database Management

### Using the management script
```bash
# Run migrations
python manage_db.py migrate

# Create a new migration
python manage_db.py create-migration "Add new feature"

# Show migration history
python manage_db.py history

# Show current revision
python manage_db.py current

# Initialize database
python manage_db.py init
```

### Using Alembic directly
```bash
# Run migrations
alembic upgrade head

# Create migration
alembic revision --autogenerate -m "Description"

# Rollback
alembic downgrade -1
```

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=postgresql://pfcam:pfcam@localhost:5432/pfcam

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Storage
STORAGE_PATH=/app/storage

# Camera
CAMERA_BASE_URL=http://192.168.86.33
```

### Camera Configuration

The application is designed to work with industrial event cameras accessible via HTTP. The camera should be:

1. **Network accessible** from the application server
2. **API enabled** with Swagger documentation at `/api/ui/#/`
3. **Properly configured** with event recording enabled

## Troubleshooting

### Common Issues

1. **Database connection failed**
   - Ensure PostgreSQL is running
   - Check DATABASE_URL in .env
   - Verify database exists: `createdb pfcam`

2. **Camera connection failed**
   - Verify camera IP is accessible
   - Check camera API is enabled
   - Ensure proper network configuration

3. **Permission denied errors**
   - Check user roles and permissions
   - Verify JWT token is valid
   - Ensure proper authorization headers

### Logs

View application logs:
```bash
# Docker
docker-compose logs backend

# Local
tail -f logs/app.log
```

### Health Check

Check application health:
```bash
curl http://localhost:8000/health
```

## Next Steps

1. **Configure your camera** - Add your camera to the system
2. **Set up event recording** - Configure camera settings for event detection
3. **Test event capture** - Trigger events and verify recording
4. **Set up notifications** - Configure alerts for new events
5. **Customize settings** - Adjust recording parameters and system settings

## Support

For issues and questions:
- Check the API documentation at http://localhost:8000/docs
- Review the logs for error messages
- Consult the development plan in `docs/DEVELOPMENT_PLAN.md` 

## Camera Health Monitoring & Reconnect

- The system automatically checks all cameras every 30 minutes.
- Offline cameras are shown with a red indicator on the dashboard.
- You can manually attempt to reconnect an offline camera using the "Reconnect" button next to it.
- Notifications are sent when a camera goes offline or comes back online. 