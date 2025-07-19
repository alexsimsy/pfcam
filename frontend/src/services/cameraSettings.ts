import { getToken } from './auth';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

function getAuthHeaders() {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
}

export interface CameraSettings {
  live_quality_level?: number;
  recording_quality_level?: number;
  heater_level?: number;
  picture_rotation?: number;
  recording_seconds_pre_event?: number;
  recording_seconds_post_event?: number;
  rtsp_quality_level?: number;
}

export interface SettingsResponse {
  camera_id: number;
  settings: CameraSettings;
  version: string;
}

export async function fetchCameraSettings(cameraId: number): Promise<SettingsResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/settings/${cameraId}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch camera settings');
  return res.json();
}

export async function updateCameraSettings(cameraId: number, settings: Partial<CameraSettings>): Promise<SettingsResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/settings/${cameraId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(settings),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchAllCamerasSettings(): Promise<Record<string, CameraSettings>> {
  const res = await fetch(`${API_BASE_URL}/api/v1/settings/cameras/all`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch all cameras settings');
  return res.json();
}

export async function resetCameraSettings(cameraId: number): Promise<SettingsResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/settings/${cameraId}/reset`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
} 