import React, { useEffect, useState } from 'react';
import {
  Group,
  Image,
  Text,
  ActionIcon,
  Menu,
  Button,
  Badge,
  Tooltip,
  Paper,
  useMantineColorScheme,
  useComputedColorScheme,
} from '@mantine/core';
import {
  IconSun,
  IconMoon,
  IconBrandGithub,
  IconRss,
  IconArticle,
  IconBook,
  IconSettings,
  IconLogout,
  IconUser,
  IconQrcode,
  IconCheck,
  IconAlertCircle,
} from '@tabler/icons-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getCurrentUser, logout } from '../api/auth';
import { getWereadStatus } from '../api/weread';

interface HeaderProps {
  onOpenWereadAuth: () => void;
  onOpenWechatAuth: () => void;
}

export function Header({ onOpenWereadAuth, onOpenWechatAuth }: HeaderProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { colorScheme, setColorScheme } = useMantineColorScheme();
  const computedColorScheme = useComputedColorScheme('light', { getInitialValueInEffect: true });

  const [username, setUsername] = useState<string>('Admin');
  const [wereadConfigured, setWereadConfigured] = useState<boolean>(false);

  useEffect(() => {
    getCurrentUser()
      .then((user) => setUsername(user.username || 'Admin'))
      .catch(() => {});

    getWereadStatus()
      .then((res) => setWereadConfigured(Boolean(res.configured)))
      .catch(() => {});
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navLinks = [
    { label: '订阅源', path: '/', icon: <IconRss size={18} /> },
    { label: '文章流', path: '/articles', icon: <IconArticle size={18} /> },
    { label: '微信读书', path: '/weread', icon: <IconBook size={18} /> },
    { label: '系统设置', path: '/settings', icon: <IconSettings size={18} /> },
  ];

  return (
    <Paper
      shadow="xs"
      p="sm"
      pos="sticky"
      style={{ top: 0, zIndex: 100, borderBottom: '1px solid var(--mantine-color-default-border)' }}
    >
      <Group justify="space-between" align="center" px="md">
        {/* Left: Brand & Nav Links */}
        <Group gap="xl">
          <Group gap="xs" style={{ cursor: 'pointer' }} onClick={() => navigate('/')}>
            <Image src="/static/logo.svg?v=2" w={32} h={32} fallbackSrc="/static/logo.svg?v=2" />
            <Text fw={700} size="lg" variant="gradient" gradient={{ from: 'blue', to: 'cyan', deg: 90 }}>
              WeFeed
            </Text>
          </Group>

          <Group gap="xs" visibleFrom="sm">
            {navLinks.map((link) => {
              const active = location.pathname === link.path;
              return (
                <Button
                  key={link.path}
                  variant={active ? 'light' : 'subtle'}
                  color={active ? 'blue' : 'gray'}
                  size="sm"
                  leftSection={link.icon}
                  onClick={() => navigate(link.path)}
                >
                  {link.label}
                </Button>
              );
            })}
          </Group>
        </Group>

        {/* Right: Status Pills & Action Icons */}
        <Group gap="sm">
          {/* WeRead Status & Quick Auth */}
          <Tooltip label={wereadConfigured ? '微信读书已授权 (点击添加/切换账号)' : '微信读书未授权 (点击扫码绑定)'}>
            <Badge
              size="lg"
              variant={wereadConfigured ? 'light' : 'filled'}
              color={wereadConfigured ? 'teal' : 'orange'}
              style={{ cursor: 'pointer' }}
              leftSection={wereadConfigured ? <IconCheck size={14} /> : <IconAlertCircle size={14} />}
              onClick={onOpenWereadAuth}
            >
              微信读书
            </Badge>
          </Tooltip>

          {/* WeChat MP QR Quick Auth */}
          <Tooltip label="公众号扫码登录授权">
            <ActionIcon variant="default" size="lg" radius="md" onClick={onOpenWechatAuth}>
              <IconQrcode size={20} />
            </ActionIcon>
          </Tooltip>

          {/* Theme Toggle */}
          <Tooltip label={computedColorScheme === 'dark' ? '切换亮色模式' : '切换暗色模式'}>
            <ActionIcon
              variant="default"
              size="lg"
              radius="md"
              onClick={() => setColorScheme(computedColorScheme === 'dark' ? 'light' : 'dark')}
            >
              {computedColorScheme === 'dark' ? <IconSun size={20} /> : <IconMoon size={20} />}
            </ActionIcon>
          </Tooltip>

          {/* GitHub Repo */}
          <Tooltip label="访问 GitHub 仓库">
            <ActionIcon
              variant="default"
              size="lg"
              radius="md"
              component="a"
              href="https://github.com/Aquarius-Situla/we-feed"
              target="_blank"
            >
              <IconBrandGithub size={20} />
            </ActionIcon>
          </Tooltip>

          {/* User Menu */}
          <Menu shadow="md" width={180}>
            <Menu.Target>
              <Button variant="default" size="sm" radius="md" leftSection={<IconUser size={16} />}>
                {username}
              </Button>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Label>用户中心</Menu.Label>
              <Menu.Item leftSection={<IconSettings size={16} />} onClick={() => navigate('/settings')}>
                系统设置
              </Menu.Item>
              <Menu.Divider />
              <Menu.Item color="red" leftSection={<IconLogout size={16} />} onClick={handleLogout}>
                退出登录
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
      </Group>
    </Paper>
  );
}

export default Header;
