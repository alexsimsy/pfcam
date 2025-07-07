import { getToken } from './auth';

export interface Event {
  id: number;
  camera_id: number;
  filename: string;
  event_name?: string;
  triggered_at: string;
  file_size?: number;
  is_downloaded: boolean;
  is_processed: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at?: string;
  camera_name?: string;
}

export interface EventListResponse {
  events: Event[];
  total: number;
  limit: number;
  offset: number;
}

export interface EventFilters {
  cameraId?: number;
  startDate?: string;
  endDate?: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

function getAuthHeaders() {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
}

export async function fetchEvents(params: any = {}) {
  const query = new URLSearchParams(params).toString();
  const response = await fetch(`${API_BASE_URL}/api/v1/events/${query ? `?${query}` : ''}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch events');
  }
  return response.json();
}

export async function syncEvents(cameraId?: number): Promise<any> {
  const params = cameraId ? `?camera_id=${cameraId}` : '';
  const res = await fetch(`${API_BASE_URL}/api/v1/events/sync${params}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to sync events');
  return res.json();
}

export async function downloadEvent(eventId: number): Promise<void> {
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}/api/v1/events/${eventId}/download`, {
    headers: {
      ...(token && { 'Authorization': `Bearer ${token}` }),
    },
  });
  if (!res.ok) throw new Error('Failed to download event');
  // Get filename from Content-Disposition header
  const disposition = res.headers.get('Content-Disposition');
  let filename = `event_${eventId}`;
  if (disposition) {
    const match = disposition.match(/filename="?([^";]+)"?/);
    if (match) filename = match[1];
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function playEvent(eventId: number): Promise<string> {
  // Returns the URL to stream the video for playback
  return `${API_BASE_URL}/api/v1/events/${eventId}/play`;
}

export async function deleteEventLocal(eventId: number): Promise<void> {
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}/api/v1/events/${eventId}/local`, {
    method: 'DELETE',
    headers: {
      ...(token && { 'Authorization': `Bearer ${token}` }),
    },
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function deleteEventFromCamera(eventId: number): Promise<void> {
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}/api/v1/events/${eventId}`, {
    method: 'DELETE',
    headers: {
      ...(token && { 'Authorization': `Bearer ${token}` }),
    },
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function getEventSyncStatus(eventId: number): Promise<{on_server: boolean, on_camera: boolean}> {
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}/api/v1/events/${eventId}/sync-status`, {
    headers: {
      ...(token && { 'Authorization': `Bearer ${token}` }),
    },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function refreshEventSyncStatus(eventId: number): Promise<{on_server: boolean}> {
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}/api/v1/events/${eventId}/refresh`, {
    headers: {
      ...(token && { 'Authorization': `Bearer ${token}` }),
    },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
} 