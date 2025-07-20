# PFCAM User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [User Roles & Permissions](#user-roles--permissions)
3. [Navigation](#navigation)
4. [Dashboard](#dashboard)
5. [Events Management](#events-management)
6. [Live Streams](#live-streams)
7. [Settings Management](#settings-management)
8. [User Management](#user-management)
9. [Troubleshooting](#troubleshooting)

---

## Getting Started

### First Login
- **Default Admin Credentials:**
  - Email: `admin@s-imsy.com`
  - Password: `admin123`
- **Important:** Change the default password after your first login

### Browser Requirements
- **Recommended:** Chrome, Firefox, Safari, Edge (latest versions)
- **Required:** JavaScript enabled
- **For Video Playback:** Safari is recommended for optimal streaming performance

---

## User Roles & Permissions

### **🔴 ADMIN Role**
**Full system access with all permissions:**
- ✅ **View Events** - See all events and their details
- ✅ **Download Events** - Download event files (videos/images)
- ✅ **Delete Events** - Remove events from the system
- ✅ **Manage Events** - Edit event metadata, assign tags
- ✅ **Manage Settings** - Configure camera and application settings
- ✅ **Manage Users** - Create, edit, delete users and assign roles
- ✅ **View Streams** - Access live camera streams
- ✅ **Manage System** - System-level configuration and maintenance
- ✅ **View Cameras** - See camera status and information
- ✅ **Manage Cameras** - Configure camera settings and parameters

### **🟡 MANAGER Role**
**Operational access with limited administrative functions:**
- ✅ **View Events** - See all events and their details
- ✅ **Download Events** - Download event files (videos/images)
- ✅ **Manage Settings** - Configure camera and application settings
- ✅ **View Streams** - Access live camera streams
- ✅ **View Cameras** - See camera status and information

**❌ Restricted from:**
- User management (create/edit/delete users)
- Event deletion
- System-level management
- Camera configuration changes

### **🟢 VIEWER Role**
**Read-only access for monitoring:**
- ✅ **View Events** - See all events and their details
- ✅ **View Streams** - Access live camera streams
- ✅ **View Cameras** - See camera status and information

**❌ Restricted from:**
- Downloading event files
- Any settings changes
- User management
- Event management (deletion, editing)
- System configuration

### **Permission Matrix**

| Permission | Admin | Manager | Viewer |
|------------|-------|---------|--------|
| **View Events** | ✅ | ✅ | ✅ |
| **Download Events** | ✅ | ✅ | ❌ |
| **Delete Events** | ✅ | ❌ | ❌ |
| **Manage Settings** | ✅ | ✅ | ❌ |
| **Manage Users** | ✅ | ❌ | ❌ |
| **View Streams** | ✅ | ✅ | ✅ |
| **Manage System** | ✅ | ❌ | ❌ |
| **View Cameras** | ✅ | ✅ | ✅ |
| **Manage Cameras** | ✅ | ❌ | ❌ |

### **Recommended Role Usage**
- **Admin**: System administrators who need full control
- **Manager**: Operations staff who need to manage events and settings but shouldn't manage users
- **Viewer**: Monitoring staff who only need to view events and streams

---

## Navigation

### Top Navigation Bar
The application features a clean navigation bar with the following sections:

- **Dashboard** - Overview and statistics
- **Events** - Event management and viewing
- **Streams** - Live camera streams
- **Settings** - System configuration
- **Admin** - User management (Admin role only)

### User Menu
Click on your username in the top-right corner to access:
- **Profile Settings** - Update your account information
- **Change Password** - Modify your login credentials
- **Logout** - Sign out of the system

---

## Dashboard

### Overview
The Dashboard provides a comprehensive overview of your PFCAM system with real-time statistics and quick access to key features.

### Key Metrics
- **Total Events** - Number of active events in the system
- **Events in Last 24 Hours** - Recent activity count
- **Unviewed Events** - Events that haven't been marked as viewed
- **Events by Tag** - Distribution of events by category

### Auto-Refresh
- The dashboard automatically refreshes every 30 seconds
- Use the "Refresh Stats" button for immediate updates
- Statistics only show active (non-deleted) events

### Quick Actions
- **View Recent Events** - Click on event counts to navigate to the Events page
- **Access Live Streams** - Quick link to camera streams
- **System Status** - Monitor camera connectivity and system health

---

## Events Management

### Viewing Events
1. Navigate to the **Events** page
2. Events are displayed in chronological order (newest first)
3. Use filters to narrow down results:
   - **Date Range** - Select specific time periods
   - **Tags** - Filter by event categories
   - **Camera** - View events from specific cameras
   - **Status** - Filter by viewed/unviewed events

### Event Details
Each event displays:
- **Event Name** - Descriptive name of the event
- **Timestamp** - When the event occurred
- **Camera** - Which camera triggered the event
- **File Size** - Size of associated video/image
- **Tags** - Categories assigned to the event
- **Status** - Viewed/unviewed indicator

### Event Actions
Depending on your role, you can:
- **View Event** - Click to see event details and media
- **Download** - Download event files (Admin/Manager only)
- **Edit Tags** - Assign or modify event categories
- **Delete** - Remove events from system (Admin only)
- **Mark as Viewed** - Update event status

### Tag Management
- **Create Tags** - Add new categories with custom colors
- **Assign Tags** - Categorize events for better organization
- **Filter by Tags** - Quickly find related events
- **Bulk Operations** - Apply tags to multiple events at once

---

## Live Streams

### Accessing Streams
1. Navigate to the **Streams** page
2. Select the camera you want to view
3. Choose stream quality (if available)
4. Click "View Stream" to open the video player

### Stream Features
- **Real-time Viewing** - Live camera feed with minimal delay
- **Quality Selection** - Choose between different resolution options
- **Snapshot Capture** - Take still images from the stream
- **Full-screen Mode** - Expand video for detailed viewing
- **Authentication** - Secure access to camera feeds

### Best Practices
- **Use Safari** for optimal streaming performance
- **Check Network** - Ensure stable internet connection
- **Close Unused Streams** - Free up bandwidth for other users
- **Monitor Quality** - Adjust settings if stream is choppy

---

## Settings Management

### Camera Settings
Configure individual camera parameters:
- **Exposure** - Adjust brightness and sensitivity
- **Focus** - Set focus distance and mode
- **Overlay** - Configure on-screen information
- **Network** - FTP and network configuration
- **Recording** - Event recording parameters

### Application Settings
Manage system-wide configuration:
- **Data Retention** - Set automatic cleanup policies
- **Storage Settings** - Configure file storage options
- **Notification Settings** - Email and alert preferences
- **System Preferences** - General application settings

### Data Retention Policy
- **Enable/Disable** - Toggle automatic data cleanup
- **Retention Period** - Set how long to keep events (days)
- **Server Only** - Policy applies to server-stored data only
- **Automatic Cleanup** - Old events are automatically deleted

---

## User Management

### Creating Users (Admin Only)
1. Navigate to **Settings** → **User Management**
2. Click "Add New User"
3. Fill in required information:
   - **Email** - User's email address
   - **Username** - Login username
   - **Full Name** - Display name
   - **Password** - Initial password
   - **Role** - Select appropriate permission level
4. Click "Create User"

### Managing Users
- **Edit User** - Update user information and roles
- **Activate/Deactivate** - Enable or disable user accounts
- **Reset Password** - Generate new login credentials
- **Delete User** - Remove user accounts (use with caution)

### Role Assignment
- **Admin** - Full system access
- **Manager** - Operational access with settings management
- **Viewer** - Read-only monitoring access

### Security Best Practices
- **Strong Passwords** - Use complex passwords for all accounts
- **Regular Updates** - Change passwords periodically
- **Role Principle** - Assign minimum necessary permissions
- **Account Monitoring** - Regularly review user access

---

## Troubleshooting

### Common Issues

#### **Can't Access Live Streams**
- Check camera connectivity
- Verify network settings
- Try refreshing the page
- Use Safari browser for best performance

#### **Events Not Appearing**
- Check FTP configuration
- Verify camera settings
- Ensure events are being triggered
- Check system logs for errors

#### **Dashboard Shows Wrong Numbers**
- Click "Refresh Stats" button
- Wait for auto-refresh (30 seconds)
- Check if events are properly filtered
- Verify no deleted events are being counted

#### **Can't Download Events**
- Check your user role permissions
- Verify file exists on server
- Check storage configuration
- Contact administrator if issue persists

#### **Settings Not Saving**
- Verify you have appropriate permissions
- Check for validation errors
- Refresh page and try again
- Contact administrator if problem continues

### Getting Help
- **Check Logs** - Review system logs for error details
- **Contact Admin** - Reach out to system administrator
- **Documentation** - Refer to this guide and API documentation
- **Support** - Contact technical support if needed

### System Requirements
- **Browser**: Modern web browser with JavaScript enabled
- **Network**: Stable internet connection
- **Permissions**: Appropriate user role for desired functions
- **Storage**: Sufficient disk space for event storage

---

## Quick Reference

### Keyboard Shortcuts
- **Refresh Page**: `F5` or `Ctrl+R` (Windows) / `Cmd+R` (Mac)
- **Hard Refresh**: `Ctrl+Shift+R` (Windows) / `Cmd+Shift+R` (Mac)
- **Full Screen**: `F11` (browser full screen)

### Important URLs
- **Application**: `http://localhost:3000` (or your server URL)
- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

### Default Settings
- **Admin Email**: `admin@s-imsy.com`
- **Default Password**: `admin123`
- **Session Timeout**: 30 minutes
- **Auto-refresh**: 30 seconds (dashboard)

---

*This user guide covers the essential features and operations of the PFCAM system. For technical details and API documentation, please refer to the API documentation at `/docs` endpoint.* 