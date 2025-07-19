import { getToken } from './auth';

export interface DashboardStats {
  cameras: {
    total: number;
    online: number;
    offline: number;
  };
  events: {
    total: number;
    last_24h: number;
    unviewed: number;
  };
  events_by_tag: Array<{
    tag_name: string;
    tag_color: string;
    count: number;
  }>;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

function getAuthHeaders() {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
}

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/stats`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch dashboard stats');
  }
  return response.json();
} 