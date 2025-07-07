import { getToken } from './auth';

export interface Camera {
  id: number;
  name: string;
  ip_address: string;
  port: number;
  base_url: string;
  username?: string;
  use_ssl: boolean;
  model?: string;
  firmware_version?: string;
  serial_number?: string;
  is_active: boolean;
  is_online: boolean;
  last_seen?: string;
  created_at: string;
  updated_at?: string;
}

export interface CameraCreate {
  name: string;
  ip_address: string;
  port: number;
  base_url: string;
  username?: string;
  password?: string;
  use_ssl: boolean;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

function getAuthHeaders() {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
}

export async function fetchCameras(): Promise<Camera[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/cameras/`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch cameras');
  return res.json();
}

export async function createCamera(data: CameraCreate): Promise<Camera> {
  const res = await fetch(`${API_BASE_URL}/api/v1/cameras/`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function updateCameraSystemSettings(cameraId: number, settings: any): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/settings/${cameraId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(settings),
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function triggerEvent(
  cameraId: number,
  preEventSeconds: number = 10,
  postEventSeconds: number = 10,
  eventName: string = "string",
  overlayText: string = "string",
  postEventUnlimited: boolean = true,
  stopOtherEvents: string = "none"
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/cameras/${cameraId}/trigger-event`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      pre_event_seconds: preEventSeconds,
      post_event_seconds: postEventSeconds,
      event_name: eventName,
      overlay_text: overlayText,
      post_event_unlimited: postEventUnlimited,
      stop_other_events: stopOtherEvents
    }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
} 