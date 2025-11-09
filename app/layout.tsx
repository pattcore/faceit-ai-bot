import React from 'react';
import './globals.css';
import Navigation from '../src/components/Navigation';
import type { Metadata, Viewport } from 'next';

export const metadata: Metadata = {
  title: 'Faceit AI Bot - Анализ статистики и поиск тиммейтов',
  description: 'Инструмент для анализа игровой статистики и поиска тиммейтов на платформе Faceit. Скачайте расширение для браузера или полную версию на нашем сайте.',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Faceit AI Bot',
  },
  icons: {
    icon: [
      { url: '/icon-192x192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icon-512x512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [
      { url: '/icon-152x152.png', sizes: '152x152', type: 'image/png' },
    ],
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: '#2E9EF7',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#2E9EF7" />
        <link rel="apple-touch-icon" href="/icon-152x152.png" />
      </head>
      <body>
        <Navigation />
        <main style={{ paddingTop: '80px' }}>{children}</main>
        <script dangerouslySetInnerHTML={{
          __html: `
            if ('serviceWorker' in navigator) {
              window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                  .then(reg => console.log('Service Worker registered'))
                  .catch(err => console.log('Service Worker registration failed:', err));
              });
            }
          `
        }} />
      </body>
    </html>
  );
}
