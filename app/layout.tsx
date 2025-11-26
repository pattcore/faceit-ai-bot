import React from 'react';
import './globals.css';
import Navigation from '../src/components/Navigation';
import { Providers } from './providers';

export const metadata = {
  title: 'Faceit AI Bot — AI demo coach and teammate search for CS2',
  description: 'Faceit AI Bot analyzes your CS2 demos with an AI coach and helps you find teammates on FACEIT.',
  icons: {
    icon: '/icon.svg',
  },
};

export const viewport = {
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
        <Providers>
          <Navigation />
          <main style={{ paddingTop: '80px' }}>{children}</main>
        </Providers>
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
