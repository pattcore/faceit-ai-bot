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

  useEffect(() => {
    const controller = new AbortController();

    const loadFromToken = async () => {
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

    loadFromToken();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (user?.username && !nickname) {
      setNickname(user.username);
    }
  }, [user, nickname]);

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
        body: JSON.stringify({
          email,
          password,
        }),
      });

      if (!res.ok) {
        setAuthError('Login failed. Check your credentials.');
        return;
      }

      const data = (await res.json()) as LoginResponse;
      if (!data.access_token) {
        setAuthError('No access token returned from API.');
        return;
      }

      window.localStorage.setItem(TOKEN_KEY, data.access_token);
      setToken(data.access_token);

      const meRes = await fetch(API_BASE + '/auth/me', {
        headers: {
          Authorization: `Bearer ${data.access_token}`,
        },
      });

      if (meRes.ok) {
        const meData = await meRes.json();
        setUser(meData);
      } else {
        setUser(null);
      }
    } catch {
      setAuthError('Network error. Please try again.');
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
        `${API_BASE}/players/${encodeURIComponent(trimmed)}/analysis?language=ru`,
        {
          headers: token
            ? {
                Authorization: `Bearer ${token}`,
              }
            : undefined,
        }
      );

      if (!res.ok) {
        setAnalysisError('Не удалось выполнить анализ игрока.');
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

  const name = user?.username || user?.email || 'Player';

  return (
    <div className="popup-root">
      <header className="popup-header">
        <div className="popup-title">Faceit AI Bot</div>
        <div className="popup-subtitle">
          AI demo coach and teammate search for CS2
        </div>
      </header>

      <main className="popup-main">
        {loading ? (
          <div style={{ fontSize: 12, color: '#9ca3af' }}>Checking extension session...</div>
        ) : user ? (
          <>
            <div style={{ fontSize: 12, color: '#9ca3af' }}>Signed in as {name}</div>

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
              <div style={{ fontSize: 12, fontWeight: 600 }}>Quick AI analysis</div>
              <div style={{ fontSize: 11, color: '#9ca3af' }}>
                Введите ник на Faceit (или свой) и получите быстрый анализ прямо в
                расширении.
              </div>
              <input
                type="text"
                placeholder="Faceit nickname"
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
                {analysisLoading ? 'Анализируем...' : 'Запустить AI-анализ'}
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
                    Рейтинг: <strong>{analysis.overall_rating}/10</strong>
                  </div>
                  <div style={{ fontSize: 11, color: '#9ca3af' }}>
                    K/D: <strong>{analysis.stats.kd_ratio.toFixed(2)}</strong>, Win
                    rate: <strong>{analysis.stats.win_rate.toFixed(1)}%</strong>, HS:{' '}
                    <strong>{analysis.stats.headshot_percentage.toFixed(1)}%</strong>
                  </div>
                  <div style={{ fontSize: 11, color: '#9ca3af' }}>
                    Матчей сыграно:{' '}
                    <strong>{analysis.stats.matches_played}</strong>
                  </div>
                  <div style={{ fontSize: 11, color: '#9ca3af' }}>
                    План тренировки: <strong>{analysis.training_plan.estimated_time}</strong>
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
              Open full analysis page
            </button>
            <button
              className="btn-secondary"
              onClick={() => openInNewTab('/demo')}
            >
              Demo analysis
            </button>
            <button
              className="btn-secondary"
              onClick={() => openInNewTab('/teammates')}
            >
              Teammates
            </button>
            <button
              className="btn-secondary"
              onClick={handleLogout}
            >
              Sign out in extension
            </button>
          </>
        ) : (
          <>
            <div style={{ fontSize: 12, color: '#9ca3af' }}>
              Log in with your Faceit AI Bot account to use the extension.
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
                placeholder="Email"
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
                placeholder="Password"
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
                {authLoading ? 'Logging in...' : 'Log in'}
              </button>
            </form>
            <button
              className="btn-secondary"
              onClick={() => openInNewTab('/auth')}
            >
              Open auth page
            </button>
            <button
              className="btn-secondary"
              onClick={() => openInNewTab('/demo/example')}
            >
              Demo analysis example
            </button>
          </>
        )}
      </main>

      <footer className="popup-footer">
        <span className="popup-hint">
          The extension uses an API token stored in the extension (not browser cookies).
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
