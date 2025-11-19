'use client';

import Link from 'next/link';
import { useAuth } from './contexts/AuthContext';
import { useTranslation } from 'react-i18next';

export default function HomePage() {
  const { user } = useAuth();
  const { t, i18n } = useTranslation();
  const lang =
    i18n.language && i18n.language.toLowerCase().startsWith('en')
      ? 'en'
      : 'ru';

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-white animate-fade-in">
      <div className="text-center mb-16">
        <h1 className="text-6xl font-bold mb-6 bg-gradient-to-r from-orange-500 to-yellow-500 bg-clip-text text-transparent">
          {t('landing.title')}
        </h1>
        <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
          {t('landing.subtitle')}
        </p>
        
        <div className="flex flex-wrap gap-4 justify-center mb-16">
          {user ? (
            <>
              <Link
                href="/demo"
                className="btn-primary"
              >
                {t('demo.title')}
              </Link>
              <Link
                href="/subscriptions"
                className="btn-primary"
              >
                {t('subscription.title')}
              </Link>
              <Link
                href="/demo/example"
                className="btn-primary"
              >
                {t('landing.cta_demo_example', {
                  defaultValue:
                    lang === 'en'
                      ? 'View demo analysis example'
                      : 'Посмотреть пример анализа',
                })}
              </Link>
            </>
          ) : (
            <>
              <Link
                href="/auth"
                className="btn-primary"
              >
                {t('landing.cta_get_started')}
              </Link>
              <Link
                href="/auth"
                className="btn-primary"
              >
                {t('landing.cta_sign_in')}
              </Link>
              <Link
                href="/demo/example"
                className="btn-primary"
              >
                {t('landing.cta_demo_example', {
                  defaultValue:
                    lang === 'en'
                      ? 'View demo analysis example'
                      : 'Посмотреть пример анализа',
                })}
              </Link>
            </>
          )}
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto px-6">
        <Link
          href="/demo"
          className="card text-center block animate-fade-in-up"
        >
          <div className="text-4xl mb-4 text-blue-400">📊</div>
          <h3 className="text-xl font-bold mb-3 text-gray-900 dark:text-white">{t('landing.feature_demo_title')}</h3>
          <p className="text-gray-600 dark:text-gray-400">{t('landing.feature_demo_desc')}</p>
        </Link>
        
        <Link
          href="/analysis"
          className="card text-center block animate-fade-in-up"
        >
          <div className="text-4xl mb-4 text-red-400">🎯</div>
          <h3 className="text-xl font-bold mb-3 text-gray-900 dark:text-white">{t('landing.feature_stats_title')}</h3>
          <p className="text-gray-600 dark:text-gray-400">{t('landing.feature_stats_desc')}</p>
        </Link>
        
        <Link
          href="/teammates"
          className="card text-center block animate-fade-in-up"
        >
          <div className="text-4xl mb-4 text-blue-400">👥</div>
          <h3 className="text-xl font-bold mb-3 text-gray-900 dark:text-white">{t('landing.feature_team_title')}</h3>
          <p className="text-gray-600 dark:text-gray-400">{t('landing.feature_team_desc')}</p>
        </Link>
      </div>
    </div>
  );
}
