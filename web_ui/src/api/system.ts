import client from './client';

export interface SysInfoResponse {
  version?: string;
  uptime?: string;
  python?: string;
  os?: string;
  database?: {
    articles_count?: number;
    feeds_count?: number;
    size?: string;
  };
  wx?: {
    login?: boolean;
    info?: any;
  };
}

export async function getSysInfo(): Promise<SysInfoResponse> {
  const res: any = await client.get('/sys/info');
  return res?.data || res;
}

export interface TagItem {
  id: string;
  name: string;
  color?: string;
  count?: number;
}

export async function listTags(): Promise<TagItem[]> {
  const res: any = await client.get('/tags');
  return res?.data || res || [];
}

export async function createTag(name: string, color?: string): Promise<any> {
  return client.post('/tags', { name, color });
}

export async function deleteTag(id: string): Promise<any> {
  return client.delete(`/tags/${id}`);
}
