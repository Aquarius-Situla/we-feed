import client from './client';

export interface ArticleItem {
  id: string;
  mp_id: string;
  mp_name?: string;
  title: string;
  pic_url?: string;
  url: string;
  description?: string;
  publish_time?: number;
  created_at?: string;
  has_content?: number;
  is_read?: number;
  content_html?: string;
  content?: string;
}

export interface ArticleListResponse {
  list: ArticleItem[];
  total: number;
}

export async function getArticles(params: {
  page?: number;
  pageSize?: number;
  mp_id?: string;
  kw?: string;
  has_content?: number;
  is_read?: number;
}): Promise<ArticleListResponse> {
  const res: any = await client.get('/articles', { params });
  return {
    list: res?.list || res?.data || [],
    total: res?.total || 0,
  };
}

export async function getArticleDetail(id: string, fetchContent: number = 0): Promise<ArticleItem> {
  const res: any = await client.get(`/articles/${id}`, { params: { fetch_content: fetchContent } });
  return res?.data || res;
}

export async function deleteArticle(id: string): Promise<any> {
  return client.delete(`/articles/${id}`);
}

export async function markArticleRead(id: string, isRead: boolean = true): Promise<any> {
  return client.put(`/articles/${id}/read`, null, { params: { is_read: isRead ? 1 : 0 } });
}

export async function refreshArticle(id: string): Promise<any> {
  return client.post(`/articles/${id}/refresh`);
}
