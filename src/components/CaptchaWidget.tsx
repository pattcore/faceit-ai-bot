'use client';

import React, { useEffect, useState } from 'react';
import TurnstileWidget from './TurnstileWidget';
import SmartCaptchaWidget from './SmartCaptchaWidget';

interface Props {
  onTokenChange: (token: string | null) => void;
  action?: string;
  resetSignal?: number;
}

type PublicConfig = {
  captcha?: {
    provider?: string | null;
    turnstile_site_key?: string | null;
    smartcaptcha_site_key?: string | null;
  };
};

export default function CaptchaWidget({ onTokenChange, action, resetSignal = 0 }: Props) {
  const [provider, setProvider] = useState<string | null>(null);
  const [turnstileSiteKey, setTurnstileSiteKey] = useState<string | null>(null);
  const [smartSiteKey, setSmartSiteKey] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const res = await fetch('/api/public-config', {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
          },
        });

        if (!res.ok) {
          return;
        }

        const cfg = (await res.json()) as PublicConfig;
        if (cancelled) return;

        const p = (cfg?.captcha?.provider || '').toLowerCase() || null;
        setProvider(p);
        setTurnstileSiteKey(cfg?.captcha?.turnstile_site_key || null);
        setSmartSiteKey(cfg?.captcha?.smartcaptcha_site_key || null);
      } catch {
        // ignore
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    // Диагностика: проверяем, какие значения видит фронт
    // eslint-disable-next-line no-console
    console.log('[CaptchaWidget]', {
      provider,
      hasTurnstileSiteKey: !!turnstileSiteKey,
      hasSmartSiteKey: !!smartSiteKey,
    });

    if (!provider) {
      onTokenChange(null);
    }
  }, [onTokenChange, provider, smartSiteKey, turnstileSiteKey]);

  if (provider === 'turnstile' && turnstileSiteKey) {
    return (
      <TurnstileWidget
        onTokenChange={onTokenChange}
        action={action}
        resetSignal={resetSignal}
        siteKey={turnstileSiteKey}
      />
    );
  }

  if (
    (provider === 'smartcaptcha' ||
      provider === 'yandex_smartcaptcha' ||
      provider === 'yandex') &&
    smartSiteKey
  ) {
    return <SmartCaptchaWidget onTokenChange={onTokenChange} siteKey={smartSiteKey} />;
  }

  return null;
}
