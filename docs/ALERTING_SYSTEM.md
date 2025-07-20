# PFCAM Alerting System

## Overview

The PFCAM alerting system provides comprehensive real-time notifications for camera events, system status changes, and user activities. The system is designed to work seamlessly across desktop and mobile devices with browser push notifications, email alerts, and in-app notifications.

## Features

### 🚨 Real-time Notifications
- **WebSocket-based real-time alerts** for instant notification delivery
- **Browser push notifications** for desktop and mobile devices
- **In-app notifications** with toast-style alerts
- **Auto-reconnection** with exponential backoff for reliable connectivity

### 📧 Email Alerts
- **HTML email templates** with responsive design
- **Event-specific notifications** with detailed information
- **System status alerts** for camera offline/online events
- **Test email functionality** for configuration verification

### 📱 Mobile Optimization
- **Responsive design** optimized for mobile devices
- **Touch-friendly interface** with proper button sizing
- **Mobile-optimized notifications** with appropriate timing
- **Progressive Web App (PWA) ready** for app-like experience

### ⚙️ User Preferences
- **Granular notification controls** for different event types
- **Email notification preferences** per user
- **Webhook integration** for external system notifications
- **Real-time status monitoring** of notification systems

## Architecture

### Backend Components

#### 1. Notification Service (`backend/app/services/notification_service.py`)
```python
class NotificationService:
    - WebSocketManager: Manages real-time connections
    - EmailService: Handles email notifications
    - Event triggers: Automatic notifications for events
```

#### 2. WebSocket Manager
- **Connection Management**: Handles multiple user connections
- **Message Queuing**: Ensures reliable message delivery
- **Authentication**: Secure WebSocket connections with JWT tokens
- **Auto-cleanup**: Removes broken connections automatically

#### 3. Email Service
- **SMTP Integration**: Configurable email server settings
- **Template Engine**: Jinja2-based HTML email templates
- **Responsive Design**: Mobile-friendly email layouts
- **Error Handling**: Graceful failure handling

### Frontend Components

#### 1. WebSocket Hook (`frontend/src/hooks/useWebSocket.ts`)
```typescript
useWebSocket({
  userId,
  onMessage,
  autoReconnect: true,
  reconnectInterval: 5000
})
```

#### 2. Notification Settings (`frontend/src/pages/NotificationSettings.tsx`)
- **Preference Management**: Toggle different notification types
- **Status Monitoring**: Real-time connection status
- **Test Functionality**: Email and WebSocket testing
- **Mobile UI**: Responsive design for all screen sizes

#### 3. Browser Push Notifications
- **Permission Management**: Automatic permission requests
- **Notification Types**: Different styles for priority levels
- **Click Actions**: Navigate to relevant pages on click
- **Auto-dismiss**: Configurable timeout for notifications

## Notification Types

### 1. Event Captured (`event_captured`)
**Trigger**: New camera event detected
**Priority**: High
**Channels**: WebSocket, Email, Browser Push
**Data**: Camera name, event details, timestamp

### 2. Camera Status (`camera_offline`, `camera_online`)
**Trigger**: Camera connectivity changes
**Priority**: High (offline), Normal (online)
**Channels**: WebSocket, Email (offline only)
**Data**: Camera name, status, timestamp

### 3. System Alerts (`system_alert`)
**Trigger**: System-wide events
**Priority**: Configurable
**Channels**: WebSocket, Email
**Data**: Alert type, message, timestamp

### 4. User Activity (`user_activity`)
**Trigger**: User actions (login, settings changes)
**Priority**: Low
**Channels**: WebSocket
**Data**: User action, timestamp

## Configuration

### Backend Configuration

#### Environment Variables
```bash
# Email Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TLS=true

# WebSocket Settings
ALLOWED_ORIGINS=["http://localhost:3000", "https://your-domain.com"]
```

#### Database Schema
```sql
-- User notification preferences
ALTER TABLE users ADD COLUMN email_notifications BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN webhook_url VARCHAR(255);
```

### Frontend Configuration

#### Environment Variables
```bash
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

#### WebSocket Connection
```typescript
const { isConnected, lastMessage } = useWebSocket({
  userId: currentUser.id,
  onMessage: handleNotification,
  autoReconnect: true,
  reconnectInterval: 5000,
  maxReconnectAttempts: 5
});
```

## API Endpoints

### WebSocket Endpoint
```
GET /api/v1/notifications/ws/{user_id}?token={jwt_token}
```

### REST Endpoints
```
GET    /api/v1/notifications/preferences     # Get user preferences
PUT    /api/v1/notifications/preferences     # Update preferences
GET    /api/v1/notifications/status          # Get connection status
POST   /api/v1/notifications/test-email      # Send test email
```

## Email Templates

### Event Notification Template
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PFCAM Event Alert</title>
    <style>
        /* Responsive CSS for mobile */
        @media (max-width: 600px) {
            .container { padding: 10px; }
            .header { padding: 15px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 PFCAM Event Alert</h1>
        </div>
        <div class="content">
            <h2>New Event Captured</h2>
            <div class="event-details">
                <h3>Event Details:</h3>
                <ul>
                    <li><strong>Camera:</strong> {{ camera.name }}</li>
                    <li><strong>Event Name:</strong> {{ event.event_name }}</li>
                    <li><strong>Triggered:</strong> {{ event.triggered_at }}</li>
                </ul>
            </div>
            <a href="{{ app_url }}/events" class="button">View Event</a>
        </div>
    </div>
</body>
</html>
```

## Mobile Optimization

### Responsive Design
- **Flexible Layouts**: CSS Grid and Flexbox for adaptive layouts
- **Touch Targets**: Minimum 44px touch targets for mobile
- **Font Scaling**: Responsive typography that scales appropriately
- **Viewport Meta**: Proper viewport configuration for mobile devices

### Performance Optimization
- **Lazy Loading**: Components load only when needed
- **Image Optimization**: Compressed images and proper sizing
- **Caching**: Browser caching for static assets
- **Minification**: Production builds with minified code

### Mobile-Specific Features
- **Swipe Gestures**: Touch-friendly navigation
- **Pull-to-Refresh**: Native mobile interaction patterns
- **Offline Support**: Service worker for offline functionality
- **App-like Experience**: Full-screen mode and splash screens

## Security Considerations

### WebSocket Security
- **JWT Authentication**: Secure token-based authentication
- **User Validation**: Verify user ID matches token
- **Connection Limits**: Prevent connection abuse
- **Rate Limiting**: API rate limiting for notifications

### Email Security
- **SMTP Authentication**: Secure email server authentication
- **TLS Encryption**: Encrypted email transmission
- **Template Sanitization**: Prevent XSS in email templates
- **Spam Prevention**: Proper email headers and formatting

### Data Privacy
- **User Consent**: Explicit permission for notifications
- **Data Minimization**: Only send necessary information
- **Retention Policies**: Automatic cleanup of old notifications
- **GDPR Compliance**: User data handling compliance

## Monitoring and Analytics

### Connection Monitoring
```python
# WebSocket connection metrics
active_connections = len(ws_manager.active_connections)
connection_health = check_connection_health()
```

### Email Delivery Tracking
```python
# Email delivery statistics
email_sent_count = track_email_delivery()
delivery_rate = calculate_delivery_rate()
```

### User Engagement
```typescript
// Frontend analytics
notification_click_rate = track_notification_clicks();
preference_changes = track_preference_updates();
```

## Troubleshooting

### Common Issues

#### WebSocket Connection Failures
```bash
# Check WebSocket endpoint
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==" \
     http://localhost:8000/api/v1/notifications/ws/1
```

#### Email Delivery Issues
```bash
# Test SMTP connection
python -c "
import smtplib
s = smtplib.SMTP('smtp.gmail.com', 587)
s.starttls()
s.login('your-email@gmail.com', 'your-password')
s.quit()
"
```

#### Browser Notification Issues
```javascript
// Check notification permission
if ('Notification' in window) {
  console.log('Permission:', Notification.permission);
  if (Notification.permission === 'default') {
    Notification.requestPermission();
  }
}
```

### Debug Mode
```bash
# Enable debug logging
LOG_LEVEL=DEBUG
docker compose up backend
```

## Future Enhancements

### Planned Features
1. **SMS Notifications**: Twilio integration for SMS alerts
2. **Slack Integration**: Direct Slack channel notifications
3. **Advanced Filtering**: Custom notification rules and filters
4. **Notification History**: Persistent notification log
5. **Bulk Operations**: Mass notification management

### Mobile App
1. **Native Mobile App**: React Native or Flutter app
2. **Push Notifications**: Firebase Cloud Messaging
3. **Offline Mode**: Local notification storage
4. **Background Sync**: Automatic data synchronization

### AI Integration
1. **Smart Filtering**: AI-powered notification relevance
2. **Predictive Alerts**: Anticipate system issues
3. **Voice Notifications**: Text-to-speech for critical alerts
4. **Image Analysis**: AI-powered event classification

## Best Practices

### Performance
- **Connection Pooling**: Reuse WebSocket connections
- **Message Batching**: Group similar notifications
- **Lazy Loading**: Load notification components on demand
- **Caching**: Cache user preferences and templates

### User Experience
- **Progressive Enhancement**: Graceful degradation for older browsers
- **Accessibility**: WCAG 2.1 AA compliance
- **Internationalization**: Multi-language support
- **Customization**: User-configurable notification styles

### Security
- **Input Validation**: Validate all notification data
- **Rate Limiting**: Prevent notification spam
- **Audit Logging**: Track all notification activities
- **Encryption**: Encrypt sensitive notification data

## Conclusion

The PFCAM alerting system provides a comprehensive, secure, and user-friendly notification solution that works seamlessly across desktop and mobile devices. With real-time WebSocket notifications, email alerts, and browser push notifications, users stay informed about important events and system status changes.

The system is designed with scalability, security, and user experience in mind, making it suitable for both small deployments and large-scale enterprise installations. 