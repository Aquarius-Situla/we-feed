import React, { useEffect, useState } from 'react';
import {
  Stack,
  Paper,
  Group,
  TextInput,
  Select,
  Button,
  SimpleGrid,
  Card,
  Image,
  Text,
  Badge,
  ActionIcon,
  Tooltip,
  Pagination,
  Loader,
  Box,
} from '@mantine/core';
import {
  IconSearch,
  IconCheck,
  IconTrash,
  IconRefresh,
  IconExternalLink,
  IconBook2,
} from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { useSearchParams } from 'react-router-dom';
import dayjs from 'dayjs';
import {
  getArticles,
  deleteArticle,
  markArticleRead,
  refreshArticle,
  ArticleItem,
} from '../api/article';
import { getFeeds, FeedItem } from '../api/feed';
import { listTags, TagItem } from '../api/system';
import ArticleReaderDrawer from '../components/ArticleReaderDrawer';

export function ArticlesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialMpId = searchParams.get('mp_id') || '';
  const initialTagId = searchParams.get('tag_id') || '';

  const [articles, setArticles] = useState<ArticleItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);

  // Filters
  const [selectedMpId, setSelectedMpId] = useState<string>(initialMpId);
  const [selectedTagId, setSelectedTagId] = useState<string>(initialTagId);
  const [searchKw, setSearchKw] = useState<string>('');
  const [readFilter, setReadFilter] = useState<string>('all');
  const [page, setPage] = useState<number>(1);
  const pageSize = 12;

  useEffect(() => {
    const mpIdFromUrl = searchParams.get('mp_id') || '';
    const tagIdFromUrl = searchParams.get('tag_id') || '';
    setSelectedMpId(mpIdFromUrl);
    setSelectedTagId(tagIdFromUrl);
    setPage(1);
  }, [searchParams]);

  // Feeds & Tags dropdown options
  const [feeds, setFeeds] = useState<FeedItem[]>([]);
  const [tags, setTags] = useState<TagItem[]>([]);

  // Reader Drawer State
  const [activeArticleId, setActiveArticleId] = useState<string | null>(null);

  useEffect(() => {
    getFeeds({ page: 1, pageSize: 100 })
      .then((res) => setFeeds(res.list))
      .catch(() => {});
    listTags()
      .then((res) => setTags(res))
      .catch(() => {});
  }, []);

  const fetchArticles = async () => {
    setLoading(true);
    try {
      const isReadParam =
        readFilter === 'read' ? 1 : readFilter === 'unread' ? 0 : undefined;
      const data = await getArticles({
        page,
        pageSize,
        mp_id: selectedMpId || undefined,
        tag_id: selectedTagId || undefined,
        kw: searchKw || undefined,
        is_read: isReadParam,
      });
      setArticles(data.list);
      setTotal(data.total);
    } catch {
      // error handled
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArticles();
  }, [page, selectedMpId, selectedTagId, readFilter]);

  const handleSelectMp = (val: string | null) => {
    setSelectedMpId(val || '');
    setPage(1);
  };

  const handleSelectReadFilter = (val: string) => {
    setReadFilter(val);
    setPage(1);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchArticles();
  };

  const handleToggleRead = async (e: React.MouseEvent, article: ArticleItem) => {
    e.stopPropagation();
    const nextRead = article.is_read ? 0 : 1;
    try {
      await markArticleRead(article.id, nextRead === 1);
      setArticles((prev) =>
        prev.map((item) => (item.id === article.id ? { ...item, is_read: nextRead } : item))
      );
    } catch {
      // error handled
    }
  };

  const handleDelete = async (e: React.MouseEvent, article: ArticleItem) => {
    e.stopPropagation();
    if (!window.confirm(`确定删除文章 "${article.title}" 吗？`)) return;
    try {
      await deleteArticle(article.id);
      notifications.show({ color: 'teal', message: '文章已删除' });
      fetchArticles();
    } catch {
      // error handled
    }
  };

  const handleRefresh = async (e: React.MouseEvent, article: ArticleItem) => {
    e.stopPropagation();
    try {
      await refreshArticle(article.id);
      notifications.show({ color: 'blue', message: '已提交抓取刷新任务' });
    } catch {
      // error handled
    }
  };

  const feedOptions = [
    { value: '', label: '全部公众号' },
    ...feeds.map((f) => ({ value: f.id, label: f.name })),
  ];

  return (
    <Stack gap="lg">
      {/* Search & Filter Toolbar */}
      <Paper p="md" radius="md" withBorder>
        <Group justify="space-between" wrap="wrap">
          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px', flex: 1, minWidth: 260 }}>
            <TextInput
              placeholder="搜索文章标题..."
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
              value={selectedTagId}
              onChange={(val) => {
                setSelectedTagId(val || '');
                setPage(1);
              }}
              data={[
                { value: '', label: '全部分类标签' },
                ...tags.map((t) => ({ value: t.id, label: t.name })),
              ]}
              w={150}
              placeholder="按分类标签筛选"
            />

            <Select
              value={selectedMpId}
              onChange={(val) => {
                setSelectedMpId(val || '');
                setPage(1);
              }}
              data={feedOptions}
              searchable
              w={180}
              placeholder="筛选公众号"
            />

            <Select
              value={readFilter}
              onChange={(val) => {
                setReadFilter(val || 'all');
                setPage(1);
              }}
              data={[
                { value: 'all', label: '全部阅读状态' },
                { value: 'unread', label: '仅未读' },
                { value: 'read', label: '仅已读' },
              ]}
              w={140}
            />
          </Group>
        </Group>
      </Paper>

      {/* Articles Grid / Stream */}
      {loading ? (
        <Stack align="center" justify="center" h={300}>
          <Loader size="lg" />
          <Text size="sm" c="dimmed">
            正在载入文章流...
          </Text>
        </Stack>
      ) : articles.length === 0 ? (
        <Stack align="center" justify="center" h={240}>
          <Text c="dimmed">暂无符合条件的文章</Text>
        </Stack>
      ) : (
        <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="md">
          {articles.map((art) => (
            <Card
              key={art.id}
              shadow="sm"
              padding="md"
              radius="md"
              withBorder
              onClick={() => setActiveArticleId(art.id)}
              style={{
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                opacity: art.is_read ? 0.75 : 1,
                transition: 'transform 0.15s ease, box-shadow 0.15s ease',
              }}
            >
              <Stack gap="xs">
                {art.pic_url ? (
                  <Box style={{ overflow: 'hidden', borderRadius: '8px' }}>
                    <Image
                      src={art.pic_url}
                      height={140}
                      fit="cover"
                      referrerPolicy="no-referrer"
                      fallbackSrc="/static/logo.svg?v=2"
                    />
                  </Box>
                ) : null}

                <Text fw={600} size="sm" lineClamp={2} style={{ lineHeight: 1.4 }}>
                  {art.title}
                </Text>

                <Group gap="xs" justify="space-between">
                  <Badge size="xs" variant="light" color="blue">
                    {art.mp_name || '公众号'}
                  </Badge>
                  {art.publish_time ? (
                    <Text size="xs" c="dimmed">
                      {dayjs.unix(art.publish_time).format('MM-DD HH:mm')}
                    </Text>
                  ) : null}
                </Group>
              </Stack>

              <Group justify="space-between" mt="sm" pt="xs" style={{ borderTop: '1px solid var(--mantine-color-default-border)' }}>
                <Group gap={4}>
                  <Tooltip label={art.is_read ? '标记为未读' : '标记为已读'}>
                    <ActionIcon
                      variant="subtle"
                      size="sm"
                      color={art.is_read ? 'teal' : 'gray'}
                      onClick={(e) => handleToggleRead(e, art)}
                    >
                      <IconCheck size={16} />
                    </ActionIcon>
                  </Tooltip>

                  <Tooltip label="重新抓取全文排版">
                    <ActionIcon variant="subtle" size="sm" onClick={(e) => handleRefresh(e, art)}>
                      <IconRefresh size={16} />
                    </ActionIcon>
                  </Tooltip>

                  <Tooltip label="删除文章">
                    <ActionIcon
                      variant="subtle"
                      color="red"
                      size="sm"
                      onClick={(e) => handleDelete(e, art)}
                    >
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Tooltip>
                </Group>

                <Button
                  size="xs"
                  variant="subtle"
                  leftSection={<IconBook2 size={14} />}
                  onClick={() => setActiveArticleId(art.id)}
                >
                  阅读
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

      {/* Article Reader Drawer */}
      <ArticleReaderDrawer
        articleId={activeArticleId}
        onClose={() => setActiveArticleId(null)}
        onRefreshList={fetchArticles}
      />
    </Stack>
  );
}

export default ArticlesPage;
