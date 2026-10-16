import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Title,
  Text,
  TextInput,
  PasswordInput,
  Button,
  Stack,
  Image,
  Group,
} from '@mantine/core';
import { useNavigate } from 'react-router-dom';
import { notifications } from '@mantine/notifications';
import { login } from '../api/auth';

export function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    // If token exists, direct redirect to home
    const token = localStorage.getItem('token');
    if (token) {
      navigate('/', { replace: true });
    }
  }, [navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;
    setLoading(true);
    try {
      await login({ username, password });
      notifications.show({ color: 'teal', message: '登录成功' });
      navigate('/', { replace: true });
    } catch {
      // error handled
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container size={420} my={80}>
      <Paper withBorder shadow="md" p={30} radius="md">
        <Stack align="center" mb="lg">
          <Image src="/static/logo.svg" w={56} h={56} fallbackSrc="/static/logo.svg" />
          <Title order={2} size="h3">
            登录 WeFeed
          </Title>
          <Text c="dimmed" size="xs">
            微信公众号与微信读书 RSS 聚合管理
          </Text>
        </Stack>

        <form onSubmit={handleSubmit}>
          <Stack gap="md">
            <TextInput
              label="用户名"
              placeholder="请输入管理员用户名"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <PasswordInput
              label="密码"
              placeholder="请输入密码"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <Button type="submit" fullWidth mt="md" loading={loading} color="blue">
              登 录
            </Button>
          </Stack>
        </form>

        <Group justify="center" mt="xl">
          <Text size="xs" c="dimmed">
            © 2026 Situla · WeFeed Community
          </Text>
        </Group>
      </Paper>
    </Container>
  );
}

export default LoginPage;
