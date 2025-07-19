import { getToken } from './auth';

import type { Tag } from './tags';

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
  is_orphaned?: boolean;
  is_played?: boolean;
  created_at: string;
  updated_at?: string;
  camera_name?: string;
  tags: Tag[];
  
  // Computed properties (will be added by backend)
  event_id?: string;
  display_name?: string;
  status_summary?: {
    on_camera: boolean;
    downloaded: boolean;
    played: boolean;
    processed: boolean;
  };
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

export async function fetchOrphanedEvents(params: any = {}) {
  const query = new URLSearchParams(params).toString();
  const response = await fetch(`${API_BASE_URL}/api/v1/events/orphaned${query ? `?${query}` : ''}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch orphaned events');
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
  const url = `${API_BASE_URL}/api/v1/events/${eventId}/download`;
  
  console.log('Downloading event:', { eventId, url });
  
  const res = await fetch(url, {
    headers: {
      ...(token && { 'Authorization': `Bearer ${token}` }),
    },
  });
  
  console.log('Download response status:', res.status);
  console.log('Download response headers:', Object.fromEntries(res.headers.entries()));
  
  if (!res.ok) {
    const errorText = await res.text();
    console.error('Download failed:', { status: res.status, error: errorText });
    throw new Error(`Failed to download event: ${res.status} ${errorText}`);
  }
  
  // Get filename from Content-Disposition header
  const disposition = res.headers.get('Content-Disposition');
  let filename = `event_${eventId}`;
  if (disposition) {
    const match = disposition.match(/filename="?([^";]+)"?/);
    if (match) filename = match[1];
  }
  
  console.log('Downloading file:', filename);
  
  const blob = await res.blob();
  console.log('Download blob size:', blob.size);
  
  const url2 = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url2;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url2);
  
  console.log('Download completed successfully');
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