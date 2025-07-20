import { getToken } from './auth';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

function getAuthHeaders() {
  const token = getToken();
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
}

export interface NotificationPreferences {
  email_notifications: boolean;
  webhook_url?: string;
  event_notifications: boolean;
  camera_status_notifications: boolean;
  system_alerts: boolean;
}

export interface NotificationPreferencesUpdate {
  email_notifications?: boolean;
  webhook_url?: string;
  event_notifications?: boolean;
  camera_status_notifications?: boolean;
  system_alerts?: boolean;
}

export interface NotificationStatus {
  websocket_connected: boolean;
  email_enabled: boolean;
  webhook_configured: boolean;
  active_connections: number;
}

export interface TestEmailResponse {
  message: string;
}

// Get notification preferences
export async function getNotificationPreferences(): Promise<NotificationPreferences> {
  const response = await fetch(`${API_BASE_URL}/api/v1/notifications/preferences`, {
    headers: getAuthHeaders(),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to get notification preferences: ${response.statusText}`);
  }
  
  return response.json();
}

// Update notification preferences
export async function updateNotificationPreferences(
  preferences: NotificationPreferencesUpdate
): Promise<NotificationPreferences> {
  const response = await fetch(`${API_BASE_URL}/api/v1/notifications/preferences`, {
    method: 'PUT',
    headers: {
      ...getAuthHeaders(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(preferences),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to update notification preferences: ${response.statusText}`);
  }
  
  return response.json();
}

// Get notification status
export async function getNotificationStatus(): Promise<NotificationStatus> {
  const response = await fetch(`${API_BASE_URL}/api/v1/notifications/status`, {
    headers: getAuthHeaders(),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to get notification status: ${response.statusText}`);
  }
  
  return response.json();
}

// Send test email
export async function sendTestEmail(): Promise<TestEmailResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/notifications/test-email`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to send test email: ${response.statusText}`);
  }
  
  return response.json();
} 