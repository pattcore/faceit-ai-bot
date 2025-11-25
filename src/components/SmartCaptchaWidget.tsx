'use client';

import React, { useEffect, useRef } from 'react';

interface Props {
  onTokenChange: (token: string | null) => void;
}

const siteKey = process.env.NEXT_PUBLIC_SMARTCAPTCHA_SITE_KEY;

export default function SmartCaptchaWidget({ onTokenChange }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const renderedRef = useRef(false);

  useEffect(() => {
    if (!siteKey) {
      return;
    }

    let cancelled = false;

    const loadScript = () => {
      return new Promise<void>((resolve, reject) => {
        if (typeof window === 'undefined') {
          resolve();
          return;
        }

        const existing = document.querySelector(
          'script[data-smartcaptcha-script="true"]',
        ) as HTMLScriptElement | null;

        if (existing) {
          if (existing.getAttribute('data-smartcaptcha-loaded') === 'true') {
            resolve();
          } else {
            existing.addEventListener('load', () => resolve(), { once: true });
            existing.addEventListener(
              'error',
              () => reject(new Error('Failed to load SmartCaptcha script')),
              { once: true },
            );
          }
          return;
        }

        const script = document.createElement('script');
        script.src = 'https://smartcaptcha.yandexcloud.net/smartcaptcha.js';
        script.async = true;
        script.defer = true;
        script.setAttribute('data-smartcaptcha-script', 'true');
        script.onload = () => {
          script.setAttribute('data-smartcaptcha-loaded', 'true');
          resolve();
        };
        script.onerror = () =>
          reject(new Error('Failed to load SmartCaptcha script'));
        document.head.appendChild(script);
      });
    };

    loadScript()
      .then(() => {
        if (cancelled) return;
        if (renderedRef.current) return;
        if (!containerRef.current) return;
        if (typeof window === 'undefined') return;

        const smartCaptcha = (window as any).smartCaptcha;
        if (!smartCaptcha || typeof smartCaptcha.render !== 'function') {
          onTokenChange(null);
          return;
        }

        smartCaptcha.render(containerRef.current, {
          sitekey: siteKey,
          callback: (token: string) => {
            onTokenChange(token || null);
          },
        });
        renderedRef.current = true;
      })
      .catch(() => {
        // ignore
        onTokenChange(null);
      });

    return () => {
      cancelled = true;
      onTokenChange(null);
    };
  }, [onTokenChange]);

  if (!siteKey) {
    return null;
  }

  return (
    <div className="flex justify-center mt-4">
      <div
        ref={containerRef}
        style={{ minHeight: 80 }}
      />
    </div>
  );
}
