"use client";

import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import API_ENDPOINTS from '../../src/config/api';

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
  const { t } = useTranslation();
  const { user } = useAuth();
  const [nickname, setNickname] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysis, setAnalysis] = useState<PlayerAnalysisData | null>(null);
  const [autoTriggered, setAutoTriggered] = useState(false);

  useEffect(() => {
    if (!nickname && user) {
      setNickname(user.username || user.email || '');
    }
  }, [user, nickname]);

  useEffect(() => {
    if (!user || autoTriggered) return;
    if (typeof window === 'undefined') return;

    const params = new URLSearchParams(window.location.search);
    const auto = params.get('auto');

    if (auto === '1') {
      analyzePlayer(
        (user as any).faceit_id || user.username || user.email || ''
      );
      setAutoTriggered(true);
    }
  }, [user, autoTriggered]);

  const analyzePlayer = async (customNickname?: string) => {
    const targetNickname = (customNickname || nickname).trim();

    if (!targetNickname) {
      setError(t('player_analysis.error_enter_nickname'));
      return;
    }

    setLoading(true);
    setError('');
    setAnalysis(null);

    try {
      const response = await fetch(
        API_ENDPOINTS.PLAYER_ANALYSIS(targetNickname)
      );

      if (!response.ok) {
        let message = t('player_analysis.error_analysis');

        try {
          const contentType = response.headers.get('content-type') || '';
          if (contentType.includes('application/json')) {
            const errorData = await response.json();
            message =
              (errorData as any)?.detail ||
              (errorData as any)?.message ||
              message;
          } else {
            const text = await response.text();
            if (text) {
              message = text.slice(0, 200);
            }
          }
        } catch (parseError) {
          // Fallback to default message if parsing fails
          console.error('Failed to parse error response for player analysis', parseError);
        }

        throw new Error(message);
      }

      const data: PlayerAnalysisData = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : t('player_analysis.error_occurred')
      );
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
          🎮 {t('player_analysis.title')}
        </h1>
        <p className="text-white/90 mb-6">
          {t('player_analysis.subtitle')}
        </p>
        
        <div className="flex gap-4 flex-wrap">
          <input
            type="text"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={t('player_analysis.placeholder')}
            className="flex-1 px-6 py-4 rounded-lg text-lg focus:outline-none focus:ring-2 focus:ring-white"
            disabled={loading}
          />
          <button
            onClick={() => analyzePlayer()}
            disabled={loading}
            className="px-8 py-4 bg-white text-orange-600 rounded-lg font-bold text-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading
              ? `⏳ ${t('player_analysis.analyzing')}`
              : `🔍 ${t('player_analysis.analyze_button')}`}
          </button>
          {user && (
            <button
              type="button"
              onClick={() =>
                analyzePlayer(
                  (user as any).faceit_id || user.username || user.email || ''
                )
              }
              disabled={loading}
              className="px-6 py-4 bg-white/90 text-orange-700 rounded-lg font-semibold text-md hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {t('player_analysis.analyze_my_account')}
            </button>
          )}
        </div>

        {error && (
          <div className="mt-4 bg-red-500/20 border border-red-500 text-white px-4 py-3 rounded-lg">
            ⚠️ {error}
          </div>
        )}
      </div>

      {/* Skeleton while loading */}
      {loading && !analysis && (
        <div className="space-y-6 animate-pulse">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-40" />
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-32" />
              </div>
              <div className="text-center">
                <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-20 mx-auto mb-2" />
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-24 mx-auto" />
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-32 mb-4" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[1,2,3,4].map((i) => (
                <div key={i} className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg space-y-2">
                  <div className="h-6 bg-gray-200 dark:bg-gray-600 rounded w-16 mx-auto" />
                  <div className="h-3 bg-gray-200 dark:bg-gray-600 rounded w-20 mx-auto" />
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-40 mb-4" />
            <div className="space-y-3">
              {[1,2,3].map((i) => (
                <div key={i} className="space-y-2">
                  <div className="flex justify-between">
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-24" />
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-10" />
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2" />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {analysis && (
        <div className="space-y-6">
          {/* Overall Rating */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-800 dark:text-white">
                  {analysis.nickname}
                </h2>
                <p className="text-gray-600 dark:text-gray-300">
                  {t('player_analysis.level')} {analysis.stats.level} • ELO {analysis.stats.elo}
                </p>
              </div>
              <div className="text-center">
                <div className={`text-6xl font-bold ${getRatingColor(analysis.overall_rating)}`}>
                  {analysis.overall_rating}/10
                </div>
                <p className="text-gray-600 dark:text-gray-300 mt-2">{t('player_analysis.overall_rating')}</p>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-4">📊 {t('player_analysis.statistics')}</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="text-3xl font-bold text-orange-600">
                  {analysis.stats.kd_ratio.toFixed(2)}
                </div>
                <div className="text-gray-600 dark:text-gray-300 mt-1">{t('common.kd_ratio')}</div>
              </div>
              <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="text-3xl font-bold text-orange-600">
                  {analysis.stats.win_rate.toFixed(1)}%
                </div>
                <div className="text-gray-600 dark:text-gray-300 mt-1">{t('common.win_rate')}</div>
              </div>
              <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="text-3xl font-bold text-orange-600">
                  {analysis.stats.headshot_percentage.toFixed(1)}%
                </div>
                <div className="text-gray-600 dark:text-gray-300 mt-1">{t('common.headshots')}</div>
              </div>
              <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="text-3xl font-bold text-orange-600">
                  {analysis.stats.matches_played}
                </div>
                <div className="text-gray-600 dark:text-gray-300 mt-1">{t('player_analysis.matches')}</div>
              </div>
            </div>
          </div>

          {/* Strengths */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-4">💪 {t('player_analysis.strengths')}</h3>
            <div className="space-y-3">
              {Object.entries(analysis.strengths).map(([key, value]) => (
                <div key={key}>
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-700 dark:text-gray-300 capitalize">
                      {key === 'aim' ? '🎯 Aim' :
                       key === 'game_sense' ? '🧠 Game Sense' :
                       key === 'positioning' ? '📍 Positioning' :
                       key === 'teamwork' ? '👥 Teamwork' :
                       '⚡ Consistency'}
                    </span>
                    <span className="font-bold text-gray-800 dark:text-white">{value}/10</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
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
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-4">🎯 {t('player_analysis.improvement')}</h3>
            <div className="mb-4">
              <span className="inline-block bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 px-3 py-1 rounded-full text-sm font-semibold">
                {t('player_analysis.priority')}: {analysis.weaknesses.priority}
              </span>
            </div>
            <div className="space-y-2">
              {analysis.weaknesses.recommendations.map((rec, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <span className="text-orange-500 mt-1">💡</span>
                  <p className="text-gray-700 dark:text-gray-300">{rec}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Training Plan */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-4">📅 {t('player_analysis.training_plan')}</h3>
            <div className="mb-4">
              <p className="text-gray-600 dark:text-gray-300">
                ⏱️ {t('player_analysis.estimated_time')}: <span className="font-semibold text-gray-800 dark:text-white">{analysis.training_plan.estimated_time}</span>
              </p>
            </div>
            <div className="space-y-4">
              {analysis.training_plan.daily_exercises.map((exercise, idx) => (
                <div key={idx} className="border-l-4 border-orange-500 pl-4 py-2">
                  <h4 className="font-bold text-gray-800 dark:text-white">{exercise.name}</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-300">⏰ {exercise.duration}</p>
                  <p className="text-gray-700 dark:text-gray-300 mt-1">{exercise.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
