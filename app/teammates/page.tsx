'use client';

import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import API_ENDPOINTS from '../../src/config/api';

interface TeammateProfile {
  user_id: string;
  faceit_nickname: string;
  stats?: {
    faceit_elo?: number;
    win_rate?: number;
    avg_kd?: number;
  };
  compatibility_score?: number;
  match_summary?: string;
  about?: string;
  discord_contact?: string;
  telegram_contact?: string;
  contact_url?: string;
}

export default function TeammatesPage() {
  const { user, token } = useAuth();
  const router = useRouter();
  const [filters, setFilters] = useState({ rank: '', region: '', role: '' });
  const [profile, setProfile] = useState({
    about: '',
    availability: '',
    discord_contact: '',
    telegram_contact: '',
    contact_url: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<TeammateProfile[]>([]);
  const { t, i18n } = useTranslation();
  const lang =
    i18n.language && i18n.language.toLowerCase().startsWith('en')
      ? 'en'
      : 'ru';

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-white flex items-center justify-center animate-fade-in">
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-8 text-white">{t('teammate.title')}</h1>
          <button
            onClick={() => router.push('/auth')}
            className="px-8 py-3 bg-orange-500 hover:bg-orange-600 rounded-lg font-semibold transition-colors"
          >
            {t('landing.cta_sign_in')}
          </button>
        </div>
      </div>
    );
  }

  const handleSearch = async () => {
    if (!user || !token) return;

    setLoading(true);
    setError(null);
    setResults([]);

    // Простейшее отображение фильтров в preferences
    let min_elo = 0;
    let max_elo = 10000;
    if (filters.rank === '1-5') {
      max_elo = 1500;
    } else if (filters.rank === '6-10') {
      min_elo = 1500;
      max_elo = 2500;
    } else if (filters.rank === '10+') {
      min_elo = 2000;
    }

    const preferences = {
      min_elo,
      max_elo,
      preferred_maps: [],
      preferred_roles: filters.role ? [filters.role] : [],
      communication_lang: [lang],
      play_style: 'balanced',
      time_zone: 'UTC',
      about: profile.about || undefined,
      availability: profile.availability || undefined,
      discord_contact: profile.discord_contact || undefined,
      telegram_contact: profile.telegram_contact || undefined,
      contact_url: profile.contact_url || undefined,
    };

    try {
      // Сохраняем предпочтения пользователя (профиль тиммейта)
      await fetch(API_ENDPOINTS.TEAMMATES_PREFERENCES, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(preferences),
      });

      // Ищем тиммейтов по этим же предпочтениям
      const response = await fetch(API_ENDPOINTS.TEAMMATES_SEARCH, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(preferences),
      });

      if (!response.ok) {
        const text = await response.text();
        setError(text || t('teammate.no_results'));
        return;
      }

      const data = await response.json();
      setResults(data);
    } catch (e) {
      console.error('Teammates search error', e);
      setError(t('teammate.no_results'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen px-8 py-12 bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-white animate-fade-in">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-4 gradient-text">
          👥 {t('teammate.title')}
        </h1>
        <p className="text-zinc-400 mb-8">
          {t('teammate.placeholder', {
            defaultValue:
              'ИИ поможет подобрать тиммейтов по твоему уровню Faceit и стилю игры. Сейчас поиск в бета и подбирает партнёров по рангу, роли и базовой статистике.',
          })}
        </p>

        <div className="glass-effect rounded-xl p-6 mb-8 space-y-4">
          <h2 className="text-2xl font-semibold">
            {t('teammate.my_profile_title', {
              defaultValue: 'Мой профиль для тиммейта',
            })}
          </h2>
          <p className="text-sm text-zinc-400">
            {t('teammate.my_profile_hint', {
              defaultValue:
                'Укажи контакты и пару слов о себе, чтобы тиммейты могли связаться с тобой.',
            })}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input
              type="text"
              className="px-4 py-3 glass-effect rounded-lg focus:outline-none focus:border-primary"
              placeholder={t('teammate.discord_placeholder', {
                defaultValue: 'Discord (например, user#1234)',
              })}
              value={profile.discord_contact}
              onChange={(e) =>
                setProfile((prev) => ({
                  ...prev,
                  discord_contact: e.target.value,
                }))
              }
            />
            <input
              type="text"
              className="px-4 py-3 glass-effect rounded-lg focus:outline-none focus:border-primary"
              placeholder={t('teammate.telegram_placeholder', {
                defaultValue: 'Telegram (например, @nickname)',
              })}
              value={profile.telegram_contact}
              onChange={(e) =>
                setProfile((prev) => ({
                  ...prev,
                  telegram_contact: e.target.value,
                }))
              }
            />
            <input
              type="text"
              className="px-4 py-3 glass-effect rounded-lg focus:outline-none focus:border-primary"
              placeholder={t('teammate.contact_url_placeholder', {
                defaultValue: 'Ссылка для связи (Discord/Telegram/сайт)',
              })}
              value={profile.contact_url}
              onChange={(e) =>
                setProfile((prev) => ({
                  ...prev,
                  contact_url: e.target.value,
                }))
              }
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <textarea
              className="px-4 py-3 glass-effect rounded-lg focus:outline-none focus:border-primary min-h-[96px]"
              placeholder={t('teammate.about_placeholder', {
                defaultValue: 'Пара слов о себе, стиле игры, любимых ролях...',
              })}
              value={profile.about}
              onChange={(e) =>
                setProfile((prev) => ({
                  ...prev,
                  about: e.target.value,
                }))
              }
            />
            <input
              type="text"
              className="px-4 py-3 glass-effect rounded-lg focus:outline-none focus:border-primary"
              placeholder={t('teammate.availability_placeholder', {
                defaultValue: 'Когда обычно играешь (например, вечера по МСК)',
              })}
              value={profile.availability}
              onChange={(e) =>
                setProfile((prev) => ({
                  ...prev,
                  availability: e.target.value,
                }))
              }
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <select
            className="px-4 py-3 glass-effect rounded-lg focus:outline-none focus:border-primary"
            value={filters.rank}
            onChange={(e) => setFilters({ ...filters, rank: e.target.value })}
          >
            <option value="">
              {t('teammate.filter_rank', { defaultValue: 'Faceit ранг' })}
            </option>
            <option>1-5</option>
            <option>6-10</option>
            <option>10+</option>
          </select>
          <select
            className="px-4 py-3 glass-effect rounded-lg focus:outline-none focus:border-primary"
            value={filters.region}
            onChange={(e) => setFilters({ ...filters, region: e.target.value })}
          >
            <option value="">
              {t('teammate.filter_region', { defaultValue: 'Регион' })}
            </option>
            <option>EU</option>
            <option>NA</option>
            <option>Asia</option>
          </select>
          <select
            className="px-4 py-3 glass-effect rounded-lg focus:outline-none focus:border-primary"
            value={filters.role}
            onChange={(e) => setFilters({ ...filters, role: e.target.value })}
          >
            <option value="">
              {t('teammate.filter_role', { defaultValue: 'Роль в команде' })}
            </option>
            <option>Entry Fragger</option>
            <option>Support</option>
            <option>AWPer</option>
          </select>
        </div>

        <div className="mb-6">
          <button
            onClick={handleSearch}
            className="btn-primary"
            disabled={loading}
          >
            {loading
              ? t('teammate.search_loading', { defaultValue: 'Searching...' })
              : t('teammate.search_button', { defaultValue: 'Search' })}
          </button>
        </div>

        {error && (
          <p className="text-red-400 mb-4 text-sm">{error}</p>
        )}

        {loading && (
          <div className="space-y-4 mb-4">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="glass-effect rounded-xl p-6 flex items-center justify-between animate-pulse"
              >
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 bg-gradient-to-r from-primary to-primary-dark rounded-full" />
                  <div className="space-y-2">
                    <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-32" />
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-40" />
                  </div>
                </div>
                <div className="h-8 w-24 bg-gray-300 dark:bg-gray-700 rounded-lg" />
              </div>
            ))}
          </div>
        )}

        <div className="space-y-4">
          {results.length === 0 && !loading && !error && (
            <div className="glass-effect rounded-xl p-6 text-zinc-300 text-sm">
              <p className="font-semibold mb-1">
                {t('teammate.no_results_title', {
                  defaultValue: 'Пока нет подходящих тиммейтов',
                })}
              </p>
              <p className="mb-2">
                {t('teammate.no_results', {
                  defaultValue:
                    'Попробуй изменить диапазон ранга или роль, либо просто поиграй ещё несколько матчей — мы будем расширять базу игроков и улучшать подбор.',
                })}
              </p>
              <p className="text-xs text-zinc-500">
                {t('teammate.no_results_hint', {
                  defaultValue:
                    'Сейчас поиск работает в тестовом режиме и использует только базовые показатели Faceit.',
                })}
              </p>
            </div>
          )}
          {results.map((p) => (
            <div
              key={p.user_id}
              className="glass-effect rounded-xl p-6 flex items-center justify-between transition-all duration-300 hover:-translate-y-1"
            >
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-gradient-to-r from-primary to-primary-dark rounded-full flex items-center justify-center text-2xl">
                  🎮
                </div>
                <div>
                  <h3 className="text-xl font-semibold">{p.faceit_nickname}</h3>
                  <p className="text-zinc-400">
                    {p.stats?.faceit_elo ? `ELO ${p.stats.faceit_elo}` : ''}
                  </p>
                  {typeof p.compatibility_score === 'number' && (
                    <p className="text-xs text-emerald-400 mt-1">
                      {t('teammate.compatibility', { defaultValue: 'Совместимость' })}
                      {': '}
                      {Math.round(p.compatibility_score * 100)}%
                    </p>
                  )}
                  {p.match_summary && (
                    <p className="text-sm text-zinc-300 mt-2">{p.match_summary}</p>
                  )}
                  {(p.discord_contact || p.telegram_contact || p.contact_url) && (
                    <div className="text-sm text-zinc-300 mt-2 space-y-1">
                      {p.discord_contact && (
                        <p>
                          {t('teammate.contact_discord', { defaultValue: 'Discord:' })}{' '}
                          {p.discord_contact}
                        </p>
                      )}
                      {p.telegram_contact && (
                        <p>
                          {t('teammate.contact_telegram', { defaultValue: 'Telegram:' })}{' '}
                          {p.telegram_contact}
                        </p>
                      )}
                      {p.contact_url && (
                        <p>
                          {t('teammate.contact_link', { defaultValue: 'Ссылка:' })}{' '}
                          <a
                            href={p.contact_url}
                            target="_blank"
                            rel="noreferrer"
                            className="underline text-primary"
                          >
                            {p.contact_url}
                          </a>
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>
              <button
                className="px-6 py-2 bg-gradient-to-r from-primary to-primary-dark rounded-lg font-medium"
                onClick={async () => {
                  try {
                    if (p.faceit_nickname) {
                      await navigator.clipboard.writeText(p.faceit_nickname);
                    }
                  } catch (err) {
                    console.error('Clipboard copy failed', err);
                  }
                }}
              >
                {t('teammate.add_friend_button', { defaultValue: 'Add Friend' })}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
