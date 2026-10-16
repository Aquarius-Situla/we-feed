import client from './client';

export interface AccessKeyItem {
  id: string;
  key: string;
  secret?: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  expires_at?: string;
  last_used_at?: string;
}

export async function listAccessKeys(): Promise<AccessKeyItem[]> {
  const res: any = await client.get('/auth/ak/list');
  return res?.data || res || [];
}

export async function createAccessKey(data: {
  name: string;
  description?: string;
  expires_in_days?: number | null;
}): Promise<AccessKeyItem> {
  const res: any = await client.post('/auth/ak/create', data);
  return res?.data || res;
}

export async function deleteAccessKey(id: string): Promise<any> {
  return client.delete(`/auth/ak/${id}`);
}
