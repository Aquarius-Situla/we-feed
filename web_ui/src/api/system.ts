import client from './client';

export interface SysInfoResponse {
  version?: string;
  core_version?: string;
  uptime?: number;
  python_version?: string;
  os?: {
    name?: string;
    version?: string;
    docker_version?: string;
    release?: string;
  } | string;
  system?: {
    node?: string;
    machine?: string;
    processor?: string;
  };
  article?: {
    all_count?: number;
    no_content_count?: number;
    has_content_count?: number;
  };
  queue?: {
    is_running?: boolean;
    pending_tasks?: number;
  };
}

export async function getSysInfo(): Promise<SysInfoResponse> {
  const res: any = await client.get('/sys/info');
  return res?.data || res || {};
}

export interface TagItem {
  id: string;
  name: string;
  cover?: string;
  intro?: string;
  status?: number;
  mps_id?: string;
  mps_list?: string[];
  mp_count?: number;
  article_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface TagPayload {
  name: string;
  cover?: string;
  intro?: string;
  status?: number;
  mps_id?: string | string[];
}

export async function listTags(): Promise<TagItem[]> {
  const res: any = await client.get('/tags');
  const items = Array.isArray(res) ? res : (res?.list || res?.data?.list || []);
  return Array.isArray(items) ? items : [];
}

export async function getTag(id: string): Promise<TagItem> {
  const res: any = await client.get(`/tags/${id}`);
  return res?.data || res;
}

export async function createTag(payload: TagPayload | string): Promise<any> {
  const body = typeof payload === 'string' ? { name: payload, mps_id: '[]' } : payload;
  return client.post('/tags', body);
}

export async function updateTag(id: string, payload: TagPayload): Promise<any> {
  return client.put(`/tags/${id}`, payload);
}

export async function deleteTag(id: string): Promise<any> {
  return client.delete(`/tags/${id}`);
}

export function getTagRssUrl(tagId: string, format: 'rss' | 'atom' | 'json' = 'rss'): string {
  const origin = window.location.origin;
  return `${origin}/feed/tag/${tagId}.${format}`;
}
