'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { API_ENDPOINTS } from '../../src/config/api';

interface User {
  id: string;
  username?: string;
  email?: string;
  faceit_id?: string;
  steam_id?: string;
  is_admin?: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string, captchaToken?: string | null) => Promise<void>;
  register: (email: string, username: string, password: string, captchaToken?: string | null) => Promise<void>;
   loginWithToken: (token: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for saved token on mount
    fetchUser();
  }, []);

  const fetchUser = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.AUTH_ME, {
        credentials: 'include',
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        setToken(null);
        setUser(null);
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string, captchaToken?: string | null) => {
    const response = await fetch(API_ENDPOINTS.AUTH_LOGIN, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        // backend поддерживает и email, и username; передаём email
        email,
        password,
        captcha_token: captchaToken,
      }),
    });

    if (!response.ok) {
      const raw = await response.text();
      let message = '';

      try {
        const data = raw ? JSON.parse(raw) : null;
        const detail: any = data && (data.detail ?? data);

        if (typeof detail === 'string') {
          message = detail;
        } else if (detail && typeof detail === 'object') {
          message =
            (detail.error as string) ||
            (detail.message as string) ||
            (detail.detail as string) ||
            '';
        }
      } catch {
        // ignore JSON parse errors
      }

      if (!message) {
        message = raw || 'Login failed';
      }

      throw new Error(message);
    }

    const data = await response.json();
    setToken(data.access_token || null);
    await fetchUser();
  };

  const loginWithToken = async (authToken: string) => {
    setToken(authToken);
    await fetchUser();
  };

  const register = async (email: string, username: string, password: string, captchaToken?: string | null) => {
    const response = await fetch(API_ENDPOINTS.AUTH_REGISTER, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        username,
        password,
        captcha_token: captchaToken,
      }),
    });

    if (!response.ok) {
      const raw = await response.text();
      let message = '';

      try {
        const data = raw ? JSON.parse(raw) : null;
        const detail: any = data && (data.detail ?? data);

        if (typeof detail === 'string') {
          message = detail;
        } else if (detail && typeof detail === 'object') {
          message =
            (detail.error as string) ||
            (detail.message as string) ||
            (detail.detail as string) ||
            '';
        }
      } catch {
        // ignore JSON parse errors
      }

      if (!message) {
        message = raw || 'Registration failed';
      }

      throw new Error(message);
    }

    // Auto-login after registration
    await login(email, password);
  };

  const logout = () => {
    fetch(API_ENDPOINTS.AUTH_LOGOUT, {
      method: 'POST',
      credentials: 'include',
    })
      .catch((error) => {
        console.error('Failed to logout:', error);
      })
      .finally(() => {
        setUser(null);
        setToken(null);
      });
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, loginWithToken, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
