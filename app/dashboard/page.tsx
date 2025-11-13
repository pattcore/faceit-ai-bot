'use client';

import React from 'react';
import { useAuth } from '../../src/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();

  if (!user) {
    router.push('/auth');
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white">
      <div className="container mx-auto px-6 pt-32 pb-16">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-orange-500 to-orange-600 bg-clip-text text-transparent">
              🎮 Dashboard
            </h1>
            <p className="text-xl text-gray-300">Welcome back, {user.username || user.email}!</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Link href="/demo" className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-8 text-center hover:bg-gray-800/70 transition-colors">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-xl font-semibold mb-3 text-white">Demo Analysis</h3>
              <p className="text-gray-400">Upload and analyze CS2 demos</p>
            </Link>
            
            <Link href="/teammates" className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-8 text-center hover:bg-gray-800/70 transition-colors">
              <div className="text-4xl mb-4">👥</div>
              <h3 className="text-xl font-semibold mb-3 text-white">Find Teammates</h3>
              <p className="text-gray-400">Connect with players</p>
            </Link>
            
            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-8 text-center">
              <div className="text-4xl mb-4">🎯</div>
              <h3 className="text-xl font-semibold mb-3 text-white">Player Stats</h3>
              <p className="text-gray-400">Track your performance</p>
            </div>
          </div>
        </div>

        {/* Subscription Card */}
        <div className="dashboard-card">
          <div className="card-header">
            <h2>💎 Subscription</h2>
          </div>
          <div className="card-content">
            <div className="subscription-status">
              <div className="status-badge">Free Plan</div>
              <p className="status-text">Upgrade to unlock all features</p>
              <button className="upgrade-btn">Upgrade to Pro</button>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="dashboard-card full-width">
          <div className="card-header">
            <h2>⚡ Quick Actions</h2>
          </div>
          <div className="card-content">
            <div className="actions-grid">
              <button className="action-btn" onClick={() => router.push('/')}>
                <span className="action-icon">📊</span>
                <span>Analyze Demo</span>
              </button>
              <button className="action-btn">
                <span className="action-icon">🎯</span>
                <span>Player Analysis</span>
              </button>
              <button className="action-btn">
                <span className="action-icon">👥</span>
                <span>Find Teammates</span>
              </button>
              <button className="action-btn">
                <span className="action-icon">📈</span>
                <span>View Stats</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .dashboard-container {
          min-height: 100vh;
          background: linear-gradient(135deg, #0c0c0c 0%, #1a1a1a 100%);
          padding: 2rem;
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 2rem;
          max-width: 1200px;
          margin-left: auto;
          margin-right: auto;
        }

        .dashboard-header h1 {
          font-size: 2.5rem;
          font-weight: 700;
          background: linear-gradient(45deg, #ff5200, #ffaa00);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .logout-btn {
          padding: 0.75rem 1.5rem;
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 8px;
          color: #fff;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }

        .logout-btn:hover {
          background: rgba(255, 255, 255, 0.15);
        }

        .dashboard-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
          gap: 1.5rem;
          max-width: 1200px;
          margin: 0 auto;
        }

        .dashboard-card {
          background: rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(10px);
          border-radius: 16px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          overflow: hidden;
        }

        .dashboard-card.full-width {
          grid-column: 1 / -1;
        }

        .card-header {
          padding: 1.5rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .card-header h2 {
          font-size: 1.25rem;
          font-weight: 600;
          color: #fff;
          margin: 0;
        }

        .card-content {
          padding: 1.5rem;
        }

        .profile-info {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .info-row {
          display: flex;
          justify-content: space-between;
          padding-bottom: 1rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .info-row:last-child {
          border-bottom: none;
          padding-bottom: 0;
        }

        .label {
          color: #a1a1aa;
          font-size: 0.9rem;
        }

        .value {
          color: #fff;
          font-weight: 500;
        }

        .subscription-status {
          text-align: center;
          padding: 1rem 0;
        }

        .status-badge {
          display: inline-block;
          padding: 0.5rem 1.5rem;
          background: rgba(59, 130, 246, 0.1);
          border: 1px solid rgba(59, 130, 246, 0.3);
          border-radius: 20px;
          color: #60a5fa;
          font-weight: 600;
          margin-bottom: 1rem;
        }

        .status-text {
          color: #a1a1aa;
          margin-bottom: 1.5rem;
        }

        .upgrade-btn {
          padding: 0.875rem 2rem;
          background: linear-gradient(135deg, #ff5200 0%, #ffaa00 100%);
          border: none;
          border-radius: 8px;
          color: #fff;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s;
        }

        .upgrade-btn:hover {
          transform: translateY(-2px);
        }

        .actions-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 1rem;
        }

        .action-btn {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.75rem;
          padding: 1.5rem 1rem;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          color: #fff;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }

        .action-btn:hover {
          background: rgba(255, 255, 255, 0.1);
          transform: translateY(-2px);
        }

        .action-icon {
          font-size: 2rem;
        }

        .loading {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #0c0c0c;
          color: #fff;
          font-size: 1.5rem;
        }
      `}</style>
    </div>
  );
}
