'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '../src/contexts/AuthContext';

export default function HomePage() {
  const { user } = useAuth();
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white">
      <div className="container mx-auto px-6 pt-32 pb-16">
        <div className="text-center mb-16">
          <h1 className="text-7xl font-bold mb-6 hero-gradient animate-glow">
            Faceit AI Bot
          </h1>
          <p className="text-2xl text-gray-300 mb-8 max-w-3xl mx-auto leading-relaxed">
            Professional CS2 analytics platform with advanced statistics and intelligent teammate matching
          </p>
          
          <div className="flex gap-6 justify-center flex-wrap">
            {user ? (
              <Link 
                href="/dashboard" 
                className="btn-primary text-lg px-10 py-4"
              >
                Dashboard
              </Link>
            ) : (
              <>
                <Link 
                  href="/auth" 
                  className="btn-primary text-lg px-10 py-4"
                >
                  Get Started
                </Link>
                <Link 
                  href="/demo" 
                  className="btn-secondary text-lg px-10 py-4"
                >
                  Try Demo
                </Link>
              </>
            )}
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <div className="card text-center group">
            <div className="w-16 h-16 mx-auto mb-6 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center text-2xl text-white">
              📊
            </div>
            <h3 className="text-2xl font-bold mb-4 text-white">Demo Analysis</h3>
            <p className="text-gray-300 text-lg">Upload and analyze CS2 demos with advanced statistics</p>
          </div>
          
          <div className="card text-center group">
            <div className="w-16 h-16 mx-auto mb-6 bg-gradient-to-r from-green-500 to-green-600 rounded-xl flex items-center justify-center text-2xl text-white">
              🎯
            </div>
            <h3 className="text-2xl font-bold mb-4 text-white">Player Statistics</h3>
            <p className="text-gray-300 text-lg">Track detailed performance metrics and improvements</p>
          </div>
          
          <div className="card text-center group">
            <div className="w-16 h-16 mx-auto mb-6 bg-gradient-to-r from-purple-500 to-purple-600 rounded-xl flex items-center justify-center text-2xl text-white">
              👥
            </div>
            <h3 className="text-2xl font-bold mb-4 text-white">Find Teammates</h3>
            <p className="text-gray-300 text-lg">Connect with compatible players for better matches</p>
          </div>
        </div>
      </div>
    </div>
  );
}
