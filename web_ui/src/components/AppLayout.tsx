import React, { useState } from 'react';
import { Box, Container } from '@mantine/core';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import WereadAuthModal from './WereadAuthModal';
import WechatAuthModal from './WechatAuthModal';

export function AppLayout() {
  const [wereadModalOpen, setWereadModalOpen] = useState<boolean>(false);
  const [wechatModalOpen, setWechatModalOpen] = useState<boolean>(false);

  return (
    <Box style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header
        onOpenWereadAuth={() => setWereadModalOpen(true)}
        onOpenWechatAuth={() => setWechatModalOpen(true)}
      />

      <Container size="xl" py="lg" style={{ flex: 1, width: '100%' }}>
        <Outlet />
      </Container>

      {/* Auth Modals */}
      <WereadAuthModal
        opened={wereadModalOpen}
        onClose={() => setWereadModalOpen(false)}
        onSuccess={() => {}}
      />
      <WechatAuthModal
        opened={wechatModalOpen}
        onClose={() => setWechatModalOpen(false)}
        onSuccess={() => {}}
      />
    </Box>
  );
}

export default AppLayout;
