'use client';

import React, { useState } from 'react';
import { useAuth } from '../../src/contexts/AuthContext';
import { useRouter } from 'next/navigation';

export default function TeammatesPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [filters, setFilters] = useState({ rank: '', region: '', role: '' });

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-8 text-white">Please login to find teammates</h1>
          <button
            onClick={() => router.push('/auth')}
            className="px-8 py-3 bg-orange-500 hover:bg-orange-600 rounded-lg font-semibold transition-colors"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-8 py-12">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-4 gradient-text">👥 Find Teammates</h1>
        <p className="text-zinc-400 mb-8">Connect with players matching your playstyle</p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <select className="px-4 py-3 glass-effect rounded-lg focus:outline-none focus:border-primary">
            <option>Select Rank</option>
            <option>1-5</option>
            <option>6-10</option>
            <option>10+</option>
          </select>
          <select className="px-4 py-3 glass-effect rounded-lg focus:outline-none focus:border-primary">
            <option>Select Region</option>
            <option>EU</option>
            <option>NA</option>
            <option>Asia</option>
          </select>
          <select className="px-4 py-3 glass-effect rounded-lg focus:outline-none focus:border-primary">
            <option>Select Role</option>
            <option>Entry Fragger</option>
            <option>Support</option>
            <option>AWPer</option>
          </select>
        </div>

        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="glass-effect rounded-xl p-6 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-gradient-to-r from-primary to-primary-dark rounded-full flex items-center justify-center text-2xl">
                  🎮
                </div>
                <div>
                  <h3 className="text-xl font-semibold">Player {i}</h3>
                  <p className="text-zinc-400">Level 10 • EU • 1.2 K/D</p>
                </div>
              </div>
              <button className="px-6 py-2 bg-gradient-to-r from-primary to-primary-dark rounded-lg font-medium">
                Add Friend
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
