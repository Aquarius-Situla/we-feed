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
  color?: string;
  count?: number;
}

export async function listTags(): Promise<TagItem[]> {
  const res: any = await client.get('/tags');
  const items = Array.isArray(res) ? res : (res?.list || res?.data?.list || []);
  return Array.isArray(items) ? items : [];
}

export async function createTag(name: string, color?: string): Promise<any> {
  return client.post('/tags', { name, color });
}

export async function deleteTag(id: string): Promise<any> {
  return client.delete(`/tags/${id}`);
}
