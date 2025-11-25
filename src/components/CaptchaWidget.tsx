'use client';

import React, { useEffect } from 'react';
import TurnstileWidget from './TurnstileWidget';
import SmartCaptchaWidget from './SmartCaptchaWidget';

interface Props {
  onTokenChange: (token: string | null) => void;
  action?: string;
}

const provider = process.env.NEXT_PUBLIC_CAPTCHA_PROVIDER?.toLowerCase();
const turnstileSiteKey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;
const smartSiteKey = process.env.NEXT_PUBLIC_SMARTCAPTCHA_SITE_KEY;

export default function CaptchaWidget({ onTokenChange, action }: Props) {
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
  }, [onTokenChange]);

  if (provider === 'turnstile' && turnstileSiteKey) {
    return <TurnstileWidget onTokenChange={onTokenChange} action={action} />;
  }

  if (
    (provider === 'smartcaptcha' ||
      provider === 'yandex_smartcaptcha' ||
      provider === 'yandex') &&
    smartSiteKey
  ) {
    return <SmartCaptchaWidget onTokenChange={onTokenChange} />;
  }

  return null;
}
