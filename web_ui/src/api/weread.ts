import client from './client';

export interface WereadAccount {
  vid: string;
  name?: string;
  avatar?: string;
  expired?: boolean;
  quota_exhausted?: boolean;
}

export interface WereadStatusResponse {
  configured: boolean;
  vid?: string;
  name?: string;
  accounts?: WereadAccount[];
  cookie_refresh_url?: string;
  browser_path?: string;
}

export async function getWereadStatus(): Promise<WereadStatusResponse> {
  const res: any = await client.get('/weread');
  return res?.data || res;
}

export async function getWereadQrCode(): Promise<any> {
  const res: any = await client.get('/weread/qr/code');
  return res?.data || res;
}

export async function checkWereadQrStatus(): Promise<any> {
  const res: any = await client.get('/weread/qr/status');
  return res?.data || res;
}

export async function testWereadConnection(): Promise<any> {
  const res: any = await client.post('/weread/test');
  return res?.data || res;
}

export async function clearWereadCookie(vid?: string): Promise<any> {
  return client.delete('/weread/cookie', { params: { vid } });
}
