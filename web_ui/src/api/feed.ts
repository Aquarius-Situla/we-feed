import client, { API_BASE } from './client';

export interface FeedItem {
  id: string;
  name: string;
  avatar?: string;
  mp_cover?: string;
  mp_intro?: string;
  article_count?: number;
  status: number; // 1: active, 0: disabled
  created_at?: string;
  updated_at?: string;
  tags?: { id: string; name: string }[];
}

export interface FeedListResponse {
  list: FeedItem[];
  total: number;
}

export async function getFeeds(params: {
  page?: number;
  pageSize?: number;
  kw?: string;
  tagId?: string;
  status?: number;
}): Promise<FeedListResponse> {
  const page = params.page || 1;
  const limit = params.pageSize || 24;
  const offset = (page - 1) * limit;
  const res: any = await client.get('/mps', {
    params: {
      limit,
      offset,
      kw: params.kw || undefined,
      tag_id: params.tagId || undefined,
      status: params.status !== undefined ? params.status : undefined,
    },
  });
  const list = res?.list || res?.data?.list || [];
  const total = res?.total ?? res?.data?.total ?? list.length;
  return {
    list: list.map((item: any) => ({
      id: item.id || item.mp_id,
      name: item.name || item.mp_name || '未命名公众号',
      avatar: item.avatar || item.mp_cover || '/static/logo.svg',
      mp_intro: item.mp_intro || item.intro || '',
      article_count: item.article_count || 0,
      status: item.status ?? 1,
      created_at: item.created_at,
      updated_at: item.updated_at,
      tags: Array.isArray(item.tags) ? item.tags : [],
    })),
    total,
  };
}

export async function addFeed(data: { name?: string; mp_name?: string; mp_id?: string; intro?: string; mp_intro?: string }): Promise<any> {
  const payload = {
    ...data,
    mp_name: data.mp_name || data.name,
    mp_intro: data.mp_intro || data.intro,
  };
  return client.post('/mps', payload);
}

export async function addFeedByArticle(url: string): Promise<any> {
  const cleanUrl = (url || '').trim();
  return client.post('/mps/by_article', { url: cleanUrl }, { params: { url: cleanUrl } });
}

export async function updateFeedStatus(mpId: string, status: number): Promise<any> {
  return client.put(`/mps/${mpId}`, { status }, { params: { status } });
}

export async function updateFeed(
  mpId: string,
  data: {
    name?: string;
    mp_name?: string;
    intro?: string;
    mp_intro?: string;
    status?: number;
    avatar?: string;
    mp_cover?: string;
  }
): Promise<any> {
  const payload = {
    ...data,
    mp_name: data.mp_name || data.name,
    mp_intro: data.mp_intro || data.intro,
  };
  return client.put(`/mps/${mpId}`, payload);
}

export async function deleteFeed(mpId: string): Promise<any> {
  return client.delete(`/mps/${mpId}`);
}

export async function refreshFeed(mpId: string): Promise<any> {
  return client.get(`/mps/update/${mpId}`);
}

export function getRssUrl(feedId?: string, format: 'rss' | 'atom' | 'json' = 'rss'): string {
  const origin = window.location.origin;
  if (!feedId) {
    return `${origin}/feed/all.${format}`;
  }
  return `${origin}/feed/${feedId}.${format}`;
}
