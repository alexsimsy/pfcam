import { getToken } from './auth';

export interface Tag {
  id: number;
  name: string;
  color: string;
  description?: string;
  created_at: string;
  updated_at?: string;
}

export interface TagListResponse {
  tags: Tag[];
  total: number;
}

export interface TagUsage {
  tag: Tag;
  usage_count: number;
}

export interface EventTagAssignment {
  event_id: number;
  tag_ids: number[];
}

function getAuthHeaders() {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
}

export async function fetchTags(params: any = {}) {
  const query = new URLSearchParams(params).toString();
  const url = `/api/v1/tags/${query ? `?${query}` : ''}`;
  const response = await fetch(url, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch tags');
  }
  return response.json();
}

export async function createTag(tagData: { name: string; color?: string; description?: string }) {
  const url = `/api/v1/tags/`;
  const response = await fetch(url, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(tagData),
  });
  if (!response.ok) {
    throw new Error('Failed to create tag');
  }
  return response.json();
}

export async function updateTag(tagId: number, tagData: { name?: string; color?: string; description?: string }) {
  const url = `/api/v1/tags/${tagId}`;
  const response = await fetch(url, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(tagData),
  });
  if (!response.ok) {
    throw new Error('Failed to update tag');
  }
  return response.json();
}

export async function deleteTag(tagId: number) {
  const url = `/api/v1/tags/${tagId}`;
  const response = await fetch(url, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to delete tag');
  }
  return response.json();
}

export async function assignTagsToEvent(eventId: number, tagIds: number[]) {
  const url = `/api/v1/tags/assign`;
  console.log('assignTagsToEvent called with:', { eventId, tagIds, url });
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ event_id: eventId, tag_ids: tagIds }),
    });
    
    console.log('assignTagsToEvent response status:', response.status);
    console.log('assignTagsToEvent response headers:', Object.fromEntries(response.headers.entries()));
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('assignTagsToEvent error response:', errorText);
      throw new Error(`Failed to assign tags to event: ${errorText}`);
    }
    
    const result = await response.json();
    console.log('assignTagsToEvent success result:', result);
    return result;
  } catch (error) {
    console.error('assignTagsToEvent caught error:', error);
    throw error;
  }
}

export async function getTagUsageStats(): Promise<TagUsage[]> {
  const url = `/api/v1/tags/usage/stats`;
  const response = await fetch(url, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch tag usage stats');
  }
  return response.json();
} 