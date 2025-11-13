'use client';

import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center">
      <div className="text-center mb-16">
        <h1 className="text-6xl font-bold mb-6 bg-gradient-to-r from-orange-500 to-yellow-500 bg-clip-text text-transparent">
          Faceit AI Bot
        </h1>
        <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
          Advanced CS2 statistics analysis and teammate search platform
        </p>
        
        <div className="flex gap-4 justify-center mb-16">
          <Link 
            href="/auth" 
            className="px-8 py-3 bg-orange-500 hover:bg-orange-600 rounded-lg font-semibold transition-colors"
          >
            Get Started
          </Link>
          <Link 
            href="/auth" 
            className="px-8 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-semibold transition-colors"
          >
            Sign In
          </Link>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto px-6">
        <div className="bg-gray-800 rounded-lg p-8 text-center hover:bg-gray-750 transition-colors">
          <div className="text-4xl mb-4 text-blue-400">📊</div>
          <h3 className="text-xl font-bold mb-3 text-white">Demo Analysis</h3>
          <p className="text-gray-400">Upload and analyze CS2 demos</p>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-8 text-center hover:bg-gray-750 transition-colors">
          <div className="text-4xl mb-4 text-red-400">🎯</div>
          <h3 className="text-xl font-bold mb-3 text-white">Player Stats</h3>
          <p className="text-gray-400">Track your performance</p>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-8 text-center hover:bg-gray-750 transition-colors">
          <div className="text-4xl mb-4 text-blue-400">👥</div>
          <h3 className="text-xl font-bold mb-3 text-white">Find Teammates</h3>
          <p className="text-gray-400">Connect with players</p>
        </div>
      </div>
    </div>
  );
}
