import client from './client';

export interface LoginParams {
  username: string;
  password: string;
}

export interface UserInfo {
  id?: string;
  username: string;
  avatar?: string;
  role?: string;
}

export async function login(data: LoginParams): Promise<any> {
  const formData = new URLSearchParams();
  formData.append('username', data.username);
  formData.append('password', data.password);
  const res: any = await client.post('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  if (res?.access_token) {
    localStorage.setItem('token', res.access_token);
  }
  return res;
}

export async function getCurrentUser(): Promise<UserInfo> {
  const res: any = await client.get('/user');
  return res?.data || res || { username: 'Admin' };
}

export async function logout(): Promise<void> {
  try {
    await client.post('/auth/logout');
  } finally {
    localStorage.removeItem('token');
  }
}

export async function getWechatQrCode(): Promise<any> {
  const res: any = await client.get('/auth/qr/code');
  return res?.data || res;
}

export async function checkWechatQrStatus(): Promise<any> {
  const res: any = await client.get('/auth/qr/status');
  return res?.data || res;
}