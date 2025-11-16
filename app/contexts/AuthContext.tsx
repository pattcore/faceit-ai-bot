'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { API_ENDPOINTS } from '../../src/config/api';

interface User {
  id: string;
  username?: string;
  email?: string;
  faceit_id?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
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
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
      setToken(savedToken);
      fetchUser(savedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async (authToken: string) => {
    try {
      const response = await fetch(API_ENDPOINTS.AUTH_ME, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        localStorage.removeItem('token');
        setToken(null);
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(API_ENDPOINTS.AUTH_LOGIN, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const raw = await response.text();
      try {
        const data = JSON.parse(raw);
        const message = (data && (data.detail || data.message)) || raw;
        throw new Error(message || 'Login failed');
      } catch {
        throw new Error(raw || 'Login failed');
      }
    }

    const data = await response.json();
    setToken(data.access_token);
    localStorage.setItem('token', data.access_token);
    await fetchUser(data.access_token);
  };

  const register = async (email: string, username: string, password: string) => {
    const formData = new FormData();
    formData.append('email', email);
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(API_ENDPOINTS.AUTH_REGISTER, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const raw = await response.text();
      try {
        const data = JSON.parse(raw);
        const message = (data && (data.detail || data.message)) || raw;
        throw new Error(message || 'Registration failed');
      } catch {
        throw new Error(raw || 'Registration failed');
      }
    }

    // Auto-login after registration
    await login(email, password);
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
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
