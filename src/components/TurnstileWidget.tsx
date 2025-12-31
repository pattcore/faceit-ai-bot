'use client';

import React, { useEffect, useRef } from 'react';

declare global {
  interface Window {
    turnstile?: {
      render: (container: HTMLElement, options: any) => string;
      reset: (widgetId?: string) => void;
    };
  }
}

interface Props {
  onTokenChange: (token: string | null) => void;
  action?: string;
  resetSignal?: number;
  siteKey: string;
}

export default function TurnstileWidget({ onTokenChange, action, resetSignal = 0, siteKey }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const widgetIdRef = useRef<string | null>(null);

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
          'script[data-turnstile-script="true"]',
        ) as HTMLScriptElement | null;

        if (existing) {
          resolve();
          return;
        }

        const script = document.createElement('script');
        script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js';
        script.async = true;
        script.defer = true;
        script.setAttribute('data-turnstile-script', 'true');
        script.onload = () => resolve();
        script.onerror = () => reject(new Error('Failed to load Turnstile script'));
        document.head.appendChild(script);
      });
    };

    loadScript()
      .then(() => {
        if (cancelled) return;
        if (!window.turnstile) return;
        if (!containerRef.current) return;

        // Ensure we don't accumulate multiple widgets in the same container
        // when the component is re-mounted or the action prop changes.
        containerRef.current.innerHTML = '';

        widgetIdRef.current = window.turnstile.render(containerRef.current, {
          sitekey: siteKey,
          action,
          callback: (token: string) => {
            onTokenChange(token);
          },
          'expired-callback': () => {
            onTokenChange(null);
          },
          'error-callback': () => {
            onTokenChange(null);
          },
        });
      })
      .catch(() => {
        onTokenChange(null);
      });

    return () => {
      cancelled = true;
      onTokenChange(null);
      try {
        if (window.turnstile && widgetIdRef.current) {
          window.turnstile.reset(widgetIdRef.current);
        }
      } catch {
        // ignore
      }
    };
  }, [action, onTokenChange]);

  useEffect(() => {
    if (!resetSignal) return;
    try {
      if (typeof window !== 'undefined' && window.turnstile && widgetIdRef.current) {
        window.turnstile.reset(widgetIdRef.current);
      }
    } catch {
      // ignore reset errors
    }
  }, [resetSignal]);

  return <div ref={containerRef} className="flex justify-center mt-4" />;
}
