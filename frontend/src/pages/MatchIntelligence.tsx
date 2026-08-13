import React, { useState } from 'react';
import { TrendingUp, Target, Users, Wind, Zap } from 'lucide-react';
import apiService, { PredictionResponse } from '../services/api';

interface MatchCard {
  home_team: string;
  away_team: string;
  predicted_home_goals: number;
  predicted_away_goals: number;
  predicted_result: 'H' | 'D' | 'A';
  confidence: {
    home_win: number;
    draw: number;
    away_win: number;
  };
  kickoff?: string;
}

const SAMPLE_MATCHES: MatchCard[] = [
  {
    home_team: 'Arsenal',
    away_team: 'Chelsea',
    predicted_home_goals: 1.85,
    predicted_away_goals: 1.42,
    predicted_result: 'H',
    confidence: { home_win: 0.70, draw: 0.15, away_win: 0.15 },
    kickoff: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    home_team: 'Manchester United',
    away_team: 'Liverpool',
    predicted_home_goals: 1.23,
    predicted_away_goals: 2.17,
    predicted_result: 'A',
    confidence: { home_win: 0.20, draw: 0.25, away_win: 0.55 },
    kickoff: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    home_team: 'Manchester City',
    away_team: 'Tottenham',
    predicted_home_goals: 2.34,
    predicted_away_goals: 0.89,
    predicted_result: 'H',
    confidence: { home_win: 0.75, draw: 0.12, away_win: 0.13 },
    kickoff: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    home_team: 'Brighton',
    away_team: 'Newcastle',
    predicted_home_goals: 1.56,
    predicted_away_goals: 1.67,
    predicted_result: 'D',
    confidence: { home_win: 0.35, draw: 0.40, away_win: 0.25 },
    kickoff: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
  },
];

interface MatchCardProps {
  match: MatchCard;
  expanded: boolean;
  onToggle: () => void;
}

function MatchCardComponent({ match, expanded, onToggle }: MatchCardProps) {
  const resultColor = 
    match.predicted_result === 'H' ? 'from-green-500 to-emerald-500' :
    match.predicted_result === 'A' ? 'from-red-500 to-rose-500' :
    'from-yellow-500 to-amber-500';

  const resultLabel = 
    match.predicted_result === 'H' ? 'Home Win' :
    match.predicted_result === 'A' ? 'Away Win' :
    'Draw';

  const topConfidence = 
    match.predicted_result === 'H' ? match.confidence.home_win :
    match.predicted_result === 'A' ? match.confidence.away_win :
    match.confidence.draw;

  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden hover:border-slate-600 transition-all">
      <div 
        onClick={onToggle}
        className="p-6 cursor-pointer hover:bg-slate-800/70 transition-colors"
      >
        {/* Match Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex-1">
            <div className="text-sm opacity-70 mb-2">Gameweek 1</div>
            <div className="flex items-center justify-between">
              <div className="text-lg font-bold">{match.home_team}</div>
              <div className="text-center">
                <div className={`text-2xl font-black bg-gradient-to-r ${resultColor} bg-clip-text text-transparent mb-1`}>
                  {match.predicted_home_goals.toFixed(1)} - {match.predicted_away_goals.toFixed(1)}
                </div>
                <div className={`text-xs px-3 py-1 rounded-full bg-gradient-to-r ${resultColor} text-white font-semibold`}>
                  {resultLabel}
                </div>
              </div>
              <div className="text-lg font-bold text-right">{match.away_team}</div>
            </div>
          </div>
        </div>

        {/* Confidence Bars */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          <div>
            <div className="text-xs opacity-70 mb-1">Home</div>
            <div className="w-full bg-slate-700/50 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full transition-all"
                style={{ width: `${match.confidence.home_win * 100}%` }}
              />
            </div>
            <div className="text-xs font-semibold mt-1">{(match.confidence.home_win * 100).toFixed(0)}%</div>
          </div>
          <div>
            <div className="text-xs opacity-70 mb-1">Draw</div>
            <div className="w-full bg-slate-700/50 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-yellow-500 to-amber-500 h-2 rounded-full transition-all"
                style={{ width: `${match.confidence.draw * 100}%` }}
              />
            </div>
            <div className="text-xs font-semibold mt-1">{(match.confidence.draw * 100).toFixed(0)}%</div>
          </div>
          <div>
            <div className="text-xs opacity-70 mb-1">Away</div>
            <div className="w-full bg-slate-700/50 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-red-500 to-rose-500 h-2 rounded-full transition-all"
                style={{ width: `${match.confidence.away_win * 100}%` }}
              />
            </div>
            <div className="text-xs font-semibold mt-1">{(match.confidence.away_win * 100).toFixed(0)}%</div>
          </div>
        </div>

        {/* Kickoff Time */}
        <div className="text-xs opacity-70">
          Kickoff: {match.kickoff ? new Date(match.kickoff).toLocaleString() : 'TBD'}
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="border-t border-slate-700/50 p-6 bg-slate-900/30 space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-700/30 rounded-lg p-4">
              <div className="text-sm opacity-70 mb-2 flex items-center gap-2">
                <Wind size={16} /> xG
              </div>
              <div className="text-lg font-bold">{match.predicted_home_goals.toFixed(1)}</div>
              <div className="text-xs opacity-70">Expected Goals</div>
            </div>
            <div className="bg-slate-700/30 rounded-lg p-4">
              <div className="text-sm opacity-70 mb-2 flex items-center gap-2">
                <Target size={16} /> Most Likely
              </div>
              <div className="text-lg font-bold">{Math.round(match.predicted_home_goals)}-{Math.round(match.predicted_away_goals)}</div>
              <div className="text-xs opacity-70">Scoreline</div>
            </div>
            <div className="bg-slate-700/30 rounded-lg p-4">
              <div className="text-sm opacity-70 mb-2 flex items-center gap-2">
                <Zap size={16} /> Confidence
              </div>
              <div className="text-lg font-bold">{(topConfidence * 100).toFixed(0)}%</div>
              <div className="text-xs opacity-70">{resultLabel}</div>
            </div>
            <div className="bg-slate-700/30 rounded-lg p-4">
              <div className="text-sm opacity-70 mb-2 flex items-center gap-2">
                <TrendingUp size={16} /> Over/Under
              </div>
              <div className="text-lg font-bold">{(match.predicted_home_goals + match.predicted_away_goals).toFixed(1)}</div>
              <div className="text-xs opacity-70">Total Goals</div>
            </div>
          </div>

          <div className="bg-slate-700/30 rounded-lg p-4">
            <div className="text-sm font-semibold mb-3">AI Analysis</div>
            <p className="text-sm text-slate-300">
              The model predicts a {resultLabel.toLowerCase()} with {(topConfidence * 100).toFixed(0)}% confidence. 
              Expected goals suggest an average of {(match.predicted_home_goals + match.predicted_away_goals).toFixed(1)} total goals in this encounter.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function MatchIntelligence() {
  const [matches, setMatches] = useState<MatchCard[]>(SAMPLE_MATCHES);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [filter, setFilter] = useState<'all' | 'home' | 'draw' | 'away'>('all');
  const [loading, setLoading] = useState(false);

  const filteredMatches = matches.filter(match => {
    if (filter === 'home') return match.predicted_result === 'H';
    if (filter === 'draw') return match.predicted_result === 'D';
    if (filter === 'away') return match.predicted_result === 'A';
    return true;
  });

  return (
    <div className="min-h-screen py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-12">
        <h1 className="text-4xl sm:text-5xl font-bold mb-4">Match Intelligence</h1>
        <p className="text-lg text-slate-400 max-w-2xl">
          AI-powered predictions for every Premier League fixture with detailed analysis and confidence scores.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-8">
        {['all', 'home', 'draw', 'away'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f as any)}
            className={`px-4 py-2 rounded-lg font-semibold transition-all ${
              filter === f
                ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            {f === 'all' ? 'All Matches' : f === 'home' ? 'Home Wins' : f === 'draw' ? 'Draws' : 'Away Wins'}
          </button>
        ))}
      </div>

      {/* Matches Grid */}
      <div className="space-y-4 mb-16">
        {filteredMatches.map((match, idx) => (
          <MatchCardComponent
            key={idx}
            match={match}
            expanded={expandedIndex === idx}
            onToggle={() => setExpandedIndex(expandedIndex === idx ? null : idx)}
          />
        ))}
      </div>

      {/* Summary Stats */}
      <div className="bg-gradient-to-r from-slate-800/50 to-slate-900/50 rounded-xl p-8 border border-slate-700/50">
        <h2 className="text-2xl font-bold mb-6">Gameweek Summary</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-sm opacity-70 mb-2">Total Matches</div>
            <div className="text-3xl font-bold">{filteredMatches.length}</div>
          </div>
          <div>
            <div className="text-sm opacity-70 mb-2">Home Wins</div>
            <div className="text-3xl font-bold text-green-400">{matches.filter(m => m.predicted_result === 'H').length}</div>
          </div>
          <div>
            <div className="text-sm opacity-70 mb-2">Draws</div>
            <div className="text-3xl font-bold text-yellow-400">{matches.filter(m => m.predicted_result === 'D').length}</div>
          </div>
          <div>
            <div className="text-sm opacity-70 mb-2">Away Wins</div>
            <div className="text-3xl font-bold text-red-400">{matches.filter(m => m.predicted_result === 'A').length}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
