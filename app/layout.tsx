import React from 'react';
import './globals.css';
import Navigation from '../src/components/Navigation';
import type { Metadata, Viewport } from 'next';

export const metadata: Metadata = {
  title: 'Faceit AI Bot - Анализ статистики и поиск тиммейтов',
  description: 'Инструмент для анализа игровой статистики и поиска тиммейтов на платформе Faceit. Скачайте расширение для браузера или полную версию на нашем сайте.',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <Navigation />
        <main style={{ paddingTop: '80px' }}>{children}</main>
      </body>
    </html>
  );
}
