import React, { useEffect, useState, useRef } from 'react';
import { Modal, Stack, Image, Text, Loader, Button, Group } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { getWechatQrCode, checkWechatQrStatus, cancelWechatQrAuth } from '../api/auth';

interface WechatAuthModalProps {
  opened: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function WechatAuthModal({ opened, onClose, onSuccess }: WechatAuthModalProps) {
  const [loading, setLoading] = useState<boolean>(false);
  const [qrImg, setQrImg] = useState<string>('');
  const [statusText, setStatusText] = useState<string>('正在准备微信公众平台授权...');
  const pollTimerRef = useRef<any>(null);
  const isSuccessRef = useRef<boolean>(false);

  const stopPolling = () => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  };

  const startPolling = () => {
    stopPolling();
    pollTimerRef.current = setInterval(async () => {
      try {
        const res = await checkWechatQrStatus();
        if (res?.login_status) {
          isSuccessRef.current = true;
          stopPolling();
          notifications.show({
            color: 'teal',
            title: '微信公众平台授权成功',
            message: '公众号凭证已成功同步！',
          });
          onSuccess?.();
          onClose(); // 授权成功直接关闭弹窗，切勿触发 cancelWechatQrAuth 导致正在提取凭证的后台被掐断
        } else if (res?.qr_code) {
          // 二维码图片已生成并校验有效
          const codeUrl = res?.code_url || `/static/wx_qrcode.png?t=${Date.now()}`;
          setQrImg((prev) => prev || codeUrl); // 若已展示图片则保持不变，避免每次轮询传入新时间戳导致图片反复重载与闪烁
          setLoading(false);
          setStatusText('请使用微信管理员扫一扫确认');
        } else if (res?.is_running) {
          // 浏览器仍在启动或加载登录页面
          setStatusText('后台正在加载微信登录页面与二维码...');
        } else {
          // 线程已退出且未生成二维码
          stopPolling();
          setLoading(false);
          setStatusText('二维码生成超时或已失效，请点击刷新重试');
        }
      } catch {
        // 网络抖动，继续轮询
      }
    }, 2000);
  };

  const startAuth = async () => {
    setLoading(true);
    setStatusText('正在启动微信公众平台登录流程...');
    setQrImg('');
    try {
      const res = await getWechatQrCode();
      if (res?.is_exists) {
        const codeUrl = res?.code || res?.url || `/static/wx_qrcode.png?t=${Date.now()}`;
        setQrImg((prev) => prev || codeUrl);
        setLoading(false);
        setStatusText('请使用微信管理员扫一扫确认');
      } else {
        setStatusText('后台正在加载微信登录页面与二维码...');
      }
      startPolling();
    } catch (err: any) {
      setLoading(false);
      setStatusText('获取二维码出错: ' + (err?.message || '网络异常'));
    }
  };

  const handleRefresh = async () => {
    if (loading && !qrImg) return;
    stopPolling();
    setLoading(true);
    setStatusText('正在重置登录会话...');
    try {
      await cancelWechatQrAuth();
    } catch {
      // 忽略清理异常
    }
    // 等待后台线程和浏览器完成优雅清理（300ms），避免刷新时并发冲突
    await new Promise((resolve) => setTimeout(resolve, 300));
    await startAuth();
  };

  const handleClose = () => {
    stopPolling();
    if (!isSuccessRef.current) {
      cancelWechatQrAuth().catch(() => {});
    }
    onClose();
  };

  useEffect(() => {
    if (opened) {
      isSuccessRef.current = false;
      startAuth();
    } else {
      stopPolling();
    }
    return () => {
      stopPolling();
      if (!isSuccessRef.current) {
        cancelWechatQrAuth().catch(() => {});
      }
    };
  }, [opened]);

  return (
    <Modal opened={opened} onClose={handleClose} title="微信公众平台扫码授权" centered radius="md">
      <Stack align="center" gap="md" py="md">
        {loading || !qrImg ? (
          <Stack align="center" gap="xs" py="xl">
            <Loader size="lg" />
            <Text size="xs" c="dimmed">
              后台启动浏览器可能需要 5-15 秒，请耐心等待
            </Text>
          </Stack>
        ) : (
          <Image src={qrImg} w={220} h={220} radius="md" style={{ border: '1px solid #e9ecef' }} />
        )}
        <Text size="sm" c="dimmed">
          {statusText}
        </Text>
        <Group mt="sm">
          <Button variant="default" size="sm" onClick={handleRefresh} loading={loading && !qrImg}>
            刷新二维码
          </Button>
          <Button variant="subtle" size="sm" color="gray" onClick={handleClose}>
            关闭
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}

export default WechatAuthModal;
