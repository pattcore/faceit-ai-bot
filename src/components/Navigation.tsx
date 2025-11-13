'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useAuth } from '../contexts/AuthContext';

const Navigation = () => {
  const { user, logout } = useAuth();

  return (
    <nav className="fixed top-0 left-0 right-0 bg-gray-900/95 backdrop-blur-lg border-b border-gray-800 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 text-xl font-bold text-white hover:opacity-80 transition-opacity">
          <Image src="/icon.svg" width={28} height={28} alt="Faceit AI Bot" />
          <span>Faceit AI Bot</span>
        </Link>

        <div className="hidden md:flex gap-8 flex-1 justify-center">
          <Link href="/" className="text-gray-300 font-medium hover:text-white transition-colors">
            Home
          </Link>
          <Link href="/demo" className="text-gray-300 font-medium hover:text-white transition-colors">
            Demo Analysis
          </Link>
          <Link href="/teammates" className="text-gray-300 font-medium hover:text-white transition-colors">
            Teammates
          </Link>
          {user && (
            <Link href="/dashboard" className="text-gray-300 font-medium hover:text-white transition-colors">
              Dashboard
            </Link>
          )}
        </div>

        <div className="flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-4">
              <span className="text-gray-300 text-sm">{user.username || user.email}</span>
              <button 
                onClick={logout} 
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-lg text-white font-medium transition-colors"
              >
                Logout
              </button>
            </div>
          ) : (
            <Link 
              href="/auth" 
              className="px-6 py-2 bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg text-white font-semibold transition-colors"
            >
              Login
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;