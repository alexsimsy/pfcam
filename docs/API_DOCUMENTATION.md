# PFCAM API Documentation

## Overview

The PFCAM API provides a comprehensive interface for managing industrial event cameras, events, users, and system settings. The API is built with FastAPI and follows RESTful principles.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All API endpoints (except authentication endpoints) require a valid JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### Authentication

#### POST /auth/login
Authenticate user and receive access token.

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@pfcam.local",
    "username": "admin",
    "full_name": "System Administrator",
    "role": "ADMIN",
    "is_active": true
  }
}
```

#### POST /auth/refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### POST /auth/logout
Logout user and invalidate tokens.

### Users

#### GET /users
List all users with optional filtering.

**Query Parameters:**
- `role` (optional): Filter by role (ADMIN, MANAGER, VIEWER)
- `is_active` (optional): Filter by active status

**Response:**
```json
[
  {
    "id": 1,
    "email": "admin@pfcam.local",
    "username": "admin",
    "full_name": "System Administrator",
    "role": "ADMIN",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### GET /users/me
Get current user information.

#### POST /users
Create a new user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "newuser",
  "password": "password123",
  "full_name": "New User",
  "role": "VIEWER"
}
```

#### PUT /users/{user_id}
Update user information.

#### DELETE /users/{user_id}
Delete user account.

### Cameras

#### GET /cameras
List all cameras with optional filtering.

**Query Parameters:**
- `is_active` (optional): Filter by active status
- `is_online` (optional): Filter by online status

**Response:**
```json
[
  {
    "id": 1,
    "name": "Camera 1",
    "ip_address": "192.168.86.33",
    "port": 80,
    "base_url": "http://192.168.86.33",
    "is_active": true,
    "is_online": true,
    "last_seen": "2024-01-01T12:00:00Z"
  }
]
```

#### POST /cameras
Create a new camera.

**Request Body:**
```json
{
  "name": "New Camera",
  "ip_address": "192.168.86.34",
  "port": 80,
  "base_url": "http://192.168.86.34",
  "username": "admin",
  "password": "password",
  "use_ssl": false
}
```

#### GET /cameras/{camera_id}/status
Get camera status and health information.

#### POST /cameras/{camera_id}/test
Test camera connection.

#### POST /cameras/{camera_id}/reboot
Reboot camera.

### Events

#### GET /events
List events with filtering and pagination.

**Query Parameters:**
- `camera_id` (optional): Filter by camera ID
- `event_name` (optional): Filter by event name
- `start_date` (optional): Start date filter
- `end_date` (optional): End date filter
- `limit` (optional): Number of events to return (default: 50, max: 100)
- `offset` (optional): Number of events to skip
- `sort_by` (optional): Sort field (triggered_at, filename)
- `sort_order` (optional): Sort order (asc, desc)

**Response:**
```json
{
  "events": [
    {
      "id": 1,
      "camera_id": 1,
      "filename": "event_20240101_120000.mp4",
      "event_name": "Motion Detected",
      "triggered_at": "2024-01-01T12:00:00Z",
      "file_size": 1024000,
      "is_downloaded": true,
      "is_processed": false
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

#### GET /events/{event_id}
Get specific event details.

#### GET /events/{event_id}/download
Download event file (image/video).

#### GET /events/{event_id}/thumbnail
Get event thumbnail.

#### DELETE /events/{event_id}
Delete event and associated files.

#### POST /events/sync
Sync events from camera to database.

#### GET /events/active/list
List currently active events from camera.

#### DELETE /events/active/stop
Stop all active events.

### Settings

#### GET /settings/{camera_id}
Get camera settings.

**Response:**
```json
{
  "camera_id": 1,
  "settings": {
    "network": {
      "ip": "192.168.86.33",
      "mask": "255.255.255.0",
      "gateway": "192.168.86.1",
      "dns": "8.8.8.8",
      "dhcp": false
    },
    "recording": {
      "seconds_pre_event": 5,
      "seconds_post_event": 10,
      "resolution_width": 1920,
      "quality_level": 80
    },
    "exposure": {
      "iso": 100,
      "shutter": 1,
      "manual": false
    }
  },
  "version": "1.0"
}
```

#### PUT /settings/{camera_id}
Update camera settings.

**Request Body:**
```json
{
  "recording_seconds_pre_event": 10,
  "recording_seconds_post_event": 15,
  "exposure_iso": 200
}
```

#### DELETE /settings/{camera_id}/reset
Reset camera settings to defaults.

#### GET /settings/{camera_id}/exposure
Get camera exposure settings.

#### PUT /settings/{camera_id}/exposure
Update camera exposure settings.

#### GET /settings/{camera_id}/focus
Get camera focus settings.

#### PUT /settings/{camera_id}/focus
Update camera focus settings.

#### GET /settings/{camera_id}/overlay
Get camera overlay settings.

#### PUT /settings/{camera_id}/overlay
Update camera overlay settings.

### Streams

#### GET /streams/{camera_id}
Get available streams for a camera.

**Response:**
```json
{
  "camera_id": 1,
  "streams": [
    {
      "name": "rtsp",
      "stream_info": {
        "codec": "H.264",
        "fps": 30,
        "resolution": {"width": 1920, "height": 1080},
        "url": {"absolute": "rtsp://192.168.86.33:554/stream1"}
      }
    },
    {
      "name": "hd",
      "stream_info": {
        "codec": "H.264",
        "fps": 30,
        "resolution": {"width": 1920, "height": 1080},
        "url": {"absolute": "http://192.168.86.33/video/hd"},
        "snapshot": {"url": {"absolute": "http://192.168.86.33/snapshot/hd"}}
      }
    }
  ],
  "count": 2
}
```

#### GET /streams/{camera_id}/{stream_name}
Get specific stream information.

#### GET /streams/{camera_id}/{stream_name}/url
Get stream URL for video player.

#### GET /streams/{camera_id}/{stream_name}/snapshot
Get snapshot from stream.

#### GET /streams/{camera_id}/rtsp/info
Get RTSP stream information.

#### GET /streams/{camera_id}/hd/info
Get HD stream information.

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

API requests are rate-limited to prevent abuse. Limits are applied per user and endpoint.

## Pagination

List endpoints support pagination with the following parameters:
- `limit`: Number of items per page (default: 50, max: 100)
- `offset`: Number of items to skip

## Filtering

Many list endpoints support filtering with query parameters. See individual endpoint documentation for available filters.

## Sorting

List endpoints support sorting with the following parameters:
- `sort_by`: Field to sort by
- `sort_order`: Sort order (asc, desc)

## File Uploads

File uploads are supported for event files and thumbnails. Files are stored in the configured storage path.

## WebSocket Support

Real-time updates are available via WebSocket connections for:
- Live camera status updates
- New event notifications
- System alerts

WebSocket endpoint: `ws://localhost:8000/ws` 