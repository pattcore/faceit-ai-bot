'use client';

import React, { useState } from 'react';
import { useAuth } from '../../src/contexts/AuthContext';
import { useRouter } from 'next/navigation';

export default function DemoPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center px-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">Please login to upload demos</h2>
          <button onClick={() => router.push('/auth')} className="btn-primary">
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    // TODO: implement upload
    setTimeout(() => setLoading(false), 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white">
      <div className="container mx-auto px-6 pt-32 pb-16">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-orange-500 to-orange-600 bg-clip-text text-transparent">📊 Demo Analysis</h1>
          <p className="text-xl text-gray-300 mb-8">Upload your CS2 demo file for detailed analysis</p>
        
        <div className="glass-effect rounded-2xl p-8">
          <div className="border-2 border-dashed border-zinc-600 rounded-xl p-12 text-center">
            <input
              type="file"
              accept=".dem"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="hidden"
              id="demo-upload"
            />
            <label htmlFor="demo-upload" className="cursor-pointer">
              <div className="text-6xl mb-4">📁</div>
              <p className="text-xl mb-2">{file ? file.name : 'Click to upload demo'}</p>
              <p className="text-sm text-zinc-500">Supported: .dem files</p>
            </label>
          </div>
          
          {file && (
            <button
              onClick={handleUpload}
              disabled={loading}
              className="w-full mt-6 btn-primary disabled:opacity-50"
            >
              {loading ? 'Analyzing...' : 'Analyze Demo'}
            </button>
          )}
        </div>
        </div>
      </div>
    </div>
  );
}
