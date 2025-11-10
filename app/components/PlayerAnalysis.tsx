'use client';

import { useState } from 'react';

interface PlayerStats {
  kd_ratio: number;
  win_rate: number;
  headshot_percentage: number;
  average_kills: number;
  matches_played: number;
  elo?: number;
  level?: number;
}

interface PlayerStrengths {
  aim: number;
  game_sense: number;
  positioning: number;
  teamwork: number;
  consistency: number;
}

interface PlayerWeaknesses {
  areas: string[];
  priority: string;
  recommendations: string[];
}

interface TrainingPlan {
  focus_areas: string[];
  daily_exercises: Array<{
    name: string;
    duration: string;
    description: string;
  }>;
  estimated_time: string;
}

interface PlayerAnalysisData {
  player_id: string;
  nickname: string;
  stats: PlayerStats;
  strengths: PlayerStrengths;
  weaknesses: PlayerWeaknesses;
  training_plan: TrainingPlan;
  overall_rating: number;
  analyzed_at: string;
}

export default function PlayerAnalysis() {
  const [nickname, setNickname] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysis, setAnalysis] = useState<PlayerAnalysisData | null>(null);

  const analyzePlayer = async () => {
    if (!nickname.trim()) {
      setError('Enter player nickname');
      return;
    }

    setLoading(true);
    setError('');
    setAnalysis(null);

    try {
      const response = await fetch(`/api/players?nickname=${encodeURIComponent(nickname)}&action=analysis`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Player analysis error');
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      analyzePlayer();
    }
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 8) return 'text-green-500';
    if (rating >= 6) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getSkillColor = (skill: number) => {
    if (skill >= 8) return 'bg-green-500';
    if (skill >= 6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Search Section */}
      <div className="bg-gradient-to-r from-orange-500 to-red-600 rounded-lg p-8 mb-8 shadow-xl">
        <h1 className="text-4xl font-bold text-white mb-4">
          🎮 Анализ игрока CS2
        </h1>
        <p className="text-white/90 mb-6">
          Получи детальный анализ статистики и персональные рекомендации
        </p>
        
        <div className="flex gap-4">
          <input
            type="text"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Введи никнейм Faceit..."
            className="flex-1 px-6 py-4 rounded-lg text-lg focus:outline-none focus:ring-2 focus:ring-white"
            disabled={loading}
          />
          <button
            onClick={analyzePlayer}
            disabled={loading}
            className="px-8 py-4 bg-white text-orange-600 rounded-lg font-bold text-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? '⏳ Анализ...' : '🔍 Анализировать'}
          </button>
        </div>

        {error && (
          <div className="mt-4 bg-red-500/20 border border-red-500 text-white px-4 py-3 rounded-lg">
            ⚠️ {error}
          </div>
        )}
      </div>

      {/* Analysis Results */}
      {analysis && (
        <div className="space-y-6">
          {/* Overall Rating */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-800">
                  {analysis.nickname}
                </h2>
                <p className="text-gray-600">
                  Уровень {analysis.stats.level} • ELO {analysis.stats.elo}
                </p>
              </div>
              <div className="text-center">
                <div className={`text-6xl font-bold ${getRatingColor(analysis.overall_rating)}`}>
                  {analysis.overall_rating}/10
                </div>
                <p className="text-gray-600 mt-2">Общая оценка</p>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">📊 Статистика</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-3xl font-bold text-orange-600">
                  {analysis.stats.kd_ratio.toFixed(2)}
                </div>
                <div className="text-gray-600 mt-1">K/D Ratio</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-3xl font-bold text-orange-600">
                  {analysis.stats.win_rate.toFixed(1)}%
                </div>
                <div className="text-gray-600 mt-1">Win Rate</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-3xl font-bold text-orange-600">
                  {analysis.stats.headshot_percentage.toFixed(1)}%
                </div>
                <div className="text-gray-600 mt-1">Headshots</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-3xl font-bold text-orange-600">
                  {analysis.stats.matches_played}
                </div>
                <div className="text-gray-600 mt-1">Матчей</div>
              </div>
            </div>
          </div>

          {/* Strengths */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">💪 Сильные стороны</h3>
            <div className="space-y-3">
              {Object.entries(analysis.strengths).map(([key, value]) => (
                <div key={key}>
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-700 capitalize">
                      {key === 'aim' ? '🎯 Прицеливание' :
                       key === 'game_sense' ? '🧠 Игровое чутье' :
                       key === 'positioning' ? '📍 Позиционирование' :
                       key === 'teamwork' ? '👥 Командная игра' :
                       '⚡ Стабильность'}
                    </span>
                    <span className="font-bold">{value}/10</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${getSkillColor(value)}`}
                      style={{ width: `${value * 10}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Weaknesses */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">🎯 Области для улучшения</h3>
            <div className="mb-4">
              <span className="inline-block bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm font-semibold">
                Приоритет: {analysis.weaknesses.priority}
              </span>
            </div>
            <div className="space-y-2">
              {analysis.weaknesses.recommendations.map((rec, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <span className="text-orange-500 mt-1">💡</span>
                  <p className="text-gray-700">{rec}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Training Plan */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">📅 План тренировок</h3>
            <div className="mb-4">
              <p className="text-gray-600">
                ⏱️ Примерное время улучшения: <span className="font-semibold">{analysis.training_plan.estimated_time}</span>
              </p>
            </div>
            <div className="space-y-4">
              {analysis.training_plan.daily_exercises.map((exercise, idx) => (
                <div key={idx} className="border-l-4 border-orange-500 pl-4 py-2">
                  <h4 className="font-bold text-gray-800">{exercise.name}</h4>
                  <p className="text-sm text-gray-600">⏰ {exercise.duration}</p>
                  <p className="text-gray-700 mt-1">{exercise.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
