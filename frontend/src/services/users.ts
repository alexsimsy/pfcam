import { getToken } from './auth';

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  role: 'admin' | 'manager' | 'viewer';
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface UserCreate {
  email: string;
  username: string;
  password: string;
  full_name: string;
  role?: 'admin' | 'manager' | 'viewer';
}

export interface UserUpdate {
  email?: string;
  username?: string;
  full_name?: string;
  role?: 'admin' | 'manager' | 'viewer';
  is_active?: boolean;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

function getAuthHeaders() {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
}

export async function fetchUsers(): Promise<User[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/users/`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch users');
  return res.json();
}

export async function createUser(data: UserCreate): Promise<User> {
  const res = await fetch(`${API_BASE_URL}/api/v1/users/`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function updateUser(userId: number, data: UserUpdate): Promise<User> {
  const res = await fetch(`${API_BASE_URL}/api/v1/users/${userId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteUser(userId: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/users/${userId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function activateUser(userId: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/users/${userId}/activate`, {
    method: 'PUT',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function deactivateUser(userId: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/users/${userId}/deactivate`, {
    method: 'PUT',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error(await res.text());
} 