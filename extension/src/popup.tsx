import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';

const SITE_BASE = 'https://pattmsc.online';
const API_BASE = SITE_BASE + '/api';

interface UserInfo {
  id: number;
  email?: string;
  username?: string;
}

function openInNewTab(path: string) {
  const url = SITE_BASE + path;
  if ((window as any).chrome?.tabs?.create) {
    (window as any).chrome.tabs.create({ url });
  } else {
    window.open(url, '_blank');
  }
}

const Popup: React.FC = () => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const controller = new AbortController();
    const loadMe = async () => {
      try {
        const res = await fetch(API_BASE + '/auth/me', {
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

    loadMe();
    return () => controller.abort();
  }, []);

  const name = user?.username || user?.email || 'Player';

  return (
    <div className="popup-root">
      <header className="popup-header">
        <div className="popup-title">Faceit AI Bot</div>
        <div className="popup-subtitle">
          Quick access to player analysis, demos and teammates
        </div>
      </header>

      <main className="popup-main">
        {loading ? (
          <div style={{ fontSize: 12, color: '#9ca3af' }}>Checking session...</div>
        ) : user ? (
          <>
            <div style={{ fontSize: 12, color: '#9ca3af' }}>Signed in as {name}</div>
            <button
              className="btn-primary"
              onClick={() => openInNewTab('/analysis?auto=1')}
            >
              Analyze my account
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
          </>
        ) : (
          <>
            <div style={{ fontSize: 12, color: '#9ca3af' }}>
              Not signed in. Log in to get personalized analysis.
            </div>
            <button
              className="btn-primary"
              onClick={() => openInNewTab('/auth')}
            >
              Log in / Sign up
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
          The extension uses the same httpOnly session as the site.
        </span>
      </footer>
    </div>
  );
};

const container = document.getElementById('root');
if (container) {
  const root = createRoot(container);
  root.render(<Popup />);
}
