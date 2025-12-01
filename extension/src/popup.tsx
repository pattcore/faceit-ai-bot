import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';

const SITE_BASE = 'https://pattmsc.online';
const API_BASE = SITE_BASE + '/api';
const TOKEN_KEY = 'faceit_ai_bot_access_token';

interface LoginResponse {
  access_token: string;
  token_type: string;
}

interface UserInfo {
  id: number;
  email?: string;
  username?: string;
}

interface PlayerStats {
  kd_ratio: number;
  win_rate: number;
  headshot_percentage: number;
  average_kills: number;
  matches_played: number;
  elo?: number | null;
  level?: number | null;
}

interface TrainingExercise {
  name: string;
  duration: string;
  description?: string;
}

interface TrainingPlan {
  focus_areas: string[];
  daily_exercises: TrainingExercise[];
  estimated_time: string;
}

interface PlayerAnalysis {
  nickname: string;
  overall_rating: number;
  stats: PlayerStats;
  training_plan: TrainingPlan;
}

type Lang = 'ru' | 'en';

const POPUP_LANG_STORAGE_KEY = 'faceit_ai_bot_popup_lang';

interface PopupTranslations {
  themeLight: string;
  themeDark: string;
  langButton: string;
  subtitle: string;
  checkingSession: string;
  signedInAs: string;
  quickTitle: string;
  quickDescription: string;
  nicknamePlaceholder: string;
  analyzeButtonIdle: string;
  analyzeButtonLoading: string;
  ratingLabel: string;
  matchesPlayedLabel: string;
  trainingPlanLabel: string;
  openFullAnalysis: string;
  demoAnalysis: string;
  teammates: string;
  logoutInExtension: string;
  loginPrompt: string;
  emailPlaceholder: string;
  passwordPlaceholder: string;
  loginButtonIdle: string;
  loginButtonLoading: string;
  steamLoginButton: string;
  demoExampleButton: string;
  footerHint: string;
  loginFailed: string;
  noToken: string;
  networkError: string;
  defaultPlayerName: string;
}

const POPUP_TRANSLATIONS: Record<Lang, PopupTranslations> = {
  ru: {
    themeLight: 'Тема: светлая',
    themeDark: 'Тема: тёмная',
    langButton: 'Язык: RU',
    subtitle: 'AI-помощник для разбора демок и поиска тиммейтов в CS2',
    checkingSession: 'Проверяем сессию расширения...',
    signedInAs: 'Выполнен вход как',
    quickTitle: 'Быстрый AI-анализ',
    quickDescription:
      'Введите ник на Faceit (или свой) и получите быстрый анализ прямо в расширении.',
    nicknamePlaceholder: 'Ник на Faceit',
    analyzeButtonIdle: 'Запустить AI-анализ',
    analyzeButtonLoading: 'Анализируем...',
    ratingLabel: 'Рейтинг',
    matchesPlayedLabel: 'Матчей сыграно',
    trainingPlanLabel: 'План тренировки',
    openFullAnalysis: 'Открыть полную страницу анализа',
    demoAnalysis: 'Демо-анализ',
    teammates: 'Поиск тиммейтов',
    logoutInExtension: 'Выйти в расширении',
    loginPrompt: 'Войдите в аккаунт Faceit AI Bot, чтобы использовать расширение.',
    emailPlaceholder: 'Почта',
    passwordPlaceholder: 'Пароль',
    loginButtonIdle: 'Войти',
    loginButtonLoading: 'Входим...',
    steamLoginButton: 'Войти через Steam',
    demoExampleButton: 'Пример демо-анализа',
    footerHint:
      'Расширение использует API-токен, сохранённый в расширении (а не cookie браузера).',
    loginFailed: 'Не удалось войти. Проверьте почту и пароль.',
    noToken: 'Сервер не вернул токен доступа.',
    networkError: 'Ошибка сети. Попробуйте ещё раз.',
    defaultPlayerName: 'Игрок',
  },
  en: {
    themeLight: 'Theme: light',
    themeDark: 'Theme: dark',
    langButton: 'Language: EN',
    subtitle: 'AI assistant for demo review and teammate search in CS2',
    checkingSession: 'Checking extension session...',
    signedInAs: 'Signed in as',
    quickTitle: 'Quick AI analysis',
    quickDescription:
      'Enter a Faceit nickname (yours or any) to get a quick analysis right in the extension.',
    nicknamePlaceholder: 'Faceit nickname',
    analyzeButtonIdle: 'Run AI analysis',
    analyzeButtonLoading: 'Analyzing...',
    ratingLabel: 'Rating',
    matchesPlayedLabel: 'Matches played',
    trainingPlanLabel: 'Training plan',
    openFullAnalysis: 'Open full analysis page',
    demoAnalysis: 'Demo analysis',
    teammates: 'Teammate search',
    logoutInExtension: 'Sign out in extension',
    loginPrompt: 'Sign in to your Faceit AI Bot account to use the extension.',
    emailPlaceholder: 'Email',
    passwordPlaceholder: 'Password',
    loginButtonIdle: 'Sign in',
    loginButtonLoading: 'Signing in...',
    steamLoginButton: 'Sign in with Steam',
    demoExampleButton: 'Demo analysis example',
    footerHint:
      'The extension uses an API token stored inside the extension (not browser cookies).',
    loginFailed: 'Login failed. Check your email and password.',
    noToken: 'API did not return an access token.',
    networkError: 'Network error. Please try again.',
    defaultPlayerName: 'Player',
  },
};

function openInNewTab(path: string) {
  const url = SITE_BASE + path;
  if ((window as any).chrome?.tabs?.create) {
    (window as any).chrome.tabs.create({ url });
  } else {
    window.open(url, '_blank');
  }
}

function getInitialNicknameFromLocation(): string {
  try {
    const url = new URL(window.location.href);
    const param = url.searchParams.get('nickname');
    return param ? param : '';
  } catch {
    return '';
  }
}

const Popup: React.FC = () => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState<boolean>(false);
  const [nickname, setNickname] = useState(() => getInitialNicknameFromLocation());
  const [analysis, setAnalysis] = useState<PlayerAnalysis | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    try {
      const stored = window.localStorage.getItem('faceit_ai_bot_popup_theme');
      return stored === 'light' ? 'light' : 'dark';
    } catch {
      return 'dark';
    }
  });
  const [lang, setLang] = useState<Lang>(() => {
    try {
      const stored = window.localStorage.getItem(POPUP_LANG_STORAGE_KEY);
      return stored === 'en' ? 'en' : 'ru';
    } catch {
      return 'ru';
    }
  });

  useEffect(() => {
    const controller = new AbortController();

    const loadSession = async () => {
      // 1) Try to use website cookie-based session first
      try {
        const cookieRes = await fetch(API_BASE + '/auth/me', {
          credentials: 'include',
          signal: controller.signal,
        });

        if (cookieRes.ok) {
          const data = await cookieRes.json();
          setUser(data);
          setLoading(false);
          return;
        }
      } catch {
        // ignore and fall back to extension token
      }

      // 2) If cookies don't work, try the extension token
      const storedToken = window.localStorage.getItem(TOKEN_KEY);
      if (!storedToken) {
        setLoading(false);
        return;
      }

      setToken(storedToken);

      try {
        const res = await fetch(API_BASE + '/auth/me', {
          headers: {
            Authorization: `Bearer ${storedToken}`,
          },
          credentials: 'include',
          signal: controller.signal,
        });

        if (!res.ok) {
          setUser(null);
        } else {
          const data = await res.json();
          setUser(data);
        }
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    loadSession();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (user?.username && !nickname) {
      setNickname(user.username);
    }
  }, [user, nickname]);

  useEffect(() => {
    try {
      window.localStorage.setItem('faceit_ai_bot_popup_theme', theme);
    } catch {
      // ignore
    }
  }, [theme]);

  useEffect(() => {
    try {
      window.localStorage.setItem(POPUP_LANG_STORAGE_KEY, lang);
    } catch {
      // ignore
    }
  }, [lang]);

  const tr = POPUP_TRANSLATIONS[lang];

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    setAuthLoading(true);
    setAuthError(null);

    try {
      const res = await fetch(API_BASE + '/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          email,
          password,
        }),
      });

      if (!res.ok) {
        setAuthError(tr.loginFailed);
        return;
      }

      const data = (await res.json()) as LoginResponse;
      if (!data.access_token) {
        setAuthError(tr.noToken);
        return;
      }

      window.localStorage.setItem(TOKEN_KEY, data.access_token);
      setToken(data.access_token);

      const meRes = await fetch(API_BASE + '/auth/me', {
        headers: {
          Authorization: `Bearer ${data.access_token}`,
        },
        credentials: 'include',
      });

      if (meRes.ok) {
        const meData = await meRes.json();
        setUser(meData);
      } else {
        setUser(null);
      }
    } catch {
      setAuthError(tr.networkError);
    } finally {
      setAuthLoading(false);
      setLoading(false);
    }
  };

  const handleLogout = () => {
    window.localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  };

  const handleAnalyzePlayer = async () => {
    const trimmed = nickname.trim();
    if (!trimmed) {
      return;
    }

    setAnalysisLoading(true);
    setAnalysisError(null);
    setAnalysis(null);

    try {
      const res = await fetch(
        `${API_BASE}/players/${encodeURIComponent(trimmed)}/analysis?language=${lang}`,
        {
          headers: token
            ? {
                Authorization: `Bearer ${token}`,
              }
            : undefined,
          credentials: 'include',
        }
      );

      if (!res.ok) {
        let message = 'Не удалось выполнить анализ игрока.';
        try {
          const errorBody = await res.json();
          const detail =
            typeof errorBody === 'string'
              ? errorBody
              : errorBody?.detail || errorBody?.error || '';

          if (res.status === 404) {
            message =
              typeof detail === 'string' && detail.includes('not found')
                ? 'Игрок не найден на Faceit.'
                : 'Игрок не найден.';
          } else if (res.status === 429) {
            message = 'Превышен лимит запросов к Faceit. Попробуйте позже.';
          } else if (res.status >= 500 && res.status < 600) {
            message =
              typeof detail === 'string' && detail
                ? `Сервис анализа временно недоступен: ${detail}`
                : 'Сервис анализа временно недоступен.';
          } else if (detail) {
            message = typeof detail === 'string' ? detail : message;
          }

          // Для отладки можно посмотреть точный ответ сервера
          // eslint-disable-next-line no-console
          console.error('AI analysis failed', res.status, errorBody);
        } catch {
          // eslint-disable-next-line no-console
          console.error('AI analysis failed', res.status);
        }

        setAnalysisError(message);
        return;
      }

      const data = (await res.json()) as PlayerAnalysis;
      setAnalysis(data);
    } catch {
      setAnalysisError('Ошибка сети. Попробуйте ещё раз.');
    } finally {
      setAnalysisLoading(false);
    }
  };

  const name = user?.username || user?.email || tr.defaultPlayerName;

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const toggleLanguage = () => {
    setLang((prev) => (prev === 'ru' ? 'en' : 'ru'));
  };

  return (
    <div
      className={`popup-root ${
        theme === 'light' ? 'popup-root-light' : 'popup-root-dark'
      }`}
    >
      <header className="popup-header">
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <div className="popup-title">Faceit AI Bot</div>
          <div
            style={{
              display: 'flex',
              gap: 4,
            }}
          >
            <button
              type="button"
              onClick={toggleTheme}
              style={{
                fontSize: 10,
                padding: '2px 6px',
                borderRadius: 9999,
                border: '1px solid #374151',
                backgroundColor: theme === 'light' ? '#e5e7eb' : '#020617',
                color: theme === 'light' ? '#111827' : '#e5e7eb',
                cursor: 'pointer',
              }}
            >
              {theme === 'light' ? tr.themeLight : tr.themeDark}
            </button>
            <button
              type="button"
              onClick={toggleLanguage}
              style={{
                fontSize: 10,
                padding: '2px 6px',
                borderRadius: 9999,
                border: '1px solid #374151',
                backgroundColor: theme === 'light' ? '#e5e7eb' : '#020617',
                color: theme === 'light' ? '#111827' : '#e5e7eb',
                cursor: 'pointer',
              }}
            >
              {tr.langButton}
            </button>
          </div>
        </div>
        <div className="popup-subtitle">
          {tr.subtitle}
        </div>
      </header>

      <main className="popup-main">
        {loading ? (
          <div style={{ fontSize: 12, color: '#9ca3af' }}>
            {tr.checkingSession}
          </div>
        ) : user ? (
          <>
            <div style={{ fontSize: 12, color: '#9ca3af' }}>
              {tr.signedInAs} {name}
            </div>

            <div
              style={{
                borderRadius: 10,
                border: '1px solid #1f2937',
                padding: 8,
                marginTop: 4,
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
                backgroundColor: '#020617',
              }}
            >
              <div style={{ fontSize: 12, fontWeight: 600 }}>{tr.quickTitle}</div>
              <div style={{ fontSize: 11, color: '#9ca3af' }}>
                {tr.quickDescription}
              </div>
              <input
                type="text"
                placeholder={tr.nicknamePlaceholder}
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                style={{
                  padding: '6px 8px',
                  borderRadius: 6,
                  border: '1px solid #374151',
                  backgroundColor: '#020617',
                  color: '#f9fafb',
                  fontSize: 12,
                }}
              />
              {analysisError && (
                <div style={{ fontSize: 11, color: '#f87171' }}>{analysisError}</div>
              )}
              <button
                className="btn-primary"
                onClick={handleAnalyzePlayer}
                disabled={analysisLoading || !nickname.trim()}
              >
                {analysisLoading ? tr.analyzeButtonLoading : tr.analyzeButtonIdle}
              </button>

              {analysis && (
                <div
                  style={{
                    marginTop: 4,
                    borderTop: '1px solid #1f2937',
                    paddingTop: 6,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 4,
                  }}
                >
                  <div style={{ fontSize: 11, color: '#9ca3af' }}>
                    {tr.ratingLabel}: <strong>{analysis.overall_rating}/10</strong>
                  </div>
                  <div style={{ fontSize: 11, color: '#9ca3af' }}>
                    K/D: <strong>{analysis.stats.kd_ratio.toFixed(2)}</strong>, Win
                    rate: <strong>{analysis.stats.win_rate.toFixed(1)}%</strong>, HS:{' '}
                    <strong>{analysis.stats.headshot_percentage.toFixed(1)}%</strong>
                  </div>
                  <div style={{ fontSize: 11, color: '#9ca3af' }}>
                    {tr.matchesPlayedLabel}: <strong>{analysis.stats.matches_played}</strong>
                  </div>
                  <div style={{ fontSize: 11, color: '#9ca3af' }}>
                    {tr.trainingPlanLabel}:{' '}
                    <strong>{analysis.training_plan.estimated_time}</strong>
                  </div>
                  {analysis.training_plan.daily_exercises?.length > 0 && (
                    <ul
                      style={{
                        margin: 0,
                        paddingLeft: 16,
                        fontSize: 11,
                        color: '#9ca3af',
                      }}
                    >
                      {analysis.training_plan.daily_exercises.slice(0, 3).map((ex, i) => (
                        <li key={i}>
                          <strong>{ex.name}</strong> — {ex.duration}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>

            <button
              className="btn-secondary"
              onClick={() => openInNewTab('/analysis?auto=1')}
            >
              {tr.openFullAnalysis}
            </button>
            <button
              className="btn-secondary"
              onClick={() => openInNewTab('/demo')}
            >
              {tr.demoAnalysis}
            </button>
            <button
              className="btn-secondary"
              onClick={() => openInNewTab('/teammates')}
            >
              {tr.teammates}
            </button>
            <button
              className="btn-secondary"
              onClick={handleLogout}
            >
              {tr.logoutInExtension}
            </button>
          </>
        ) : (
          <>
            <div style={{ fontSize: 12, color: '#9ca3af' }}>
              {tr.loginPrompt}
            </div>
            <form
              onSubmit={handleLogin}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
                marginTop: 6,
              }}
            >
              <input
                type="email"
                placeholder={tr.emailPlaceholder}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{
                  padding: '6px 8px',
                  borderRadius: 6,
                  border: '1px solid #374151',
                  backgroundColor: '#020617',
                  color: '#f9fafb',
                  fontSize: 12,
                }}
              />
              <input
                type="password"
                placeholder={tr.passwordPlaceholder}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{
                  padding: '6px 8px',
                  borderRadius: 6,
                  border: '1px solid #374151',
                  backgroundColor: '#020617',
                  color: '#f9fafb',
                  fontSize: 12,
                }}
              />
              {authError && (
                <div style={{ fontSize: 11, color: '#f87171' }}>{authError}</div>
              )}
              <button
                type="submit"
                className="btn-primary"
                disabled={authLoading}
              >
                {authLoading ? tr.loginButtonLoading : tr.loginButtonIdle}
              </button>
            </form>
            <div
              style={{
                marginTop: 8,
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
              }}
            >
              <button
                type="button"
                className="btn-secondary"
                onClick={() => openInNewTab('/auth')}
              >
                {tr.steamLoginButton}
              </button>
            </div>
            <button
              className="btn-secondary"
              onClick={() => openInNewTab('/demo/example')}
            >
              {tr.demoExampleButton}
            </button>
          </>
        )}
      </main>

      <footer className="popup-footer">
        <span className="popup-hint">
          {tr.footerHint}
        </span>
      </footer>
    </div>
  );
}

const container = document.getElementById('root');
if (container) {
  const root = createRoot(container);
  root.render(<Popup />);
}
