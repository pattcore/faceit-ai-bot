'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { API_ENDPOINTS } from '../../src/config/api';
import TurnstileWidget from '../../src/components/TurnstileWidget';

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [captchaToken, setCaptchaToken] = useState<string | null>(null);
  
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const turnstileEnabled = !!process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;

      if (turnstileEnabled && !captchaToken) {
        setError(
          t('auth.captcha_required', {
            defaultValue: 'Подтвердите, что вы не бот, выполнив проверку CAPTCHA.',
          }),
        );
        setLoading(false);
        return;
      }

      if (isLogin) {
        await login(email, password, captchaToken);
      } else {
        await register(email, username, password, captchaToken);
      }
      router.push('/');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '';
      setError(
        errorMessage ||
          (isLogin
            ? t('auth.login_failed')
            : t('auth.register_failed'))
      );
      console.error('Auth error:', err);
    } finally {
      setLoading(false);
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
              minLength={6}
            />
          </div>

          <div>
            <TurnstileWidget onTokenChange={handleCaptchaTokenChange} action={isLogin ? 'auth_login' : 'auth_register'} />
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
            onClick={() => {
              window.location.href = API_ENDPOINTS.AUTH_STEAM_LOGIN;
            }}
            className="w-full flex items-center justify-center gap-2 bg-gray-800 hover:bg-gray-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
            disabled={loading}
          >
            <span>🎮</span>
            <span>{t('auth.login_with_steam', 'Sign in with Steam')}</span>
          </button>

          <div className="mt-3" />

          <button
            type="button"
            onClick={() => {
              window.location.href = API_ENDPOINTS.AUTH_FACEIT_LOGIN;
            }}
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
              onClick={() => setIsLogin(!isLogin)} 
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
