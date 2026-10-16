import React, { useEffect, useState, useRef } from 'react';
import { Modal, Stack, Image, Text, Loader, Button, Group } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { getWereadQrCode, checkWereadQrStatus } from '../api/weread';

interface WereadAuthModalProps {
  opened: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function WereadAuthModal({ opened, onClose, onSuccess }: WereadAuthModalProps) {
  const [loading, setLoading] = useState<boolean>(false);
  const [qrImg, setQrImg] = useState<string>('');
  const [statusText, setStatusText] = useState<string>('正在获取微信读书登录二维码...');
  const pollTimerRef = useRef<any>(null);

  const startAuth = async () => {
    setLoading(true);
    setStatusText('正在生成微信读书授权二维码...');
    setQrImg('');
    try {
      const res = await getWereadQrCode();
      const codeUrl = res?.code || res?.url || res?.data?.code || res;
      if (codeUrl && typeof codeUrl === 'string') {
        setQrImg(codeUrl);
        setStatusText('请使用微信扫一扫完成授权');
        startPolling();
      } else {
        setStatusText('获取二维码失败，请稍后重试');
      }
    } catch (err: any) {
      setStatusText('获取二维码出错: ' + (err?.message || '网络异常'));
    } finally {
      setLoading(false);
    }
  };

  const startPolling = () => {
    stopPolling();
    pollTimerRef.current = setInterval(async () => {
      try {
        const res = await checkWereadQrStatus();
        if (res?.login_status || res?.status === 1 || res?.ok) {
          stopPolling();
          notifications.show({
            color: 'teal',
            title: '微信读书授权成功',
            message: `账号 ${res?.vid || ''} 绑定成功！`,
          });
          onSuccess?.();
          onClose();
        } else if (res?.qr_code === false || res?.expired) {
          stopPolling();
          setStatusText('二维码已过期，请刷新重试');
        }
      } catch {
        // continue polling
      }
    }, 2500);
  };

  const stopPolling = () => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  };

  useEffect(() => {
    if (opened) {
      startAuth();
    } else {
      stopPolling();
    }
    return () => stopPolling();
  }, [opened]);

  return (
    <Modal opened={opened} onClose={onClose} title="微信读书扫码授权" centered radius="md">
      <Stack align="center" gap="md" py="md">
        {loading ? (
          <Loader size="lg" />
        ) : qrImg ? (
          <Image src={qrImg} w={220} h={220} radius="md" style={{ border: '1px solid #e9ecef' }} />
        ) : null}
        <Text size="sm" c="dimmed">
          {statusText}
        </Text>
        <Group mt="sm">
          <Button variant="default" size="sm" onClick={startAuth}>
            刷新二维码
          </Button>
          <Button variant="subtle" size="sm" color="gray" onClick={onClose}>
            关闭
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}

export default WereadAuthModal;
