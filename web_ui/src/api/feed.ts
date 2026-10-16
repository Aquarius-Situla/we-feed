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
}

export interface FeedListResponse {
  list: FeedItem[];
  total: number;
}

export async function getFeeds(params: {
  page?: number;
  pageSize?: number;
  kw?: string;
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
    })),
    total,
  };
}

export async function addFeed(data: { name: string; mp_id?: string; intro?: string }): Promise<any> {
  return client.post('/mps', data);
}

export async function addFeedByArticle(url: string): Promise<any> {
  return client.post('/mps/by_article', { url });
}

export async function updateFeedStatus(mpId: string, status: number): Promise<any> {
  return client.put(`/mps/${mpId}`, null, { params: { status } });
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
