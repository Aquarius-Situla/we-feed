import React, { useEffect, useState } from 'react';
import {
  Stack,
  Paper,
  Title,
  Text,
  Group,
  Button,
  Badge,
  SimpleGrid,
  Card,
  Avatar,
  ActionIcon,
  Tooltip,
  Loader,
  Alert,
} from '@mantine/core';
import {
  IconPlus,
  IconRefresh,
  IconTrash,
  IconCheck,
  IconAlertCircle,
  IconBook,
  IconPlugConnected,
} from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import {
  getWereadStatus,
  testWereadConnection,
  clearWereadCookie,
  WereadStatusResponse,
  WereadAccount,
} from '../api/weread';
import WereadAuthModal from '../components/WereadAuthModal';

export function WeReadPage() {
  const [status, setStatus] = useState<WereadStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [testing, setTesting] = useState<boolean>(false);
  const [authModalOpen, setAuthModalOpen] = useState<boolean>(false);

  const fetchStatus = async (check = false) => {
    setLoading(true);
    try {
      const data = await getWereadStatus(check);
      setStatus(data);
    } catch {
      // error handled
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleTestConnection = async () => {
    setTesting(true);
    try {
      const res = await testWereadConnection();
      notifications.show({
        color: 'teal',
        title: '测试连通性成功',
        message: res?.message || '微信读书接口与 Cookie 有效！',
      });
      await fetchStatus(true);
      window.dispatchEvent(new CustomEvent('weread-status-updated'));
    } catch (err: any) {
      notifications.show({
        color: 'red',
        title: '测试连接失败',
        message: err?.message || 'Cookie 已失效或连接超时',
      });
      await fetchStatus(true);
      window.dispatchEvent(new CustomEvent('weread-status-updated'));
    } finally {
      setTesting(false);
    }
  };

  const handleDeleteAccount = async (account: WereadAccount) => {
    if (!window.confirm(`确定要解除绑定微信读书账号 VID: ${account.vid} 吗？`)) return;
    try {
      await clearWereadCookie(account.vid);
      notifications.show({ color: 'teal', message: '已成功移除该微信读书账号' });
      fetchStatus(true);
      window.dispatchEvent(new CustomEvent('weread-status-updated'));
    } catch {
      // error handled
    }
  };

  return (
    <Stack gap="lg">
      <Paper p="lg" radius="md" withBorder>
        <Group justify="space-between" wrap="wrap">
          <Stack gap={4}>
            <Title order={2} size="h3">
              微信读书多账号与保活管理
            </Title>
            <Text size="sm" c="dimmed">
              支持多微信号绑定轮转与自动保活，当主账号额度耗尽时自动故障转移至备用账号，保证文章抓取永不中断。
            </Text>
          </Stack>

          <Group gap="sm">
            <Button
              variant="default"
              leftSection={<IconPlugConnected size={16} />}
              loading={testing}
              onClick={handleTestConnection}
            >
              测试连接
            </Button>
            <Button
              variant="filled"
              color="blue"
              leftSection={<IconPlus size={16} />}
              onClick={() => setAuthModalOpen(true)}
            >
              扫码添加账号
            </Button>
          </Group>
        </Group>
      </Paper>

      {/* Main Status & Accounts */}
      {loading ? (
        <Stack align="center" justify="center" h={200}>
          <Loader size="lg" />
        </Stack>
      ) : (
        <Stack gap="md">
          {status?.configured ? (
            status?.expired ? (
              <Alert
                icon={<IconAlertCircle size={18} />}
                title="微信读书登录凭据已失效"
                color="red"
                radius="md"
              >
                当前微信读书账号凭据已过期（微信读书提示登录超时），公众号文章抓取已暂停。请点击右上角“扫码添加账号”重新扫码登录以恢复。
              </Alert>
            ) : (
              <Alert
                icon={<IconCheck size={18} />}
                title="微信读书通道运行正常"
                color="teal"
                radius="md"
              >
                已配置可用凭据，容器内置自动保活服务正在持续守护 Cookie 有效性。
              </Alert>
            )
          ) : (
            <Alert
              icon={<IconAlertCircle size={18} />}
              title="尚未配置微信读书账号"
              color="orange"
              radius="md"
            >
              微信读书通道目前处于未授权状态，请点击右上角“扫码添加账号”绑定您的微信号以开启高清抓取通道。
            </Alert>
          )}

          <Title order={3} size="h4" mt="sm">
            已绑定账号列表
          </Title>

          {status?.accounts && status.accounts.length > 0 ? (
            <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="md">
              {status.accounts.map((acc) => (
                <Card key={acc.vid} shadow="sm" padding="md" radius="md" withBorder>
                  <Group justify="space-between" align="flex-start">
                    <Group gap="sm">
                      <Avatar src={acc.avatar} radius="xl" size="md">
                        <IconBook size={20} />
                      </Avatar>
                      <Stack gap={2}>
                        <Text fw={600} size="sm">
                          {acc.name || `用户 VID: ${acc.vid}`}
                        </Text>
                        <Text size="xs" c="dimmed">
                          VID: {acc.vid}
                        </Text>
                      </Stack>
                    </Group>

                    <Tooltip label="解除绑定">
                      <ActionIcon
                        variant="subtle"
                        color="red"
                        size="sm"
                        onClick={() => handleDeleteAccount(acc)}
                      >
                        <IconTrash size={16} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>

                  <Group mt="md" gap="xs">
                    <Badge size="xs" variant="light" color={acc.expired ? 'red' : 'teal'}>
                      {acc.expired ? '凭据已过期' : '凭据有效'}
                    </Badge>
                    <Badge
                      size="xs"
                      variant="light"
                      color={acc.quota_exhausted ? 'orange' : 'blue'}
                    >
                      {acc.quota_exhausted ? '今日配额已耗尽' : '额度充足'}
                    </Badge>
                  </Group>
                </Card>
              ))}
            </SimpleGrid>
          ) : status?.vid ? (
            <Card shadow="sm" padding="md" radius="md" withBorder>
              <Group justify="space-between">
                <Group gap="sm">
                  <Avatar radius="xl" size="md">
                    <IconBook size={20} />
                  </Avatar>
                  <Stack gap={2}>
                    <Text fw={600} size="sm">
                      主账号 (VID: {status.vid})
                    </Text>
                    <Text size="xs" c="dimmed">
                      {status.name || '默认绑定凭据'}
                    </Text>
                  </Stack>
                </Group>
                <Badge size="xs" variant="light" color="teal">
                  有效运行中
                </Badge>
              </Group>
            </Card>
          ) : (
            <Paper p="xl" radius="md" withBorder style={{ textAlign: 'center' }}>
              <Text c="dimmed">暂无绑定账号，请点击上方“扫码添加账号”完成绑定。</Text>
            </Paper>
          )}
        </Stack>
      )}

      {/* Auth Modal */}
      <WereadAuthModal
        opened={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onSuccess={() => fetchStatus(true)}
      />
    </Stack>
  );
}

export default WeReadPage;
