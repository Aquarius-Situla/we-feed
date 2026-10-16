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
      const msg = data.message || data.detail || '请求失败';
      notifications.show({
        color: 'red',
        title: '错误',
        message: String(msg),
      });
      return Promise.reject(new Error(msg));
    }
    return data;
  },
  (error) => {
    if (error.response?.status === 401) {
      handleUnauthorized();
    } else {
      const msg =
        error.response?.data?.message ||
        error.response?.data?.detail?.message ||
        error.response?.data?.detail ||
        error.message ||
        '网络请求失败';
      notifications.show({
        color: 'red',
        title: '请求错误',
        message: String(msg),
      });
    }
    return Promise.reject(error);
  }
);

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
