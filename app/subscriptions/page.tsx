'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/navigation';
import API_ENDPOINTS from '../../src/config/api';
import { useTranslation } from 'react-i18next';
import CaptchaWidget from '../../src/components/CaptchaWidget';

export default function SubscriptionsPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [loadingTier, setLoadingTier] = useState<string | null>(null);
  const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const { t, i18n } = useTranslation();
  const [captchaToken, setCaptchaToken] = useState<string | null>(null);
  const [captchaReset, setCaptchaReset] = useState(0);

  const plans = [
    { tier: 'FREE', price: 0, popular: false },
    { tier: 'BASIC', price: 299, popular: false },
    { tier: 'PRO', price: 599, popular: true },
    { tier: 'ELITE', price: 999, popular: false }
  ] as const;

  const [usdRate, setUsdRate] = useState<number | null>(null);

  useEffect(() => {
    // For English UI show approximate USD equivalent based on current FX rate
    if (!i18n.language.startsWith('en')) {
      setUsdRate(null);
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        const res = await fetch('https://api.exchangerate.host/latest?base=RUB&symbols=USD');
        if (!res.ok) return;
        const data = await res.json();
        const rate = data?.rates?.USD;
        if (!cancelled && typeof rate === 'number' && rate > 0) {
          setUsdRate(rate);
        }
      } catch (err) {
        console.error('Failed to load FX rate', err);
        if (!cancelled) setUsdRate(null);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [i18n.language]);

  const handleCaptchaTokenChange = useCallback((token: string | null) => {
    setCaptchaToken(token);
  }, []);

  const handleSelect = async (tier: string, price: number) => {
    if (!user) {
      router.push('/auth');
      return;
    }

    if (price === 0) {
      // Здесь можно дернуть /subscriptions/{user_id}, чтобы зафиксировать FREE-подписку
      setStatus({ type: 'success', message: t('subscription.free_label') });
      return;
    }

    try {
      setLoadingTier(tier);

      const captchaProvider = process.env.NEXT_PUBLIC_CAPTCHA_PROVIDER?.toLowerCase();
      const captchaEnabled = !!captchaProvider;

      if (captchaEnabled && !captchaToken) {
        setStatus({
          type: 'error',
          message: t('auth.captcha_required', {
            defaultValue: 'Подтвердите, что вы не бот, выполнив проверку CAPTCHA.',
          }),
        });
        setCaptchaReset((prev) => prev + 1);
        setLoadingTier(null);
        return;
      }

      const token = captchaToken;

      const response = await fetch(API_ENDPOINTS.PAYMENTS_CREATE, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: String(user.id),
          subscription_tier: tier.toLowerCase(),
          amount: price,
          currency: 'RUB',
          payment_method: 'sbp',
          provider: 'sbp',
          description: `Подписка ${tier} для пользователя ${user.id}`,
          captcha_token: token,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Payment create error:', errorText);
        setStatus({ type: 'error', message: errorText || t('demo.error_sbp') });

        // При ошибке оплаты отправляем на страницу неуспешного платежа
        const failUrl = `https://pattmsc.online/payment/fail?subscription=${tier.toLowerCase()}`;
        window.location.href = failUrl;
        return;
      }

      await response.json();

      // Считаем токен капчи израсходованным для платежа
      setCaptchaToken(null);
      setCaptchaReset((prev) => prev + 1);
      const targetUrl = `https://pattmsc.online/payment/success?subscription=${tier.toLowerCase()}`;
      window.location.href = targetUrl;
    } catch (error) {
      console.error('Payment error:', error);
      setStatus({ type: 'error', message: t('demo.error_sbp') });

      // Любая сетевая ошибка также ведёт на страницу неуспешного платежа
      const failUrl = `https://pattmsc.online/payment/fail?subscription=${tier.toLowerCase()}`;
      window.location.href = failUrl;
    } finally {
      setLoadingTier(null);
    }
  };

  return (
    <div className="min-h-screen py-20 px-6 bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-white animate-fade-in">
      <div className="max-w-6xl mx-auto">
        {user && (
          <div className="mb-8 flex justify-center">
            <CaptchaWidget
              onTokenChange={handleCaptchaTokenChange}
              action="payment_create"
              resetSignal={captchaReset}
            />
          </div>
        )}
        {status && (
          <div
            className={`mb-8 px-4 py-3 rounded-lg text-sm border ${
              status.type === 'error'
                ? 'bg-red-50 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-100 dark:border-red-700'
                : 'bg-green-50 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-100 dark:border-green-700'
            }`}
          >
            {status.message}
          </div>
        )}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold hero-gradient mb-6">{t('subscription.title')}</h1>
          <p className="text-xl text-gray-300">{t('subscription.subtitle')}</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map((plan) => {
            const features = t(`subscription.plans.${plan.tier}.features`, { returnObjects: true }) as string[];
            return (
              <div key={plan.tier} className={`card animate-fade-in-up ${plan.popular ? 'ring-2 ring-orange-500' : ''}`}>
                {plan.popular && (
                  <div className="text-center mb-4">
                    <span className="bg-orange-500 text-white px-3 py-1 rounded-full text-sm">
                      {t('subscription.popular_badge')}
                    </span>
                  </div>
                )}
                
                <div className="text-center mb-6">
                  <h3 className="text-2xl font-bold text-white mb-2">{plan.tier}</h3>
                  <div className="text-3xl font-bold text-white mb-4">
                    {plan.price === 0
                      ? t('subscription.free_label')
                      : (() => {
                          const isEn = i18n.language.startsWith('en');
                          const rubPrice = plan.price;

                          // For English UI show approximate USD price.
                          // Use live FX rate when available, otherwise fall back to a static rate.
                          if (isEn) {
                            const effectiveRate =
                              typeof usdRate === 'number' && usdRate > 0
                                ? usdRate
                                : 0.011; // fallback RUB→USD
                            const usdPrice = (rubPrice * effectiveRate).toFixed(2);
                            return t('subscription.per_month', { price: usdPrice });
                          }

                          // Non-English locales keep RUB price
                          return t('subscription.per_month', { price: rubPrice });
                        })()}
                  </div>
                </div>

                <ul className="space-y-2 mb-6">
                  {features.map((feature, i) => (
                    <li key={i} className="text-gray-300 flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      {feature}
                  </li>
                ))}
              </ul>

                <button
                  onClick={() => handleSelect(plan.tier, plan.price)}
                  className="w-full btn-primary disabled:opacity-60"
                  disabled={loadingTier === plan.tier}
                >
                  {loadingTier === plan.tier
                    ? t('subscription.button_loading')
                    : t('subscription.button_select')}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
