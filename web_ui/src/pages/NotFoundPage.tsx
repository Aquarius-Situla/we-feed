import React from 'react';
import { Container, Title, Text, Button, Group } from '@mantine/core';
import { useNavigate } from 'react-router-dom';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <Container size="sm" py={80} style={{ textAlign: 'center' }}>
      <Title order={1} size={64} fw={900} c="dimmed">
        404
      </Title>
      <Title order={2} mt="md">
        页面未找到
      </Title>
      <Text c="dimmed" size="sm" mt="sm">
        您访问的页面不存在或已被移除。
      </Text>
      <Group justify="center" mt="xl">
        <Button variant="light" onClick={() => navigate('/')}>
          返回首页
        </Button>
      </Group>
    </Container>
  );
}

export default NotFoundPage;
