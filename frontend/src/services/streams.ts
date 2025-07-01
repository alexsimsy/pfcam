import { getToken } from './auth';

export interface StreamInfo {
  name: string;
  codec: string;
  fps: number;
  resolution: {
    width: number;
    height: number;
  };
  url: {
    absolute: string;
    relative?: string;
  };
  snapshot?: {
    url: {
      absolute: string;
      relative?: string;
    };
  };
}

export interface StreamResponse {
  name: string;
  stream_info: StreamInfo;
  camera_id: number;
}

export interface StreamList {
  camera_id: number;
  streams: StreamResponse[];
  count: number;
}

export interface SnapshotResponse {
  camera_id: number;
  stream_name: string;
  snapshot_url: string;
  resolution: {
    width: number;
    height: number;
  };
}

export interface SnapshotListItem {
  id: number;
  filename: string;
  taken_at: string;
  download_url: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function getAuthHeaders() {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
}

export async function fetchCameraStreams(cameraId: number): Promise<StreamList> {
  const res = await fetch(`${API_BASE_URL}/v1/streams/${cameraId}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch camera streams');
  return res.json();
}

export async function getStreamSnapshot(cameraId: number, streamName: string): Promise<SnapshotResponse> {
  const res = await fetch(`${API_BASE_URL}/v1/streams/${cameraId}/${streamName}/snapshot`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to get stream snapshot');
  return res.json();
}

export async function getStreamUrl(cameraId: number, streamName: string): Promise<{
  camera_id: number;
  stream_name: string;
  stream_url: string;
  codec: string;
  fps: number;
  resolution: { width: number; height: number };
}> {
  const res = await fetch(`${API_BASE_URL}/v1/streams/${cameraId}/${streamName}/url`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to get stream URL');
  return res.json();
}

export async function listSnapshots(cameraId: number): Promise<SnapshotListItem[]> {
  const url = `${API_BASE_URL}/v1/streams/snapshots/${cameraId}`;
  console.log('Fetching snapshots from:', url);
  const res = await fetch(url, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch snapshots');
  return res.json();
}

export function getSnapshotDownloadUrl(snapshotId: number): string {
  return `${API_BASE_URL}/v1/streams/snapshots/${snapshotId}/download`;
}

export async function deleteSnapshot(snapshotId: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/v1/streams/snapshots/${snapshotId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to delete snapshot');
} 