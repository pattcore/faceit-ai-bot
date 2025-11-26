'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useAuth } from '../../app/contexts/AuthContext';
import LanguageSwitcher from './LanguageSwitcher';
import ThemeSwitcher from './ThemeSwitcher';
import { useTranslation } from 'react-i18next';

const Navigation = () => {
  const { user, logout } = useAuth();
  const { t } = useTranslation();

  return (
    <nav className="fixed top-0 left-0 right-0 bg-white/80 dark:bg-gray-900/95 backdrop-blur-lg border-b border-gray-200 dark:border-gray-800 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 text-xl font-bold text-gray-900 dark:text-white hover:opacity-80 transition-opacity">
          <Image src="/icon.svg" width={28} height={28} alt="Faceit AI Bot" />
          <span>Faceit AI Bot</span>
        </Link>

        <div className="hidden md:flex gap-8 flex-1 justify-center">
          <Link href="/" className="text-gray-700 dark:text-gray-300 font-medium hover:text-gray-900 dark:hover:text-white transition-colors">
            {t('nav.home')}
          </Link>
          <Link href="/demo" className="text-gray-700 dark:text-gray-300 font-medium hover:text-gray-900 dark:hover:text-white transition-colors">
            {t('nav.demo')}
          </Link>
          <Link href="/teammates" className="text-gray-700 dark:text-gray-300 font-medium hover:text-gray-900 dark:hover:text-white transition-colors">
            {t('nav.teammates')}
          </Link>
          <Link href="/subscriptions" className="text-gray-700 dark:text-gray-300 font-medium hover:text-gray-900 dark:hover:text-white transition-colors">
            {t('nav.subscriptions')}
          </Link>
          {user && (
            <>
              <Link href="/analysis" className="text-gray-700 dark:text-gray-300 font-medium hover:text-gray-900 dark:hover:text-white transition-colors">
                {t('nav.player_analysis', { defaultValue: 'Player Analysis' })}
              </Link>
              <Link href="/dashboard" className="text-gray-700 dark:text-gray-300 font-medium hover:text-gray-900 dark:hover:text-white transition-colors">
                {t('nav.dashboard')}
              </Link>
              {user.is_admin && (
                <Link
                  href="/admin/rate-limit"
                  className="text-orange-500 dark:text-orange-400 font-medium hover:text-orange-600 dark:hover:text-orange-300 transition-colors"
                >
                  {t('nav.admin_rate_limit', { defaultValue: 'Admin (rate limit)' })}
                </Link>
              )}
            </>
          )}
        </div>

        <div className="flex items-center gap-4">
          <ThemeSwitcher />
          <LanguageSwitcher />
          {user ? (
            <div className="flex items-center gap-3">
              <Link
                href="/dashboard"
                className="flex items-center gap-2 px-3 py-1 rounded-full bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 text-sm font-medium"
              >
                <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-orange-500 text-white text-xs font-bold">
                  {(user.username || user.email || '?')[0]?.toUpperCase()}
                </span>
                <span>{user.username || user.email}</span>
              </Link>
              <button
                onClick={logout}
                className="px-3 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white font-medium text-sm transition-colors"
              >
                {t('nav.logout', { defaultValue: 'Logout' })}
              </button>
            </div>
          ) : (
            <>
              <Link
                href="/auth"
                className="px-6 py-2 bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg text-white font-semibold transition-colors"
              >
                {t('nav.login')}
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;