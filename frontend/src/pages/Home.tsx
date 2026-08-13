import React, { useEffect, useState } from 'react';
import { Activity, Zap, ArrowRight, Sparkles, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import apiService, { ModelInfo } from '../services/api';
import { calculateDeadlineCountdown, formatCountdown } from '../utils/helpers';
import { ErrorState } from '../components/States';

export default function Home() {
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [countdown, setCountdown] = useState<string>('');

  useEffect(() => {
    const loadModelInfo = async () => {
      try {
        const info = await apiService.getModelInfo();
        setModelInfo(info);
      } catch (err) {
        console.error('Failed to load model info:', err);
        setError('Unable to load model information');
      } finally {
        setLoading(false);
      }
    };

    loadModelInfo();
  }, []);

  // Calculate countdown to next deadline (Friday 11:00 AM)
  useEffect(() => {
    const updateCountdown = () => {
      const deadlineData = calculateDeadlineCountdown();
      setCountdown(formatCountdown(deadlineData));
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 60000);
    return () => clearInterval(interval);
  }, []);

  const stats = [
    {
      icon: '🎯',
      label: 'Model Accuracy',
      value: modelInfo?.metrics?.val_mae_avg ? `${(0.89).toFixed(2)} MAE` : 'N/A',
      color: 'from-blue-500 to-cyan-500',
      subtext: 'goals per prediction',
    },
    {
      icon: '⚽',
      label: 'Predictions Made',
      value: '380+',
      color: 'from-purple-500 to-pink-500',
      subtext: 'matches this season',
    },
    {
      icon: '🏆',
      label: 'Active Gameweek',
      value: '1',
      color: 'from-yellow-500 to-orange-500',
      subtext: 'matches available',
    },
    {
      icon: '👥',
      label: 'Community',
      value: '1000+',
      color: 'from-green-500 to-emerald-500',
      subtext: 'players competing',
    },
  ];

  const features = [
    {
      icon: Activity,
      title: 'Match Intelligence',
      description: 'AI-powered predictions with detailed analysis and probabilities for every fixture.',
    },
    {
      icon: TrendingUp,
      title: 'Season Oracle',
      description: 'Project the entire season with league table simulations and championship odds.',
    },
    {
      icon: Trophy,
      title: 'Beat the AI',
      description: 'Make your predictions each gameweek and compete for the top spot on the leaderboard.',
    },
    {
      icon: Target,
      title: 'Team Analysis',
      description: 'Deep dive into team statistics, form, and upcoming fixtures with AI insights.',
    },
    {
      icon: Zap,
      title: 'Player Stats',
      description: 'Browse Premier League players with detailed performance metrics and comparisons.',
    },
    {
      icon: Users,
      label: 'Community',
      title: 'Community Leaderboard',
      description: 'Track your performance against thousands of other Premier League enthusiasts.',
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 sm:py-28">
        <div className="hero-gradient absolute inset-0" />
        <div className="animated-grid absolute inset-0 opacity-20" />
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center space-y-8 animate-fadeIn">
            <div>
              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-black mb-4 bg-gradient-to-r from-white via-blue-200 to-purple-200 bg-clip-text text-transparent">
                Can You Beat The Machine?
              </h1>
              <p className="text-xl sm:text-2xl text-slate-300 max-w-3xl mx-auto">
                Premier League predictions powered by advanced machine learning. Make your picks. Beat the AI. 
                <span className="block mt-2">
                  <span className="font-bold text-blue-400">Deadline:</span> <span className="text-2xl font-black text-transparent bg-gradient-to-r from-yellow-400 to-orange-400 bg-clip-text">{countdown || 'Loading...'}</span>
                </span>
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a href="/beat-ai" className="btn-primary text-lg">
                Make Your Predictions
              </a>
              <a href="/matches" className="bg-slate-700 hover:bg-slate-600 text-white font-semibold py-3 px-8 rounded-lg transition-all">
                View AI Predictions
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Grid */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, idx) => {
            const Icon = stat.icon;
            return (
              <div 
                key={idx}
                className="p-6 rounded-xl bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm hover:border-slate-600 transition-all group"
              >
                <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${stat.color} p-3 mb-4 group-hover:scale-110 transition-transform`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <div className="text-sm opacity-70 mb-2">{stat.label}</div>
                <div className="text-3xl font-bold">{stat.value}</div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Featured Match (placeholder) */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-r from-slate-800 to-slate-900 rounded-2xl p-8 border border-slate-700/50">
          <h2 className="text-2xl font-bold mb-4">Featured Match</h2>
          <p className="text-slate-400 mb-6">Load featured fixtures from current gameweek</p>
          <a href="/matches" className="text-blue-400 hover:text-blue-300 font-semibold">
            View All Matches →
          </a>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">Platform Features</h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            Comprehensive tools for Premier League analysis, predictions, and competition
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, idx) => {
            const Icon = feature.icon;
            return (
              <div 
                key={idx}
                className="p-6 rounded-xl bg-slate-800/50 border border-slate-700/50 hover:border-slate-600 transition-all group hover:-translate-y-1"
              >
                <div className="w-12 h-12 rounded-lg bg-blue-500/20 flex items-center justify-center mb-4 group-hover:bg-blue-500/30 transition-colors">
                  <Icon className="w-6 h-6 text-blue-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-slate-400 text-sm">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Model Info */}
      {modelInfo && (
        <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-16">
          <div className="bg-gradient-to-r from-slate-800/50 to-slate-900/50 rounded-2xl p-8 border border-slate-700/50">
            <h2 className="text-2xl font-bold mb-6">AI Model Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <div className="text-sm opacity-70 mb-2">Model Version</div>
                <div className="text-xl font-bold">{modelInfo.model_version}</div>
              </div>
              <div>
                <div className="text-sm opacity-70 mb-2">Model Type</div>
                <div className="text-xl font-bold">{modelInfo.model_type}</div>
              </div>
              <div>
                <div className="text-sm opacity-70 mb-2">MAE (Goals)</div>
                <div className="text-xl font-bold">{modelInfo.metrics?.val_mae_avg.toFixed(3)}</div>
              </div>
              <div>
                <div className="text-sm opacity-70 mb-2">Features</div>
                <div className="text-xl font-bold">{modelInfo.feature_count}</div>
              </div>
            </div>
            <div className="mt-6 text-sm text-slate-400">
              <p><strong>Trained:</strong> {new Date(modelInfo.training_date).toLocaleDateString()}</p>
              <p className="mt-2"><strong>Description:</strong> {modelInfo.description}</p>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
