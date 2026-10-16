import React, { useEffect, useState } from 'react';
import {
  SimpleGrid,
  Card,
  Image,
  Text,
  Badge,
  Group,
  Stack,
  Button,
  TextInput,
  Select,
  ActionIcon,
  Menu,
  Switch,
  Modal,
  Loader,
  Pagination,
  Tooltip,
  Paper,
  Box,
} from '@mantine/core';
import {
  IconSearch,
  IconPlus,
  IconRss,
  IconCopy,
  IconTrash,
  IconRefresh,
  IconArrowRight,
  IconDownload,
  IconLink,
} from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { useNavigate } from 'react-router-dom';
import {
  getFeeds,
  addFeed,
  addFeedByArticle,
  updateFeedStatus,
  deleteFeed,
  refreshFeed,
  getRssUrl,
  FeedItem,
} from '../api/feed';

export function FeedsPage() {
  const navigate = useNavigate();

  const [feeds, setFeeds] = useState<FeedItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);

  // Filters
  const [searchKw, setSearchKw] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [page, setPage] = useState<number>(1);
  const pageSize = 12;

  // Add Subscription Modal
  const [addModalOpen, setAddModalOpen] = useState<boolean>(false);
  const [addMode, setAddMode] = useState<'article' | 'name'>('article');
  const [addInput, setAddInput] = useState<string>('');
  const [adding, setAdding] = useState<boolean>(false);

  const fetchFeeds = async () => {
    setLoading(true);
    try {
      const statusParam =
        statusFilter === 'active' ? 1 : statusFilter === 'disabled' ? 0 : undefined;
      const data = await getFeeds({
        page,
        pageSize,
        kw: searchKw || undefined,
        status: statusParam,
      });
      setFeeds(data.list);
      setTotal(data.total);
    } catch {
      // error handled by client
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFeeds();
  }, [page, statusFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchFeeds();
  };

  const handleToggleStatus = async (feed: FeedItem) => {
    const nextStatus = feed.status === 1 ? 0 : 1;
    try {
      await updateFeedStatus(feed.id, nextStatus);
      setFeeds((prev) =>
        prev.map((item) => (item.id === feed.id ? { ...item, status: nextStatus } : item))
      );
      notifications.show({
        color: nextStatus === 1 ? 'teal' : 'gray',
        message: `${feed.name} 已${nextStatus === 1 ? '启用' : '禁用'}`,
      });
    } catch {
      // error handled
    }
  };

  const handleDelete = async (feed: FeedItem) => {
    if (!window.confirm(`确定要取消订阅 "${feed.name}" 吗？`)) return;
    try {
      await deleteFeed(feed.id);
      notifications.show({ color: 'teal', message: `已取消订阅 ${feed.name}` });
      fetchFeeds();
    } catch {
      // error handled
    }
  };

  const handleRefresh = async (feed: FeedItem) => {
    try {
      await refreshFeed(feed.id);
      notifications.show({ color: 'blue', message: `已触发 ${feed.name} 文章更新任务` });
    } catch {
      // error handled
    }
  };

  const handleCopyRss = (feedId?: string, format: 'rss' | 'atom' | 'json' = 'rss') => {
    const url = getRssUrl(feedId, format);
    navigator.clipboard.writeText(url);
    notifications.show({
      color: 'blue',
      message: `${format.toUpperCase()} 订阅源已复制到剪贴板！`,
    });
  };

  const handleAddSubmit = async () => {
    if (!addInput.trim()) return;
    setAdding(true);
    try {
      if (addMode === 'article') {
        await addFeedByArticle(addInput.trim());
      } else {
        await addFeed({ name: addInput.trim() });
      }
      notifications.show({ color: 'teal', message: '订阅成功添加！' });
      setAddModalOpen(false);
      setAddInput('');
      fetchFeeds();
    } catch {
      // error handled
    } finally {
      setAdding(false);
    }
  };

  return (
    <Stack gap="lg">
      {/* Top Controls */}
      <Paper p="md" radius="md" withBorder>
        <Group justify="space-between" wrap="wrap">
          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px', flex: 1, minWidth: 260 }}>
            <TextInput
              placeholder="搜索公众号名称..."
              leftSection={<IconSearch size={16} />}
              value={searchKw}
              onChange={(e) => setSearchKw(e.target.value)}
              style={{ flex: 1 }}
            />
            <Button type="submit" variant="light">
              搜索
            </Button>
          </form>

          <Group gap="sm">
            <Select
              value={statusFilter}
              onChange={(val) => {
                setStatusFilter(val || 'all');
                setPage(1);
              }}
              data={[
                { value: 'all', label: '全部状态' },
                { value: 'active', label: '仅显示启用' },
                { value: 'disabled', label: '仅显示已禁用' },
              ]}
              w={140}
            />

            <Menu shadow="md">
              <Menu.Target>
                <Button variant="default" leftSection={<IconRss size={16} />}>
                  全量订阅源
                </Button>
              </Menu.Target>
              <Menu.Dropdown>
                <Menu.Item onClick={() => handleCopyRss(undefined, 'rss')}>复制 RSS 2.0 源</Menu.Item>
                <Menu.Item onClick={() => handleCopyRss(undefined, 'atom')}>复制 Atom 源</Menu.Item>
                <Menu.Item onClick={() => handleCopyRss(undefined, 'json')}>复制 JSON Feed</Menu.Item>
              </Menu.Dropdown>
            </Menu>

            <Button
              variant="default"
              leftSection={<IconDownload size={16} />}
              component="a"
              href="/feed/opml"
              target="_blank"
            >
              导出 OPML
            </Button>

            <Button
              variant="filled"
              color="blue"
              leftSection={<IconPlus size={16} />}
              onClick={() => setAddModalOpen(true)}
            >
              添加订阅
            </Button>
          </Group>
        </Group>
      </Paper>

      {/* Feed Cards Grid */}
      {loading ? (
        <Stack align="center" justify="center" h={300}>
          <Loader size="lg" />
          <Text size="sm" c="dimmed">
            正在加载订阅源...
          </Text>
        </Stack>
      ) : feeds.length === 0 ? (
        <Stack align="center" justify="center" h={240}>
          <Text c="dimmed">暂无订阅公众号，点击右上角“添加订阅”添加您的第一个订阅！</Text>
        </Stack>
      ) : (
        <SimpleGrid cols={{ base: 1, sm: 2, md: 3, lg: 4 }} spacing="md">
          {feeds.map((feed) => (
            <Card
              key={feed.id}
              shadow="sm"
              padding="md"
              radius="md"
              withBorder
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'transform 0.2s ease, box-shadow 0.2s ease',
              }}
            >
              <Stack gap="sm">
                <Group justify="space-between" align="flex-start" wrap="nowrap">
                  <Group gap="sm" wrap="nowrap">
                    <Image
                      src={feed.avatar}
                      w={44}
                      h={44}
                      radius="xl"
                      fallbackSrc="/static/logo.svg"
                      style={{ border: '1px solid var(--mantine-color-default-border)' }}
                    />
                    <Box style={{ overflow: 'hidden' }}>
                      <Text fw={600} size="sm" lineClamp={1}>
                        {feed.name}
                      </Text>
                      <Badge size="xs" variant="light" color={feed.status === 1 ? 'teal' : 'gray'}>
                        {feed.article_count || 0} 篇文章
                      </Badge>
                    </Box>
                  </Group>

                  <Switch
                    checked={feed.status === 1}
                    onChange={() => handleToggleStatus(feed)}
                    size="xs"
                    color="teal"
                  />
                </Group>

                <Text size="xs" c="dimmed" lineClamp={2} style={{ minHeight: '32px' }}>
                  {feed.mp_intro || '暂无公众号简介'}
                </Text>
              </Stack>

              <Group justify="space-between" mt="md" pt="sm" style={{ borderTop: '1px solid var(--mantine-color-default-border)' }}>
                <Group gap={4}>
                  <Menu shadow="sm">
                    <Menu.Target>
                      <Tooltip label="复制 RSS 订阅链接">
                        <ActionIcon variant="subtle" size="sm">
                          <IconRss size={16} />
                        </ActionIcon>
                      </Tooltip>
                    </Menu.Target>
                    <Menu.Dropdown>
                      <Menu.Item onClick={() => handleCopyRss(feed.id, 'rss')}>复制 RSS 2.0</Menu.Item>
                      <Menu.Item onClick={() => handleCopyRss(feed.id, 'atom')}>复制 Atom</Menu.Item>
                      <Menu.Item onClick={() => handleCopyRss(feed.id, 'json')}>复制 JSON</Menu.Item>
                    </Menu.Dropdown>
                  </Menu>

                  <Tooltip label="手动刷新更新文章">
                    <ActionIcon variant="subtle" size="sm" onClick={() => handleRefresh(feed)}>
                      <IconRefresh size={16} />
                    </ActionIcon>
                  </Tooltip>

                  <Tooltip label="取消订阅">
                    <ActionIcon variant="subtle" color="red" size="sm" onClick={() => handleDelete(feed)}>
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Tooltip>
                </Group>

                <Button
                  variant="subtle"
                  size="xs"
                  rightSection={<IconArrowRight size={14} />}
                  onClick={() => navigate(`/articles?mp_id=${feed.id}`)}
                >
                  查看文章
                </Button>
              </Group>
            </Card>
          ))}
        </SimpleGrid>
      )}

      {/* Pagination */}
      {total > pageSize ? (
        <Group justify="center" mt="md">
          <Pagination
            value={page}
            onChange={setPage}
            total={Math.ceil(total / pageSize)}
            size="sm"
            radius="md"
          />
        </Group>
      ) : null}

      {/* Add Subscription Modal */}
      <Modal
        opened={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        title="添加微信公众号订阅"
        centered
        radius="md"
      >
        <Stack gap="md">
          <Group gap="xs">
            <Button
              variant={addMode === 'article' ? 'filled' : 'default'}
              size="xs"
              onClick={() => setAddMode('article')}
              leftSection={<IconLink size={14} />}
            >
              文章链接识别 (推荐)
            </Button>
            <Button
              variant={addMode === 'name' ? 'filled' : 'default'}
              size="xs"
              onClick={() => setAddMode('name')}
            >
              公众号名称添加
            </Button>
          </Group>

          <TextInput
            label={addMode === 'article' ? '微信文章链接' : '公众号名称'}
            placeholder={
              addMode === 'article'
                ? 'https://mp.weixin.qq.com/s/...'
                : '例如: 人民日报'
            }
            value={addInput}
            onChange={(e) => setAddInput(e.target.value)}
            required
          />

          <Text size="xs" c="dimmed">
            {addMode === 'article'
              ? '粘贴该公众号任意一篇推文链接，系统将自动逆向解析其 Profile 元数据并完成订阅。'
              : '输入公众号完整标准名称。'}
          </Text>

          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={() => setAddModalOpen(false)}>
              取消
            </Button>
            <Button loading={adding} onClick={handleAddSubmit} color="blue">
              确认订阅
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}

export default FeedsPage;
