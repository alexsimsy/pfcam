export interface ApplicationSettings {
  id: number;
  auto_start_streams: boolean;
  stream_quality: 'low' | 'medium' | 'high';
  store_data_on_camera: boolean;
  auto_download_events: boolean;
  auto_download_snapshots: boolean;
  event_retention_days: number;
  snapshot_retention_days: number;
  mobile_data_saving: boolean;
  low_bandwidth_mode: boolean;
  created_at: string;
  updated_at?: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL;

export async function fetchApplicationSettings(): Promise<ApplicationSettings> {
  const response = await fetch(`${API_BASE_URL}/v1/settings/application/settings`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch settings: ${response.statusText}`);
  }

  return response.json();
}

export async function updateApplicationSettings(updates: Partial<ApplicationSettings>): Promise<ApplicationSettings> {
  const response = await fetch(`${API_BASE_URL}/api/v1/settings/application/settings`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    throw new Error(`Failed to update settings: ${response.statusText}`);
  }

  return response.json();
}

export async function resetApplicationSettings(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/settings/application/settings/reset`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to reset settings: ${response.statusText}`);
  }
} 