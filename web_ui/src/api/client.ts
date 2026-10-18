import axios from 'axios';
import { notifications } from '@mantine/notifications';

const rawBase = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '');
export const API_BASE = `${rawBase}/api/v1/wx`;

export const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token') || 'sso';
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

client.interceptors.response.use(
  (response) => {
    const data = response.data;
    // Standard response format: { code: 0, data: ... }
    if (data !== null && typeof data === 'object' && 'code' in data) {
      if (data.code === 0) {
        return data.data !== undefined ? data.data : data;
      }
      if (data.code === 401) {
        handleUnauthorized();
        return Promise.reject(new Error('登录已过期'));
      }
      const rawMsg = data.message || data.detail || '请求失败';
      const msg = formatErrorMessage(rawMsg);
      notifications.show({
        color: 'red',
        title: '错误',
        message: msg,
      });
      return Promise.reject(new Error(msg));
    }
    return data;
  },
  (error) => {
    if (error.response?.status === 401) {
      handleUnauthorized();
    } else {
      const rawMsg =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        error.message ||
        '网络请求失败';
      const msg = formatErrorMessage(rawMsg);
      notifications.show({
        color: 'red',
        title: '请求错误',
        message: msg,
      });
    }
    return Promise.reject(error);
  }
);

export function formatErrorMessage(err: any): string {
  if (!err) return '未知错误';
  if (typeof err === 'string') return err;
  if (typeof err.message === 'string') return err.message;
  if (typeof err.detail === 'string') return err.detail;
  if (Array.isArray(err)) {
    const msgs = err
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') {
          const loc = Array.isArray(item.loc)
            ? item.loc.filter((p: any) => p !== 'body' && p !== 'query').join('.')
            : '';
          const m = item.msg || item.message || JSON.stringify(item);
          return loc ? `${loc}: ${m}` : m;
        }
        return String(item);
      })
      .filter(Boolean);
    if (msgs.length > 0) return msgs.join('; ');
  }
  if (typeof err === 'object') {
    if (err.msg && typeof err.msg === 'string') return err.msg;
    if (err.detail) return formatErrorMessage(err.detail);
    try {
      return JSON.stringify(err);
    } catch {
      return String(err);
    }
  }
  return String(err);
}

function handleUnauthorized() {
  const currentToken = localStorage.getItem('token');
  if (currentToken === 'sso') {
    return;
  }
  localStorage.removeItem('token');
  if (window.location.pathname !== '/login') {
    window.location.href = '/login';
  }
}

export default client;
