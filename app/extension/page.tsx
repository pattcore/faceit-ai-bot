'use client';

import Link from 'next/link';
import { useTranslation } from 'react-i18next';

export default function ExtensionPage() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-white flex items-center justify-center animate-fade-in">
      <div className="max-w-3xl w-full mx-auto px-6 py-16">
        <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-orange-500 to-yellow-500 bg-clip-text text-transparent">
          {t('extensionPage.title')}
        </h1>
        <p className="text-lg text-gray-400 mb-8">
          {t('extensionPage.description')}
        </p>

        <div className="mb-8">
          <a
            href="/assets/prod/faceit-ai-bot-extension.zip"
            className="btn-primary inline-flex items-center justify-center px-6 py-3 text-base font-semibold"
          >
            {t('extensionPage.download_button')}
          </a>
          <p className="mt-2 text-sm text-gray-400">
            {t('extensionPage.download_hint')}
          </p>
        </div>

        <div className="space-y-8">
          <section className="card">
            <h2 className="text-2xl font-semibold mb-3">
              {t('extensionPage.features_title')}
            </h2>
            <ul className="list-disc list-inside space-y-2 text-gray-200">
              <li>{t('extensionPage.feature_open_toolbar')}</li>
              <li>{t('extensionPage.feature_analyze_from_faceit')}</li>
              <li>{t('extensionPage.feature_jump_from_steam')}</li>
            </ul>
          </section>

          <section className="card">
            <h2 className="text-2xl font-semibold mb-3">
              {t('extensionPage.install_title')}
            </h2>
            <ol className="list-decimal list-inside space-y-2 text-gray-200 text-sm md:text-base">
              <li>
                <a
                  href="https://github.com/pattcore/faceit-ai-bot"
                  target="_blank"
                  rel="noreferrer"
                  className="text-orange-400 hover:text-orange-300 underline"
                >
                  GitHub: pat1one/faceit-ai-bot
                </a>{' '}
                — {t('extensionPage.step_download_repo')}
              </li>
              <li>{t('extensionPage.step_unpack_zip')}</li>
              <li>
                <ul className="list-disc list-inside ml-5 mt-1 space-y-1 text-gray-300">
                  <li><code>chrome://extensions</code> — для Google Chrome</li>
                  <li><code>edge://extensions</code> — для Microsoft Edge</li>
                  <li><code>opera://extensions</code> — для Opera</li>
                </ul>
                <span className="block mt-1 text-gray-200 text-sm">
                  {t('extensionPage.step_open_extensions')}
                </span>
              </li>
              <li>{t('extensionPage.step_enable_dev_mode')}</li>
              <li>
                {t('extensionPage.step_load_unpacked')}
              </li>
              <li>
                {t('extensionPage.step_login_and_token')}{' '}
                <a
                  href="https://pattmsc.online"
                  target="_blank"
                  rel="noreferrer"
                  className="text-orange-400 hover:text-orange-300 underline"
                >
                  pattmsc.online
                </a>
              </li>
            </ol>
          </section>

          <section className="card">
            <h2 className="text-2xl font-semibold mb-3">
              {t('extensionPage.links_title')}
            </h2>
            <ul className="space-y-2 text-gray-200">
              <li>
                <a
                  href="https://pattmsc.online"
                  target="_blank"
                  rel="noreferrer"
                  className="text-orange-400 hover:text-orange-300 underline"
                >
                  {t('extensionPage.site_link')}: pattmsc.online
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/pat1one/faceit-ai-bot"
                  target="_blank"
                  rel="noreferrer"
                  className="text-orange-400 hover:text-orange-300 underline"
                >
                  {t('extensionPage.repo_link')}: github.com/pat1one/faceit-ai-bot
                </a>
              </li>
            </ul>
          </section>

          <div className="flex flex-wrap gap-3">
            <Link href="/" className="btn-primary">
              {t('extensionPage.cta_home')}
            </Link>
            <Link href="/analysis" className="btn-primary">
              {t('extensionPage.cta_analysis')}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
