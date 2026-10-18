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
  Textarea,
  MultiSelect,
  NumberInput,
  Tooltip,
  SimpleGrid,
  Card,
  Loader,
  Menu,
} from '@mantine/core';
import {
  IconKey,
  IconTag,
  IconInfoCircle,
  IconPlus,
  IconTrash,
  IconCopy,
  IconEdit,
  IconRss,
  IconExternalLink,
} from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { useNavigate } from 'react-router-dom';
import {
  listAccessKeys,
  createAccessKey,
  deleteAccessKey,
  AccessKeyItem,
} from '../api/accessKey';
import {
  listTags,
  createTag,
  updateTag,
  deleteTag,
  getTagRssUrl,
  TagItem,
  getSysInfo,
  SysInfoResponse,
} from '../api/system';
import { getFeeds } from '../api/feed';
import dayjs from 'dayjs';

export function SettingsPage() {
  const navigate = useNavigate();
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
  const [tagModalOpen, setTagModalOpen] = useState<boolean>(false);
  const [editingTag, setEditingTag] = useState<TagItem | null>(null);
  const [tagName, setTagName] = useState<string>('');
  const [tagIntro, setTagIntro] = useState<string>('');
  const [tagMps, setTagMps] = useState<string[]>([]);
  const [savingTag, setSavingTag] = useState<boolean>(false);
  const [availableFeeds, setAvailableFeeds] = useState<{ value: string; label: string }[]>([]);

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

  const fetchAvailableFeeds = async () => {
    try {
      const res = await getFeeds({ pageSize: 1000 });
      setAvailableFeeds(res.list.map((f) => ({ value: f.id, label: f.name })));
    } catch {
      // error handled
    }
  };

  useEffect(() => {
    if (activeTab === 'keys') fetchKeys();
    if (activeTab === 'tags') {
      fetchTags();
      fetchAvailableFeeds();
    }
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

  const handleOpenCreateTag = () => {
    setEditingTag(null);
    setTagName('');
    setTagIntro('');
    setTagMps([]);
    setTagModalOpen(true);
    fetchAvailableFeeds();
  };

  const handleOpenEditTag = (tag: TagItem) => {
    setEditingTag(tag);
    setTagName(tag.name || '');
    setTagIntro(tag.intro || '');
    let mps = tag.mps_list || [];
    if (!mps.length && tag.mps_id) {
      try {
        const parsed = JSON.parse(tag.mps_id);
        if (Array.isArray(parsed)) {
          mps = parsed.map((item: any) =>
            typeof item === 'object' && item?.id ? String(item.id) : String(item)
          );
        }
      } catch {}
    }
    setTagMps(mps);
    setTagModalOpen(true);
    fetchAvailableFeeds();
  };

  const handleSaveTag = async () => {
    if (!tagName.trim()) return;
    setSavingTag(true);
    try {
      const payload = {
        name: tagName.trim(),
        intro: tagIntro.trim(),
        mps_id: tagMps,
      };
      if (editingTag) {
        await updateTag(editingTag.id, payload);
        notifications.show({ color: 'teal', message: `标签 "${tagName.trim()}" 已更新！` });
      } else {
        await createTag(payload);
        notifications.show({ color: 'teal', message: `标签 "${tagName.trim()}" 创建成功！` });
      }
      setTagModalOpen(false);
      fetchTags();
    } catch {
      // error handled
    } finally {
      setSavingTag(false);
    }
  };

  const handleDeleteTag = async (tag: TagItem) => {
    if (!window.confirm(`确定要删除分类标签 "${tag.name}" 吗？关联的 RSS 聚合源将失效。`)) return;
    try {
      await deleteTag(tag.id);
      notifications.show({ color: 'teal', message: `分类标签 "${tag.name}" 已删除` });
      fetchTags();
    } catch {
      // error handled
    }
  };

  const handleCopyTagRss = (tagId: string, format: 'rss' | 'atom' | 'json' = 'rss') => {
    const url = getTagRssUrl(tagId, format);
    navigator.clipboard.writeText(url);
    notifications.show({
      color: 'blue',
      message: `${format.toUpperCase()} 分类订阅源已复制到剪贴板！`,
    });
  };

  return (
    <Stack gap="lg">
      <Paper p="lg" radius="md" withBorder>
        <Title order={2} size="h3">
          系统设置与密钥凭据
        </Title>
        <Text size="sm" c="dimmed">
          管理用于 Miniflux、FreshRSS 等外部阅读器客户端认证的 Access Key、订阅分类标签与底层服务指标。
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
            <Group justify="space-between" mb="md">
              <Group gap="xs">
                <Text fw={600} size="sm">
                  订阅分类标签列表
                </Text>
                <Badge size="xs" variant="light" color="blue">
                  共 {tags.length} 个分类
                </Badge>
              </Group>
              <Button
                size="xs"
                variant="filled"
                color="blue"
                leftSection={<IconPlus size={14} />}
                onClick={handleOpenCreateTag}
              >
                新建分类标签
              </Button>
            </Group>

            {tagsLoading ? (
              <Stack align="center" py="xl">
                <Loader size="md" />
              </Stack>
            ) : !Array.isArray(tags) || tags.length === 0 ? (
              <Text c="dimmed" py="md">
                暂无分类标签。点击上方「新建分类标签」即可创建专属的公众号分类并生成聚合 RSS 源。
              </Text>
            ) : (
              <Table striped highlightOnHover verticalSpacing="sm">
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>分类名称</Table.Th>
                    <Table.Th>简介说明</Table.Th>
                    <Table.Th>关联订阅数</Table.Th>
                    <Table.Th>分类聚合源</Table.Th>
                    <Table.Th>文章快捷浏览</Table.Th>
                    <Table.Th>操作</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {tags.map((t) => {
                    const mpCount =
                      t.mp_count !== undefined
                        ? t.mp_count
                        : Array.isArray(t.mps_list)
                        ? t.mps_list.length
                        : 0;
                    return (
                      <Table.Tr key={t.id}>
                        <Table.Td>
                          <Badge size="md" variant="light" color="blue">
                            {t.name}
                          </Badge>
                        </Table.Td>
                        <Table.Td>
                          <Text size="xs" c="dimmed" lineClamp={1}>
                            {t.intro || '-'}
                          </Text>
                        </Table.Td>
                        <Table.Td>
                          <Badge size="xs" variant="outline" color={mpCount > 0 ? 'teal' : 'gray'}>
                            {mpCount} 个公众号
                          </Badge>
                        </Table.Td>
                        <Table.Td>
                          <Menu shadow="md" position="bottom-start">
                            <Menu.Target>
                              <Button
                                size="xs"
                                variant="subtle"
                                leftSection={<IconRss size={14} />}
                              >
                                复制订阅源
                              </Button>
                            </Menu.Target>
                            <Menu.Dropdown>
                              <Menu.Item onClick={() => handleCopyTagRss(t.id, 'rss')}>
                                复制 RSS 2.0 源
                              </Menu.Item>
                              <Menu.Item onClick={() => handleCopyTagRss(t.id, 'atom')}>
                                复制 Atom 源
                              </Menu.Item>
                              <Menu.Item onClick={() => handleCopyTagRss(t.id, 'json')}>
                                复制 JSON Feed
                              </Menu.Item>
                            </Menu.Dropdown>
                          </Menu>
                        </Table.Td>
                        <Table.Td>
                          <Button
                            size="xs"
                            variant="subtle"
                            leftSection={<IconExternalLink size={14} />}
                            onClick={() => navigate(`/articles?tag_id=${t.id}`)}
                          >
                            浏览分类文章
                          </Button>
                        </Table.Td>
                        <Table.Td>
                          <Group gap="xs">
                            <Tooltip label="编辑分类与关联公众号">
                              <ActionIcon
                                variant="subtle"
                                color="blue"
                                size="sm"
                                onClick={() => handleOpenEditTag(t)}
                              >
                                <IconEdit size={16} />
                              </ActionIcon>
                            </Tooltip>
                            <Tooltip label="删除分类">
                              <ActionIcon
                                variant="subtle"
                                color="red"
                                size="sm"
                                onClick={() => handleDeleteTag(t)}
                              >
                                <IconTrash size={16} />
                              </ActionIcon>
                            </Tooltip>
                          </Group>
                        </Table.Td>
                      </Table.Tr>
                    );
                  })}
                </Table.Tbody>
              </Table>
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
                    {sysInfo?.core_version || sysInfo?.version || '1.5.7'}
                  </Text>
                  <Badge size="xs" variant="light" color="blue" mt="xs">
                    WeFeed Community Fork
                  </Badge>
                </Card>

                <Card shadow="xs" padding="md" radius="md" withBorder>
                  <Text size="xs" c="dimmed">
                    Python 运行时
                  </Text>
                  <Text fw={700} size="sm" mt="xs" ff="monospace" lineClamp={2}>
                    {sysInfo?.python_version ? String(sysInfo.python_version).split(' ')[0] : 'Python 3.13'}
                  </Text>
                  <Text size="xs" c="dimmed" mt="xs">
                    运行在 {typeof sysInfo?.os === 'object' && sysInfo?.os?.name ? `${sysInfo.os.name} (${sysInfo.os.release || 'Docker'})` : String(sysInfo?.os || 'Linux Docker')}
                  </Text>
                </Card>

                <Card shadow="xs" padding="md" radius="md" withBorder>
                  <Text size="xs" c="dimmed">
                    收录与队列监控
                  </Text>
                  <Text fw={700} size="xl" mt="xs">
                    {sysInfo?.article?.all_count ?? 0} 篇文章
                  </Text>
                  <Text size="xs" c="dimmed" mt="xs">
                    队列状态: {sysInfo?.queue?.is_running ? '🟢 运行中' : '⚪ 空闲'} (等待任务: {sysInfo?.queue?.pending_tasks ?? 0})
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

      {/* Create / Edit Tag Modal */}
      <Modal
        opened={tagModalOpen}
        onClose={() => setTagModalOpen(false)}
        title={editingTag ? '编辑订阅分类标签' : '新建订阅分类标签'}
        centered
        radius="md"
        size="lg"
      >
        <Stack gap="md">
          <TextInput
            label="标签名称"
            placeholder="例如: 科技前沿、深度阅读、财经观察"
            value={tagName}
            onChange={(e) => setTagName(e.target.value)}
            required
          />
          <Textarea
            label="简介描述"
            placeholder="可选：简单描述该分类所涵盖的内容主题"
            value={tagIntro}
            onChange={(e) => setTagIntro(e.target.value)}
            minRows={2}
          />
          <MultiSelect
            label="关联公众号"
            description="选择归属于该分类标签的公众号，保存后将自动归集并生成专属聚合 RSS 源"
            placeholder="请选择或搜索公众号..."
            data={availableFeeds}
            value={tagMps}
            onChange={setTagMps}
            searchable
            clearable
            nothingFoundMessage="未找到公众号"
            maxDropdownHeight={240}
          />
          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={() => setTagModalOpen(false)}>
              取消
            </Button>
            <Button loading={savingTag} onClick={handleSaveTag} color="blue">
              {editingTag ? '保存修改' : '确认创建'}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}

export default SettingsPage;
