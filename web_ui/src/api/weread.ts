import client from './client';

export interface WereadAccount {
  vid: string;
  name?: string;
  avatar?: string;
  expired?: boolean;
  quota_exhausted?: boolean;
  error_msg?: string;
}

export interface WereadStatusResponse {
  configured: boolean;
  valid?: boolean;
  expired?: boolean;
  error_msg?: string;
  vid?: string;
  name?: string;
  accounts?: WereadAccount[];
  cookie_refresh_url?: string;
  browser_path?: string;
}

export async function getWereadStatus(check = false): Promise<WereadStatusResponse> {
  const res: any = await client.get('/weread', { params: { check } });
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
