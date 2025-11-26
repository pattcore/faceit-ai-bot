'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';

import { useAuth } from '../../contexts/AuthContext';
import API_ENDPOINTS from '../../../src/config/api';

type BanKind = 'ip' | 'user';

interface Ban {
  type: BanKind;
  value: string;
  ttl: number | null;
}

interface Violation {
  type: BanKind;
  value: string;
  count: number;
  ttl: number | null;
}

interface RateLimitConfig {
  requests_per_minute: number;
  requests_per_hour: number;
  ban_enabled: boolean;
  ban_threshold: number;
  ban_window_seconds: number;
  ban_ttl_seconds: number;
}

interface ConfigResponse {
  redis_enabled?: boolean;
  rate_limit?: RateLimitConfig;
  detail?: unknown;
}

interface BansResponse {
  enabled?: boolean;
  bans?: Ban[];
  detail?: unknown;
}

interface ViolationsResponse {
  enabled?: boolean;
  violations?: Violation[];
  detail?: unknown;
}

export default function AdminRateLimitPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const { t } = useTranslation();

  const [bans, setBans] = useState<Ban[]>([]);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [bansEnabled, setBansEnabled] = useState<boolean | null>(null);
  const [violationsEnabled, setViolationsEnabled] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [config, setConfig] = useState<RateLimitConfig | null>(null);
  const [configRedisEnabled, setConfigRedisEnabled] = useState<boolean | null>(null);

  const [formKind, setFormKind] = useState<BanKind>('ip');
  const [formValue, setFormValue] = useState('');
  const [formLoading, setFormLoading] = useState(false);
  const [filterType, setFilterType] = useState<'all' | BanKind>('all');
  const [searchValue, setSearchValue] = useState('');
  const [cleanupLoading, setCleanupLoading] = useState(false);

  const formatTtl = (ttl: number | null | undefined): string => {
    if (ttl == null || ttl < 0) {
      return t('adminRateLimit.ttl_infinite', {
        defaultValue: 'без ограничения',
      });
    }

    if (ttl === 0) {
      return t('adminRateLimit.ttl_expired', {
        defaultValue: 'истёк',
      });
    }

    if (ttl < 60) {
      return t('adminRateLimit.ttl_seconds', {
        count: ttl,
        defaultValue: '{{count}} с',
      });
    }

    const minutes = Math.round(ttl / 60);
    if (minutes < 60) {
      return t('adminRateLimit.ttl_minutes', {
        count: minutes,
        defaultValue: '{{count}} мин',
      });
    }

    const hours = Math.round(minutes / 60);
    return t('adminRateLimit.ttl_hours', {
      count: hours,
      defaultValue: '{{count}} ч',
    });
  };

  const extractErrorMessage = async (response: Response): Promise<string> => {
    try {
      const text = await response.text();
      if (!text) {
        return response.statusText || 'Request failed';
      }

      try {
        const data = JSON.parse(text);
        const detail: any = (data && (data.detail ?? data)) as any;

        if (typeof detail === 'string') {
          return detail;
        }
        if (detail && typeof detail === 'object') {
          return (
            (detail.error as string) ||
            (detail.message as string) ||
            (detail.detail as string) ||
            text
          );
        }

        return text;
      } catch {
        return text;
      }
    } catch {
      return response.statusText || 'Request failed';
    }
  };

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [bansRes, violRes, configRes] = await Promise.all([
        fetch(API_ENDPOINTS.ADMIN_RATE_LIMIT_BANS, {
          credentials: 'include',
        }),
        fetch(API_ENDPOINTS.ADMIN_RATE_LIMIT_VIOLATIONS, {
          credentials: 'include',
        }),
        fetch(API_ENDPOINTS.ADMIN_RATE_LIMIT_CONFIG, {
          credentials: 'include',
        }),
      ]);

      if (
        bansRes.status === 401 ||
        bansRes.status === 403 ||
        violRes.status === 401 ||
        violRes.status === 403 ||
        configRes.status === 401 ||
        configRes.status === 403
      ) {
        const message = t('adminRateLimit.error_forbidden', {
          defaultValue:
            'Нет доступа. Зайдите под админской учётной записью или проверьте права.',
        });
        setError(message);
        return;
      }

      const bansJson = (await bansRes.json()) as BansResponse;
      const violJson = (await violRes.json()) as ViolationsResponse;

      let configJson: ConfigResponse | null = null;
      if (configRes.ok) {
        try {
          configJson = (await configRes.json()) as ConfigResponse;
        } catch (configError) {
          console.error('Failed to parse rate limit config', configError);
        }
      }

      setBansEnabled(Boolean(bansJson.enabled));
      setViolationsEnabled(Boolean(violJson.enabled));
      setBans(Array.isArray(bansJson.bans) ? bansJson.bans : []);
      setViolations(
        Array.isArray(violJson.violations) ? violJson.violations : [],
      );

      if (configJson && configJson.rate_limit) {
        setConfig(configJson.rate_limit);
      } else {
        setConfig(null);
      }

      if (typeof configJson?.redis_enabled === 'boolean') {
        setConfigRedisEnabled(configJson.redis_enabled);
      } else {
        setConfigRedisEnabled(null);
      }
    } catch (e) {
      console.error('Failed to load rate limit admin data', e);
      setError(
        t('adminRateLimit.error_load', {
          defaultValue:
            'Не удалось загрузить данные rate limit. Попробуйте ещё раз позже.',
        }),
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading && user?.is_admin) {
      loadData();
    }
  }, [authLoading, user]);

  const handleCreateBan = async (event: React.FormEvent) => {
    event.preventDefault();

    const value = formValue.trim();
    if (!value) {
      setError(
        t('adminRateLimit.error_value_required', {
          defaultValue: 'Укажите IP или user id для бана.',
        }),
      );
      return;
    }

    setFormLoading(true);
    setError(null);

    try {
      const res = await fetch(
        API_ENDPOINTS.ADMIN_RATE_LIMIT_BAN(formKind, value),
        {
          method: 'POST',
          credentials: 'include',
        },
      );

      if (!res.ok) {
        if (res.status === 401 || res.status === 403) {
          setError(
            t('adminRateLimit.error_forbidden', {
              defaultValue:
                'Нет доступа. Зайдите под админской учётной записью или проверьте права.',
            }),
          );
          return;
        }

        const message = await extractErrorMessage(res);
        setError(
          t('adminRateLimit.error_create_ban', {
            defaultValue: 'Не удалось создать бан: {{message}}',
            message,
          }),
        );
        return;
      }

      setFormValue('');
      await loadData();
    } catch (e) {
      console.error('Failed to create rate limit ban', e);
      setError(
        t('adminRateLimit.error_create_ban_generic', {
          defaultValue: 'Не удалось создать бан. Попробуйте позже.',
        }),
      );
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteBan = async (kind: BanKind, value: string) => {
    setError(null);

    try {
      const res = await fetch(
        API_ENDPOINTS.ADMIN_RATE_LIMIT_BAN(kind, value),
        {
          method: 'DELETE',
          credentials: 'include',
        },
      );

      if (!res.ok) {
        if (res.status === 401 || res.status === 403) {
          setError(
            t('adminRateLimit.error_forbidden', {
              defaultValue:
                'Нет доступа. Зайдите под админской учётной записью или проверьте права.',
            }),
          );
          return;
        }

        const message = await extractErrorMessage(res);
        setError(
          t('adminRateLimit.error_delete_ban', {
            defaultValue: 'Не удалось снять бан: {{message}}',
            message,
          }),
        );
        return;
      }

      await loadData();
    } catch (e) {
      console.error('Failed to delete rate limit ban', e);
      setError(
        t('adminRateLimit.error_delete_ban_generic', {
          defaultValue: 'Не удалось снять бан. Попробуйте позже.',
        }),
      );
    }
  };

  const handleCreateBanFromViolation = async (violation: Violation) => {
    const value = violation.value.trim();
    if (!value) {
      return;
    }

    setFormLoading(true);
    setError(null);

    try {
      const res = await fetch(
        API_ENDPOINTS.ADMIN_RATE_LIMIT_BAN(violation.type, value),
        {
          method: 'POST',
          credentials: 'include',
        },
      );

      if (!res.ok) {
        if (res.status === 401 || res.status === 403) {
          setError(
            t('adminRateLimit.error_forbidden', {
              defaultValue:
                'Нет доступа. Зайдите под админской учётной записью или проверьте права.',
            }),
          );
          return;
        }

        const message = await extractErrorMessage(res);
        setError(
          t('adminRateLimit.error_create_ban', {
            defaultValue: 'Не удалось создать бан: {{message}}',
            message,
          }),
        );
        return;
      }

      await loadData();
    } catch (e) {
      console.error('Failed to create rate limit ban from violation', e);
      setError(
        t('adminRateLimit.error_create_ban_generic', {
          defaultValue: 'Не удалось создать бан. Попробуйте позже.',
        }),
      );
    } finally {
      setFormLoading(false);
    }
  };

  const handleCleanupViolations = async () => {
    if (violations.length === 0) {
      return;
    }

    setError(null);
    setCleanupLoading(true);

    try {
      const res = await fetch(
        API_ENDPOINTS.ADMIN_RATE_LIMIT_VIOLATIONS_CLEANUP,
        {
          method: 'POST',
          credentials: 'include',
        },
      );

      if (!res.ok) {
        if (res.status === 401 || res.status === 403) {
          setError(
            t('adminRateLimit.error_forbidden', {
              defaultValue:
                'Нет доступа. Зайдите под админской учётной записью или проверьте права.',
            }),
          );
          return;
        }

        const message = await extractErrorMessage(res);
        setError(
          t('adminRateLimit.error_cleanup_violations', {
            defaultValue: 'Не удалось очистить нарушения: {{message}}',
            message,
          }),
        );
        return;
      }

      await loadData();
    } catch (e) {
      console.error('Failed to cleanup rate limit violations', e);
      setError(
        t('adminRateLimit.error_cleanup_violations_generic', {
          defaultValue: 'Не удалось очистить нарушения. Попробуйте позже.',
        }),
      );
    } finally {
      setCleanupLoading(false);
    }
  };

  const normalizedSearch = searchValue.trim().toLowerCase();
  const filteredBans = bans.filter((ban) => {
    if (filterType !== 'all' && ban.type !== filterType) {
      return false;
    }
    if (normalizedSearch && !ban.value.toLowerCase().includes(normalizedSearch)) {
      return false;
    }
    return true;
  });

  const filteredViolations = violations.filter((viol) => {
    if (filterType !== 'all' && viol.type !== filterType) {
      return false;
    }
    if (
      normalizedSearch &&
      !viol.value.toLowerCase().includes(normalizedSearch)
    ) {
      return false;
    }
    return true;
  });

  if (!authLoading && !user) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6 py-20">
        <div className="card w-full max-w-md text-center">
          <h2 className="text-2xl font-bold text-white mb-4">
            {t('adminRateLimit.login_required_title', {
              defaultValue: 'Только для админов',
            })}
          </h2>
          <p className="text-gray-400 mb-6">
            {t('adminRateLimit.login_required_text', {
              defaultValue:
                'Эта страница доступна только авторизованным пользователям.',
            })}
          </p>
          <button
            type="button"
            onClick={() => router.push('/auth')}
            className="btn-primary w-full"
          >
            {t('adminRateLimit.login_button', {
              defaultValue: 'Войти',
            })}
          </button>
        </div>
      </div>
    );
  }

  if (!authLoading && user && !user.is_admin) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6 py-20">
        <div className="card w-full max-w-md text-center">
          <h2 className="text-2xl font-bold text-white mb-4">
            {t('adminRateLimit.no_admin_title', {
              defaultValue: 'Нет доступа',
            })}
          </h2>
          <p className="text-gray-400 mb-6">
            {t('adminRateLimit.no_admin_text', {
              defaultValue: 'Эта страница доступна только администраторам.',
            })}
          </p>
          <button
            type="button"
            onClick={() => router.push('/')}
            className="btn-primary w-full"
          >
            {t('adminRateLimit.back_button', {
              defaultValue: 'На главную',
            })}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-6 py-10 flex justify-center bg-gray-900 text-white">
      <div className="w-full max-w-5xl space-y-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">
            {t('adminRateLimit.title', {
              defaultValue: 'Управление rate limit',
            })}
          </h1>
          <p className="text-gray-400">
            {t('adminRateLimit.subtitle', {
              defaultValue:
                'Просмотр и ручное управление банами и нарушениями rate limit.',
            })}
          </p>
        </div>

        {config && (
          <div className="card p-4 bg-gray-800/60 border border-gray-700 rounded-xl">
            <h2 className="text-lg font-semibold mb-2">
              {t('adminRateLimit.config_title', {
                defaultValue: 'Текущие настройки rate limit',
              })}
            </h2>
            <div className="grid sm:grid-cols-2 gap-2 text-sm text-gray-200">
              <div>
                {t('adminRateLimit.config_requests_per_minute', {
                  defaultValue: 'Лимит в минуту:',
                })}{' '}
                <span className="font-mono">
                  {config.requests_per_minute}
                </span>
              </div>
              <div>
                {t('adminRateLimit.config_requests_per_hour', {
                  defaultValue: 'Лимит в час:',
                })}{' '}
                <span className="font-mono">
                  {config.requests_per_hour}
                </span>
              </div>
              <div>
                {t('adminRateLimit.config_ban_enabled', {
                  defaultValue: 'Автобан:',
                })}{' '}
                <span className="font-mono">
                  {config.ban_enabled
                    ? t('adminRateLimit.config_ban_on', {
                        defaultValue: 'включён',
                      })
                    : t('adminRateLimit.config_ban_off', {
                        defaultValue: 'выключен',
                      })}
                </span>
              </div>
              <div>
                {t('adminRateLimit.config_ban_rule', {
                  defaultValue: 'Порог автобана:',
                })}{' '}
                <span className="font-mono">
                  {config.ban_threshold} / {config.ban_window_seconds}{' '}
                  {t('adminRateLimit.config_seconds', {
                    defaultValue: 'с',
                  })}{' '}
                  → {config.ban_ttl_seconds}{' '}
                  {t('adminRateLimit.config_seconds', {
                    defaultValue: 'с',
                  })}
                </span>
              </div>
            </div>
            <div className="mt-3 text-sm">
              <span
                className={
                  configRedisEnabled
                    ? 'text-green-400'
                    : configRedisEnabled === false
                    ? 'text-red-400'
                    : 'text-gray-400'
                }
              >
                {t('adminRateLimit.config_redis_status', {
                  defaultValue: 'Статус Redis: ',
                })}
                {configRedisEnabled === null &&
                  t('adminRateLimit.config_redis_unknown', {
                    defaultValue: 'нет данных',
                  })}
                {configRedisEnabled === true &&
                  t('adminRateLimit.config_redis_on', {
                    defaultValue: 'подключен',
                  })}
                {configRedisEnabled === false &&
                  t('adminRateLimit.config_redis_off', {
                    defaultValue: 'не подключен',
                  })}
              </span>
            </div>
          </div>
        )}

        {error && (
          <div className="p-3 bg-red-900/40 border border-red-700 rounded-lg text-sm text-red-200">
            {error}
          </div>
        )}

        {(!bansEnabled || !violationsEnabled) && (
          <div className="p-3 bg-yellow-900/30 border border-yellow-700 rounded-lg text-sm text-yellow-200">
            {t('adminRateLimit.redis_disabled', {
              defaultValue:
                'Redis rate limiting не активен или кеш не подключен. Данные могут быть неполными.',
            })}
          </div>
        )}

        <div className="card p-4 bg-gray-800/60 border border-gray-700 rounded-xl">
          <h2 className="text-lg font-semibold">
            {t('adminRateLimit.filters_title', {
              defaultValue: 'Фильтры',
            })}
          </h2>
          <div className="mt-3 flex flex-col md:flex-row gap-3">
            <div className="flex flex-col">
              <label className="text-sm text-gray-300 mb-1">
                {t('adminRateLimit.filter_type_label', {
                  defaultValue: 'Тип (IP/User)',
                })}
              </label>
              <select
                value={filterType}
                onChange={(e) =>
                  setFilterType(e.target.value as 'all' | BanKind)
                }
                className="px-3 py-2 rounded-md bg-gray-900 border border-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
              >
                <option value="all">
                  {t('adminRateLimit.filter_type_all', {
                    defaultValue: 'Все',
                  })}
                </option>
                <option value="ip">
                  {t('adminRateLimit.filter_type_ip', {
                    defaultValue: 'Только IP',
                  })}
                </option>
                <option value="user">
                  {t('adminRateLimit.filter_type_user', {
                    defaultValue: 'Только пользователи',
                  })}
                </option>
              </select>
            </div>
            <div className="flex-1 flex flex-col">
              <label className="text-sm text-gray-300 mb-1">
                {t('adminRateLimit.filter_search_label', {
                  defaultValue: 'Поиск по значению',
                })}
              </label>
              <input
                type="text"
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                className="w-full px-3 py-2 rounded-md bg-gray-900 border border-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                placeholder={t('adminRateLimit.filter_search_placeholder', {
                  defaultValue: 'Часть IP или user id',
                })}
              />
            </div>
          </div>
        </div>

        <form
          onSubmit={handleCreateBan}
          className="card p-4 space-y-4 bg-gray-800/60 border border-gray-700 rounded-xl"
        >
          <h2 className="text-xl font-semibold">
            {t('adminRateLimit.create_ban_title', {
              defaultValue: 'Добавить бан',
            })}
          </h2>
          <p className="text-sm text-gray-400">
            {t('adminRateLimit.create_ban_description', {
              defaultValue:
                'Ручной бан по IP или user id. TTL берётся из настроек автобана бэкенда.',
            })}
          </p>
          <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-end">
            <div className="flex flex-col">
              <label className="text-sm text-gray-300 mb-1">
                {t('adminRateLimit.kind_label', { defaultValue: 'Тип' })}
              </label>
              <select
                value={formKind}
                onChange={(e) => setFormKind(e.target.value as BanKind)}
                className="px-3 py-2 rounded-md bg-gray-900 border border-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
              >
                <option value="ip">
                  {t('adminRateLimit.kind_ip', { defaultValue: 'IP' })}
                </option>
                <option value="user">
                  {t('adminRateLimit.kind_user', { defaultValue: 'User ID' })}
                </option>
              </select>
            </div>
            <div className="flex-1 flex flex-col">
              <label className="text-sm text-gray-300 mb-1">
                {t('adminRateLimit.value_label', {
                  defaultValue: 'Значение (IP или user id)',
                })}
              </label>
              <input
                type="text"
                value={formValue}
                onChange={(e) => setFormValue(e.target.value)}
                className="w-full px-3 py-2 rounded-md bg-gray-900 border border-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                placeholder={t('adminRateLimit.value_placeholder', {
                  defaultValue: 'Например, 1.2.3.4 или 123',
                })}
              />
            </div>
            <button
              type="submit"
              disabled={formLoading}
              className="btn-primary whitespace-nowrap px-4 py-2 disabled:opacity-60"
            >
              {formLoading
                ? t('adminRateLimit.button_creating', {
                    defaultValue: 'Создание...',
                  })
                : t('adminRateLimit.button_create', {
                    defaultValue: 'Добавить бан',
                  })}
            </button>
          </div>
        </form>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="card p-4 bg-gray-800/60 border border-gray-700 rounded-xl">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold">
                {t('adminRateLimit.bans_title', {
                  defaultValue: 'Активные баны',
                })}
              </h2>
              {loading && (
                <span className="text-xs text-gray-400">
                  {t('adminRateLimit.loading', { defaultValue: 'Загрузка...' })}
                </span>
              )}
            </div>

            {filteredBans.length === 0 ? (
              <p className="text-sm text-gray-400">
                {t('adminRateLimit.bans_empty', {
                  defaultValue: 'Сейчас нет активных банов.',
                })}
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-400">
                      <th className="py-2 pr-4">{t('adminRateLimit.table_type', { defaultValue: 'Тип' })}</th>
                      <th className="py-2 pr-4">{t('adminRateLimit.table_value', { defaultValue: 'Значение' })}</th>
                      <th className="py-2 pr-4">{t('adminRateLimit.table_ttl', { defaultValue: 'TTL' })}</th>
                      <th className="py-2" />
                    </tr>
                  </thead>
                  <tbody>
                    {filteredBans.map((ban) => (
                      <tr key={`${ban.type}:${ban.value}`} className="border-t border-gray-700">
                        <td className="py-2 pr-4 align-top text-gray-200">
                          {ban.type}
                        </td>
                        <td className="py-2 pr-4 align-top break-all text-gray-100">
                          {ban.value}
                        </td>
                        <td className="py-2 pr-4 align-top text-gray-300">
                          {formatTtl(ban.ttl)}
                        </td>
                        <td className="py-2 align-top text-right">
                          <button
                            type="button"
                            onClick={() => handleDeleteBan(ban.type, ban.value)}
                            className="text-xs px-2 py-1 rounded-md border border-red-600 text-red-200 hover:bg-red-900/40 transition-colors"
                          >
                            {t('adminRateLimit.button_unban', {
                              defaultValue: 'Снять бан',
                            })}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="card p-4 bg-gray-800/60 border border-gray-700 rounded-xl">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold">
                {t('adminRateLimit.violations_title', {
                  defaultValue: 'Нарушения rate limit',
                })}
              </h2>
              <div className="flex items-center gap-3">
                {loading && (
                  <span className="text-xs text-gray-400">
                    {t('adminRateLimit.loading', {
                      defaultValue: 'Загрузка...',
                    })}
                  </span>
                )}
                <button
                  type="button"
                  onClick={handleCleanupViolations}
                  disabled={cleanupLoading || loading || violations.length === 0}
                  className="text-xs px-2 py-1 rounded-md border border-yellow-500 text-yellow-200 hover:bg-yellow-900/40 disabled:opacity-60 transition-colors"
                >
                  {cleanupLoading
                    ? t('adminRateLimit.button_cleanup_running', {
                        defaultValue: 'Очистка...',
                      })
                    : t('adminRateLimit.button_cleanup', {
                        defaultValue: 'Очистить нарушения',
                      })}
                </button>
              </div>
            </div>

            {filteredViolations.length === 0 ? (
              <p className="text-sm text-gray-400">
                {t('adminRateLimit.violations_empty', {
                  defaultValue: 'Нарушения не зафиксированы.',
                })}
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-400">
                      <th className="py-2 pr-4">{t('adminRateLimit.table_type', { defaultValue: 'Тип' })}</th>
                      <th className="py-2 pr-4">{t('adminRateLimit.table_value', { defaultValue: 'Значение' })}</th>
                      <th className="py-2 pr-4">{t('adminRateLimit.table_count', { defaultValue: 'Счётчик' })}</th>
                      <th className="py-2 pr-4">{t('adminRateLimit.table_ttl', { defaultValue: 'TTL' })}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredViolations.map((viol) => (
                      <tr
                        key={`${viol.type}:${viol.value}`}
                        className="border-t border-gray-700"
                      >
                        <td className="py-2 pr-4 align-top text-gray-200">
                          {viol.type}
                        </td>
                        <td className="py-2 pr-4 align-top break-all text-gray-100">
                          {viol.value}
                        </td>
                        <td className="py-2 pr-4 align-top text-gray-200">
                          {viol.count}
                        </td>
                        <td className="py-2 pr-4 align-top text-gray-300">
                          {formatTtl(viol.ttl)}
                        </td>
                        <td className="py-2 align-top text-right">
                          <button
                            type="button"
                            onClick={() => handleCreateBanFromViolation(viol)}
                            disabled={formLoading}
                            className="text-xs px-2 py-1 rounded-md border border-orange-500 text-orange-200 hover:bg-orange-900/40 disabled:opacity-60 transition-colors"
                          >
                            {t('adminRateLimit.button_ban_from_violation', {
                              defaultValue: 'Забанить',
                            })}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
