'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { API_ENDPOINTS } from '../../src/config/api';
import CaptchaWidget from '../../src/components/CaptchaWidget';

type PublicConfig = {
  captcha?: {
    provider?: string | null;
    turnstile_site_key?: string | null;
    smartcaptcha_site_key?: string | null;
  };
};

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [captchaToken, setCaptchaToken] = useState<string | null>(null);
  const [captchaReset, setCaptchaReset] = useState(0);
  const [captchaEnabled, setCaptchaEnabled] = useState(false);
  
  const { login, register, loginWithToken } = useAuth();
  const router = useRouter();
  const { t } = useTranslation();

  const handleCaptchaTokenChange = useCallback((token: string | null) => {
    setCaptchaToken(token);
  }, []);

  // Handle OpenID/OAuth callbacks: token & auto=1 from query params
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const url = new URL(window.location.href);
    const steamToken = url.searchParams.get('steam_token');
    const faceitToken = url.searchParams.get('faceit_token');
    const genericToken = url.searchParams.get('token');
    const auto = url.searchParams.get('auto');

    const authToken = steamToken || faceitToken || genericToken;

    if (!authToken) {
      return;
    }

    const handleExternalLogin = async () => {
      try {
        await loginWithToken(authToken);

        // Очистим токен из URL, чтобы не светился в адресной строке
        url.searchParams.delete('steam_token');
        url.searchParams.delete('faceit_token');
        url.searchParams.delete('token');
        window.history.replaceState({}, '', url.toString());

        if (auto === '1') {
          router.replace('/analysis?auto=1');
        } else {
          router.replace('/');
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '';
        setError(errorMessage || t('auth.login_failed'));
        console.error('External auth error:', err);
      }
    };

    handleExternalLogin();
  }, [loginWithToken, router, t]);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const res = await fetch('/api/public-config', {
          method: 'GET',
          credentials: 'include',
          headers: {
            Accept: 'application/json',
          },
        });

        if (!res.ok) {
          if (!cancelled) setCaptchaEnabled(false);
          return;
        }

        const cfg = (await res.json()) as PublicConfig;
        const provider = (cfg?.captcha?.provider || '').toLowerCase().trim();
        const hasTurnstileKey = !!cfg?.captcha?.turnstile_site_key;
        const hasSmartKey = !!cfg?.captcha?.smartcaptcha_site_key;

        const enabled =
          (provider === 'turnstile' && hasTurnstileKey) ||
          ((provider === 'smartcaptcha' || provider === 'yandex_smartcaptcha' || provider === 'yandex') &&
            hasSmartKey);

        if (!cancelled) setCaptchaEnabled(enabled);
      } catch {
        if (!cancelled) setCaptchaEnabled(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const handlePageShow = (event: any) => {
      try {
        if (event && (event as any).persisted) {
          setCaptchaToken(null);
          setCaptchaReset((prev) => prev + 1);
        }
      } catch {
      }
    };

    window.addEventListener('pageshow', handlePageShow);

    return () => {
      window.removeEventListener('pageshow', handlePageShow);
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (captchaEnabled && !captchaToken) {
        setError(
          t('auth.captcha_required', {
            defaultValue: 'Подтвердите, что вы не бот, выполнив проверку CAPTCHA.',
          }),
        );
        // Обновляем виджет, если пользователь попытался отправить форму без токена
        setCaptchaReset((prev) => prev + 1);
        setLoading(false);
        return;
      }

      if (isLogin) {
        await login(email, password, captchaToken);
      } else {
        await register(email, username, password, captchaToken);
      }

      // Считаем токен израсходованным для обычного логина/регистрации
      setCaptchaToken(null);
      setCaptchaReset((prev) => prev + 1);

      router.push('/');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '';
      let message = errorMessage;

      if (message) {
        const lower = message.toLowerCase();

        if (lower.includes('captcha verification failed')) {
          message = t('auth.captcha_failed', {
            defaultValue:
              'Проверка CAPTCHA не пройдена. Пожалуйста, попробуйте ещё раз.',
          });
        } else if (
          lower.includes('rate limit exceeded') ||
          lower.includes('too many requests') ||
          lower.includes('access temporarily blocked') ||
          lower.includes('превышен лимит') ||
          lower.includes('достигнут дневной лимит')
        ) {
          message = t('auth.error_rate_limited', {
            defaultValue:
              'Слишком много запросов. Доступ временно ограничен, попробуйте позже.',
          });
        }
      }

      setError(
        message ||
          (isLogin
            ? t('auth.login_failed')
            : t('auth.register_failed'))
      );
      console.error('Auth error:', err);

      // После любой ошибки сбрасываем капчу, чтобы пользователь мог пройти её заново
      setCaptchaToken(null);
      setCaptchaReset((prev) => prev + 1);
    } finally {
      setLoading(false);
    }
  };

  const handleSteamLoginClick = () => {
    if (captchaEnabled && !captchaToken) {
      setError(
        t('auth.captcha_required', {
          defaultValue: 'Подтвердите, что вы не бот, выполнив проверку CAPTCHA.',
        }),
      );
      // Просим пользователя пройти капчу ещё раз
      setCaptchaReset((prev) => prev + 1);
      return;
    }

    const baseUrl = API_ENDPOINTS.AUTH_STEAM_LOGIN;
    const token = captchaToken;

    try {
      const url = new URL(baseUrl, window.location.origin);
      if (token) {
        url.searchParams.set('captcha_token', token);
      }
      // считаем токен израсходованным при клике по внешнему логину
      setCaptchaToken(null);
      setCaptchaReset((prev) => prev + 1);
      window.location.href = url.toString();
    } catch {
      if (token) {
        const separator = baseUrl.includes('?') ? '&' : '?';
        window.location.href = `${baseUrl}${separator}captcha_token=${encodeURIComponent(
          token,
        )}`;
      } else {
        window.location.href = baseUrl;
      }
      // на всякий случай тоже обнуляем токен, если редирект не сработал как ожидалось
      setCaptchaToken(null);
      setCaptchaReset((prev) => prev + 1);
    }
  };

  const handleFaceitLoginClick = () => {
    if (captchaEnabled && !captchaToken) {
      setError(
        t('auth.captcha_required', {
          defaultValue: 'Подтвердите, что вы не бот, выполнив проверку CAPTCHA.',
        }),
      );
      setCaptchaReset((prev) => prev + 1);
      return;
    }

    const baseUrl = API_ENDPOINTS.AUTH_FACEIT_LOGIN;
    const token = captchaToken;

    try {
      const url = new URL(baseUrl, window.location.origin);
      if (token) {
        url.searchParams.set('captcha_token', token);
      }
      setCaptchaToken(null);
      setCaptchaReset((prev) => prev + 1);
      window.location.href = url.toString();
    } catch {
      if (token) {
        const separator = baseUrl.includes('?') ? '&' : '?';
        window.location.href = `${baseUrl}${separator}captcha_token=${encodeURIComponent(
          token,
        )}`;
      } else {
        window.location.href = baseUrl;
      }
      setCaptchaToken(null);
      setCaptchaReset((prev) => prev + 1);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-20">
      <div className="card w-full max-w-md">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-white text-center mb-2">
            {isLogin ? t('auth.title_login') : t('auth.title_register')}
          </h2>
          <p className="text-gray-400 text-center mb-8">
            {isLogin
              ? t('auth.subtitle_login')
              : t('auth.subtitle_register')}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              {t('auth.email_label')}
            </label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t('auth.email_placeholder')}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-500"
              required
            />
          </div>

          {!isLogin && (
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t('auth.username_label')}
              </label>
              <input 
                type="text" 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder={t('auth.username_placeholder')}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-500"
                required
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              {t('auth.password_label')}
            </label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t('auth.password_placeholder')}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-500"
              required
              minLength={8}
            />
          </div>

          <div>
            <CaptchaWidget
              onTokenChange={handleCaptchaTokenChange}
              action={isLogin ? 'auth_login' : 'auth_register'}
              resetSignal={captchaReset}
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 text-sm">
              {error}
            </div>
          )}

          <button 
            type="submit" 
            className="w-full btn-primary"
            disabled={loading}
          >
            {loading
              ? t('auth.loading')
              : isLogin
                ? t('auth.login_button')
                : t('auth.register_button')}
          </button>
        </form>

        <div className="mt-6">
          <div className="flex items-center my-4">
            <div className="flex-grow border-t border-gray-700" />
            <span className="mx-3 text-gray-400 text-sm">
              {t('auth.or', 'or')}
            </span>
            <div className="flex-grow border-t border-gray-700" />
          </div>

          <button
            type="button"
            onClick={handleSteamLoginClick}
            className="w-full flex items-center justify-center gap-2 bg-gray-800 hover:bg-gray-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
            disabled={loading}
          >
            <span>🎮</span>
            <span>{t('auth.login_with_steam', 'Sign in with Steam')}</span>
          </button>

          <div className="mt-3" />

          <button
            type="button"
            onClick={handleFaceitLoginClick}
            className="w-full flex items-center justify-center gap-2 bg-gray-800 hover:bg-gray-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
            disabled={loading}
          >
            <span>⚔️</span>
            <span>{t('auth.login_with_faceit', 'Sign in with FACEIT')}</span>
          </button>
        </div>

        <div className="mt-6 text-center">
          <p className="text-center text-gray-400">
            {isLogin
              ? t('auth.no_account')
              : t('auth.have_account')}
            {' '}
            <button 
              onClick={() => {
                setIsLogin(!isLogin);
                setCaptchaToken(null);
                setCaptchaReset((prev) => prev + 1);
                setError('');
              }} 
              className="text-orange-500 hover:text-orange-400 underline"
            >
              {isLogin
                ? t('auth.switch_to_register')
                : t('auth.switch_to_login')}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
