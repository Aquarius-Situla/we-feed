import React, { useEffect, useState } from 'react';
import {
  Drawer,
  Stack,
  Title,
  Text,
  Group,
  Button,
  Divider,
  Loader,
  ScrollArea,
  Badge,
} from '@mantine/core';
import { IconExternalLink, IconRefresh, IconCheck, IconCopy } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { getArticleDetail, refreshArticle, markArticleRead, ArticleItem } from '../api/article';
import dayjs from 'dayjs';

interface ArticleReaderDrawerProps {
  articleId: string | null;
  onClose: () => void;
  onRefreshList?: () => void;
}

export function ArticleReaderDrawer({ articleId, onClose, onRefreshList }: ArticleReaderDrawerProps) {
  const [article, setArticle] = useState<ArticleItem | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  useEffect(() => {
    if (!articleId) {
      setArticle(null);
      return;
    }

    setLoading(true);
    getArticleDetail(articleId, 1)
      .then((data) => {
        setArticle(data);
        // Automatically mark as read
        if (!data.is_read) {
          markArticleRead(articleId, true).catch(() => {});
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [articleId]);

  const handleRefreshContent = async () => {
    if (!articleId) return;
    setRefreshing(true);
    try {
      await refreshArticle(articleId);
      notifications.show({
        color: 'teal',
        title: '已提交刷新任务',
        message: '后台正在拉取最新排版正文，请稍候...',
      });
      // Fetch updated detail
      setTimeout(async () => {
        const updated = await getArticleDetail(articleId, 1);
        setArticle(updated);
        onRefreshList?.();
      }, 2500);
    } catch {
      // error handled by client
    } finally {
      setRefreshing(false);
    }
  };

  const handleCopyLink = () => {
    if (article?.url) {
      navigator.clipboard.writeText(article.url);
      notifications.show({ color: 'blue', message: '文章链接已复制到剪贴板' });
    }
  };

  return (
    <Drawer
      opened={Boolean(articleId)}
      onClose={onClose}
      position="right"
      size="xl"
      title={article?.mp_name ? `来自公众号：${article.mp_name}` : '文章详情'}
      padding="md"
    >
      {loading ? (
        <Stack align="center" justify="center" h={400}>
          <Loader size="lg" />
          <Text size="sm" c="dimmed">
            正在载入正文...
          </Text>
        </Stack>
      ) : article ? (
        <ScrollArea h="calc(100vh - 100px)" type="auto">
          <Stack gap="md" pr="md">
            <Title order={2} size="h3" style={{ lineHeight: 1.4 }}>
              {article.title}
            </Title>

            <Group justify="space-between" align="center">
              <Group gap="xs">
                {article.publish_time ? (
                  <Text size="xs" c="dimmed">
                    {dayjs.unix(article.publish_time).format('YYYY-MM-DD HH:mm')}
                  </Text>
                ) : null}
                <Badge size="sm" variant="light" color={article.has_content ? 'green' : 'gray'}>
                  {article.has_content ? '全文已缓存' : '仅摘要'}
                </Badge>
              </Group>

              <Group gap="xs">
                <Button
                  size="xs"
                  variant="default"
                  leftSection={<IconRefresh size={14} />}
                  loading={refreshing}
                  onClick={handleRefreshContent}
                >
                  刷新正文
                </Button>
                <Button
                  size="xs"
                  variant="default"
                  leftSection={<IconCopy size={14} />}
                  onClick={handleCopyLink}
                >
                  复制链接
                </Button>
                {article.url ? (
                  <Button
                    size="xs"
                    variant="light"
                    component="a"
                    href={article.url}
                    target="_blank"
                    leftSection={<IconExternalLink size={14} />}
                  >
                    在微信查看
                  </Button>
                ) : null}
              </Group>
            </Group>

            <Divider my="sm" />

            {/* Article Content Display */}
            {article.content_html || article.content ? (
              <div
                className="article-reader-body"
                style={{
                  fontSize: '16px',
                  lineHeight: '1.8',
                  wordBreak: 'break-word',
                }}
                dangerouslySetInnerHTML={{
                  __html: article.content_html || article.content || '',
                }}
              />
            ) : (
              <Stack align="center" py="xl">
                <Text c="dimmed">暂无完整正文内容，您可以点击上方“刷新正文”抓取全文。</Text>
              </Stack>
            )}
          </Stack>
        </ScrollArea>
      ) : null}
    </Drawer>
  );
}

export default ArticleReaderDrawer;
