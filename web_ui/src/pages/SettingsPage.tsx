import React, { useEffect, useState } from 'react';
import {
  Stack,
  Paper,
  Title,
  Text,
  Tabs,
  Group,
  Button,
  Table,
  Badge,
  ActionIcon,
  Modal,
  TextInput,
  NumberInput,
  Tooltip,
  SimpleGrid,
  Card,
  Loader,
} from '@mantine/core';
import {
  IconKey,
  IconTag,
  IconInfoCircle,
  IconPlus,
  IconTrash,
  IconCopy,
} from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import {
  listAccessKeys,
  createAccessKey,
  deleteAccessKey,
  AccessKeyItem,
} from '../api/accessKey';
import { listTags, createTag, deleteTag, TagItem, getSysInfo, SysInfoResponse } from '../api/system';
import dayjs from 'dayjs';

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<string | null>('keys');

  // Access Keys
  const [keys, setKeys] = useState<AccessKeyItem[]>([]);
  const [keysLoading, setKeysLoading] = useState<boolean>(false);
  const [createKeyModalOpen, setCreateKeyModalOpen] = useState<boolean>(false);
  const [keyName, setKeyName] = useState<string>('');
  const [keyExpires, setKeyExpires] = useState<number | string>(365);
  const [creatingKey, setCreatingKey] = useState<boolean>(false);

  // Tags
  const [tags, setTags] = useState<TagItem[]>([]);
  const [tagsLoading, setTagsLoading] = useState<boolean>(false);
  const [tagName, setTagName] = useState<string>('');
  const [creatingTag, setCreatingTag] = useState<boolean>(false);

  // SysInfo
  const [sysInfo, setSysInfo] = useState<SysInfoResponse | null>(null);
  const [sysLoading, setSysLoading] = useState<boolean>(false);

  const fetchKeys = async () => {
    setKeysLoading(true);
    try {
      const data = await listAccessKeys();
      setKeys(data);
    } catch {
      // error handled
    } finally {
      setKeysLoading(false);
    }
  };

  const fetchTags = async () => {
    setTagsLoading(true);
    try {
      const data = await listTags();
      setTags(data);
    } catch {
      // error handled
    } finally {
      setTagsLoading(false);
    }
  };

  const fetchSysInfo = async () => {
    setSysLoading(true);
    try {
      const data = await getSysInfo();
      setSysInfo(data);
    } catch {
      // error handled
    } finally {
      setSysLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'keys') fetchKeys();
    if (activeTab === 'tags') fetchTags();
    if (activeTab === 'info') fetchSysInfo();
  }, [activeTab]);

  const handleCreateKey = async () => {
    if (!keyName.trim()) return;
    setCreatingKey(true);
    try {
      await createAccessKey({
        name: keyName.trim(),
        expires_in_days: typeof keyExpires === 'number' ? keyExpires : 365,
      });
      notifications.show({ color: 'teal', message: 'Access Key 创建成功！' });
      setCreateKeyModalOpen(false);
      setKeyName('');
      fetchKeys();
    } catch {
      // error handled
    } finally {
      setCreatingKey(false);
    }
  };

  const handleDeleteKey = async (id: string) => {
    if (!window.confirm('确定要删除该 Access Key 吗？关联的 RSS 客户端将无法认证。')) return;
    try {
      await deleteAccessKey(id);
      notifications.show({ color: 'teal', message: 'Access Key 已删除' });
      fetchKeys();
    } catch {
      // error handled
    }
  };

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    notifications.show({ color: 'blue', message: `${label} 已复制到剪贴板！` });
  };

  const handleCreateTag = async () => {
    if (!tagName.trim()) return;
    setCreatingTag(true);
    try {
      await createTag(tagName.trim());
      notifications.show({ color: 'teal', message: '标签创建成功' });
      setTagName('');
      fetchTags();
    } catch {
      // error handled
    } finally {
      setCreatingTag(false);
    }
  };

  const handleDeleteTag = async (id: string) => {
    try {
      await deleteTag(id);
      notifications.show({ color: 'teal', message: '标签已删除' });
      fetchTags();
    } catch {
      // error handled
    }
  };

  return (
    <Stack gap="lg">
      <Paper p="lg" radius="md" withBorder>
        <Title order={2} size="h3">
          系统设置与密钥凭据
        </Title>
        <Text size="sm" c="dimmed">
          管理用于 Miniflux、FreshRSS 等外部阅读器客户端认证的 Access Key、订阅标签与底层服务指标。
        </Text>
      </Paper>

      <Tabs value={activeTab} onChange={setActiveTab} radius="md">
        <Tabs.List>
          <Tabs.Tab value="keys" leftSection={<IconKey size={16} />}>
            API Access Key
          </Tabs.Tab>
          <Tabs.Tab value="tags" leftSection={<IconTag size={16} />}>
            订阅分类标签
          </Tabs.Tab>
          <Tabs.Tab value="info" leftSection={<IconInfoCircle size={16} />}>
            系统环境与状态
          </Tabs.Tab>
        </Tabs.List>

        {/* Tab: Keys */}
        <Tabs.Panel value="keys" pt="md">
          <Paper p="md" radius="md" withBorder>
            <Group justify="space-between" mb="md">
              <Text fw={600} size="sm">
                Access Key 凭据清单
              </Text>
              <Button
                size="xs"
                variant="filled"
                color="blue"
                leftSection={<IconPlus size={14} />}
                onClick={() => setCreateKeyModalOpen(true)}
              >
                新建 Access Key
              </Button>
            </Group>

            {keysLoading ? (
              <Stack align="center" py="xl">
                <Loader size="md" />
              </Stack>
            ) : keys.length === 0 ? (
              <Text c="dimmed" py="md">
                暂无 Access Key。如果您的 RSS 阅读器（如 FreshRSS）需要认证抓取私有源，请新建一个 Key。
              </Text>
            ) : (
              <Table striped highlightOnHover verticalSpacing="sm">
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>名称</Table.Th>
                    <Table.Th>Access Key</Table.Th>
                    <Table.Th>创建时间</Table.Th>
                    <Table.Th>状态</Table.Th>
                    <Table.Th>操作</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {keys.map((k) => (
                    <Table.Tr key={k.id}>
                      <Table.Td>{k.name}</Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          <Text ff="monospace" size="xs">
                            {k.key}
                          </Text>
                          <Tooltip label="复制完整请求头 Authorization: AK-SK ...">
                            <ActionIcon
                              variant="subtle"
                              size="xs"
                              onClick={() => handleCopy(`AK-SK ${k.key}`, 'AK-SK 授权头')}
                            >
                              <IconCopy size={14} />
                            </ActionIcon>
                          </Tooltip>
                        </Group>
                      </Table.Td>
                      <Table.Td>{k.created_at ? dayjs(k.created_at).format('YYYY-MM-DD') : '-'}</Table.Td>
                      <Table.Td>
                        <Badge size="xs" variant="light" color={k.is_active ? 'teal' : 'gray'}>
                          {k.is_active ? '活跃' : '停用'}
                        </Badge>
                      </Table.Td>
                      <Table.Td>
                        <Tooltip label="删除 Key">
                          <ActionIcon
                            variant="subtle"
                            color="red"
                            size="sm"
                            onClick={() => handleDeleteKey(k.id)}
                          >
                            <IconTrash size={16} />
                          </ActionIcon>
                        </Tooltip>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            )}
          </Paper>
        </Tabs.Panel>

        {/* Tab: Tags */}
        <Tabs.Panel value="tags" pt="md">
          <Paper p="md" radius="md" withBorder>
            <Group mb="md" gap="sm">
              <TextInput
                placeholder="新标签名称..."
                value={tagName}
                onChange={(e) => setTagName(e.target.value)}
                style={{ flex: 1, maxWidth: 320 }}
              />
              <Button
                size="sm"
                variant="light"
                leftSection={<IconPlus size={14} />}
                loading={creatingTag}
                onClick={handleCreateTag}
              >
                添加标签
              </Button>
            </Group>

            {tagsLoading ? (
              <Stack align="center" py="xl">
                <Loader size="md" />
              </Stack>
            ) : tags.length === 0 ? (
              <Text c="dimmed" py="md">
                暂无分类标签。
              </Text>
            ) : (
              <Group gap="sm">
                {tags.map((t) => (
                  <Badge
                    key={t.id}
                    size="lg"
                    variant="light"
                    color={t.color || 'blue'}
                    rightSection={
                      <ActionIcon
                        variant="transparent"
                        color="red"
                        size="xs"
                        onClick={() => handleDeleteTag(t.id)}
                      >
                        <IconTrash size={12} />
                      </ActionIcon>
                    }
                  >
                    {t.name}
                  </Badge>
                ))}
              </Group>
            )}
          </Paper>
        </Tabs.Panel>

        {/* Tab: System Info */}
        <Tabs.Panel value="info" pt="md">
          <Paper p="md" radius="md" withBorder>
            {sysLoading ? (
              <Stack align="center" py="xl">
                <Loader size="md" />
              </Stack>
            ) : (
              <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="md">
                <Card shadow="xs" padding="md" radius="md" withBorder>
                  <Text size="xs" c="dimmed">
                    应用版本
                  </Text>
                  <Text fw={700} size="xl" mt="xs">
                    {sysInfo?.version || '1.5.7'}
                  </Text>
                  <Badge size="xs" variant="light" color="blue" mt="xs">
                    WeFeed Community Fork
                  </Badge>
                </Card>

                <Card shadow="xs" padding="md" radius="md" withBorder>
                  <Text size="xs" c="dimmed">
                    Python 运行时
                  </Text>
                  <Text fw={700} size="lg" mt="xs" ff="monospace">
                    {sysInfo?.python || 'Python 3.13'}
                  </Text>
                  <Text size="xs" c="dimmed" mt="xs">
                    运行在 {sysInfo?.os || 'Linux Docker'}
                  </Text>
                </Card>

                <Card shadow="xs" padding="md" radius="md" withBorder>
                  <Text size="xs" c="dimmed">
                    数据库收录规模
                  </Text>
                  <Text fw={700} size="xl" mt="xs">
                    {sysInfo?.database?.articles_count ?? '-'} 篇文章
                  </Text>
                  <Text size="xs" c="dimmed" mt="xs">
                    共收录 {sysInfo?.database?.feeds_count ?? '-'} 个订阅源
                  </Text>
                </Card>
              </SimpleGrid>
            )}
          </Paper>
        </Tabs.Panel>
      </Tabs>

      {/* Create Key Modal */}
      <Modal
        opened={createKeyModalOpen}
        onClose={() => setCreateKeyModalOpen(false)}
        title="创建新 Access Key"
        centered
        radius="md"
      >
        <Stack gap="md">
          <TextInput
            label="Key 名称 / 用途描述"
            placeholder="例如: FreshRSS-VPS"
            value={keyName}
            onChange={(e) => setKeyName(e.target.value)}
            required
          />
          <NumberInput
            label="有效期 (天)"
            value={keyExpires}
            onChange={setKeyExpires}
            min={1}
            max={3650}
          />
          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={() => setCreateKeyModalOpen(false)}>
              取消
            </Button>
            <Button loading={creatingKey} onClick={handleCreateKey} color="blue">
              确认生成
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}

export default SettingsPage;
