import React, { useState } from 'react';
import { Search, TrendingUp, Target, Shield, Activity } from 'lucide-react';

interface Player {
  id: number;
  name: string;
  team: string;
  position: string;
  number: number;
  goals: number;
  assists: number;
  appearances: number;
  minutes_played: number;
  rating: number;
  form: string;
}

const PLAYERS: Player[] = [
  {
    id: 1,
    name: 'Erling Haaland',
    team: 'Manchester City',
    position: 'ST',
    number: 9,
    goals: 24,
    assists: 5,
    appearances: 30,
    minutes_played: 2340,
    rating: 9.1,
    form: 'WWWWW',
  },
  {
    id: 2,
    name: 'Bukayo Saka',
    team: 'Arsenal',
    position: 'RW',
    number: 7,
    goals: 12,
    assists: 8,
    appearances: 28,
    minutes_played: 2100,
    rating: 8.5,
    form: 'WWWDW',
  },
  {
    id: 3,
    name: 'Mohamed Salah',
    team: 'Liverpool',
    position: 'RW',
    number: 11,
    goals: 18,
    assists: 9,
    appearances: 29,
    minutes_played: 2250,
    rating: 8.8,
    form: 'WWWWD',
  },
  {
    id: 4,
    name: 'Phil Foden',
    team: 'Manchester City',
    position: 'LW',
    number: 14,
    goals: 15,
    assists: 7,
    appearances: 27,
    minutes_played: 2010,
    rating: 8.6,
    form: 'WWDWW',
  },
  {
    id: 5,
    name: 'Declan Rice',
    team: 'Arsenal',
    position: 'CM',
    number: 41,
    goals: 2,
    assists: 1,
    appearances: 30,
    minutes_played: 2700,
    rating: 8.2,
    form: 'WDWWW',
  },
  {
    id: 6,
    name: 'Jude Bellingham',
    team: 'Manchester United',
    position: 'CM',
    number: 5,
    goals: 5,
    assists: 3,
    appearances: 26,
    minutes_played: 1950,
    rating: 8.1,
    form: 'WWDWD',
  },
  {
    id: 7,
    name: 'Harry Kane',
    team: 'Tottenham',
    position: 'ST',
    number: 10,
    goals: 16,
    assists: 4,
    appearances: 27,
    minutes_played: 2160,
    rating: 8.4,
    form: 'WDWWD',
  },
  {
    id: 8,
    name: 'Son Heung-min',
    team: 'Tottenham',
    position: 'LW',
    number: 7,
    goals: 10,
    assists: 6,
    appearances: 25,
    minutes_played: 1875,
    rating: 8.0,
    form: 'WDWDW',
  },
];

interface PlayerCardProps {
  player: Player;
}

function PlayerCard({ player }: PlayerCardProps) {
  const positionColor: { [key: string]: string } = {
    'ST': 'from-red-500 to-rose-500',
    'RW': 'from-blue-500 to-cyan-500',
    'LW': 'from-purple-500 to-pink-500',
    'CM': 'from-green-500 to-emerald-500',
    'CB': 'from-yellow-500 to-orange-500',
    'GK': 'from-slate-500 to-slate-600',
  };

  const formEmojis: { [key: string]: string } = {
    'W': '✅',
    'D': '⚽',
    'L': '❌',
  };

  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden hover:border-slate-600 transition-all group">
      {/* Player Header */}
      <div className={`p-6 bg-gradient-to-r ${positionColor[player.position]} bg-opacity-10`}>
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="text-sm font-semibold text-slate-400 mb-1">{player.team}</div>
            <h3 className="text-2xl font-bold">{player.name}</h3>
            <div className="flex gap-2 mt-2">
              <span className={`px-3 py-1 rounded-full bg-gradient-to-r ${positionColor[player.position]} text-white text-xs font-bold`}>
                {player.position}
              </span>
              <span className="px-3 py-1 rounded-full bg-slate-700 text-slate-300 text-xs font-bold">
                #{player.number}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-yellow-400">{player.rating.toFixed(1)}</div>
            <div className="text-xs text-slate-400">Rating</div>
          </div>
        </div>

        {/* Recent Form */}
        <div className="flex gap-1">
          {player.form.split('').map((result, idx) => (
            <div 
              key={idx}
              title={result === 'W' ? 'Win' : result === 'D' ? 'Draw' : 'Loss'}
              className={`w-5 h-5 rounded flex items-center justify-center text-xs font-bold ${
                result === 'W' ? 'bg-green-500/30 text-green-400' :
                result === 'D' ? 'bg-yellow-500/30 text-yellow-400' :
                'bg-red-500/30 text-red-400'
              }`}
            >
              {formEmojis[result]}
            </div>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          {/* Goals */}
          <div className="bg-slate-700/30 rounded-lg p-4">
            <div className="text-xs opacity-70 mb-2 flex items-center gap-1">
              <Target size={14} /> Goals
            </div>
            <div className="text-2xl font-bold text-red-400">{player.goals}</div>
            <div className="text-xs text-slate-400 mt-1">{player.appearances} apps</div>
          </div>

          {/* Assists */}
          <div className="bg-slate-700/30 rounded-lg p-4">
            <div className="text-xs opacity-70 mb-2 flex items-center gap-1">
              <Activity size={14} /> Assists
            </div>
            <div className="text-2xl font-bold text-blue-400">{player.assists}</div>
            <div className="text-xs text-slate-400 mt-1">Per {Math.round(player.appearances / player.assists)} apps</div>
          </div>

          {/* Minutes */}
          <div className="bg-slate-700/30 rounded-lg p-4">
            <div className="text-xs opacity-70 mb-2">Minutes Played</div>
            <div className="text-lg font-bold">{(player.minutes_played / 60).toFixed(0)}h</div>
            <div className="text-xs text-slate-400 mt-1">{player.minutes_played} mins</div>
          </div>

          {/* Appearances */}
          <div className="bg-slate-700/30 rounded-lg p-4">
            <div className="text-xs opacity-70 mb-2 flex items-center gap-1">
              <TrendingUp size={14} /> Appearances
            </div>
            <div className="text-2xl font-bold text-green-400">{player.appearances}</div>
            <div className="text-xs text-slate-400 mt-1">This season</div>
          </div>
        </div>

        {/* Stats Bars */}
        <div className="space-y-3 mt-6 pt-6 border-t border-slate-700/50">
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-xs font-semibold">Attacking Power</span>
              <span className="text-xs text-slate-400">{Math.round((player.goals + player.assists) / player.appearances * 10)}</span>
            </div>
            <div className="w-full bg-slate-700/50 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-red-500 to-rose-500 h-2 rounded-full"
                style={{ width: `${Math.min((player.goals + player.assists) / player.appearances * 100, 100)}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between mb-2">
              <span className="text-xs font-semibold">Consistency</span>
              <span className="text-xs text-slate-400">{Math.round(player.appearances / 30 * 100)}</span>
            </div>
            <div className="w-full bg-slate-700/50 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full"
                style={{ width: `${player.appearances / 30 * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Players() {
  const [searchQuery, setSearchQuery] = useState('');
  const [positionFilter, setPositionFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'rating' | 'goals' | 'assists' | 'appearances'>('rating');

  const positions = ['all', ...new Set(PLAYERS.map(p => p.position))];

  const filtered = PLAYERS.filter(player => {
    const matchesSearch = player.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         player.team.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesPosition = positionFilter === 'all' || player.position === positionFilter;
    return matchesSearch && matchesPosition;
  });

  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'rating') return b.rating - a.rating;
    if (sortBy === 'goals') return b.goals - a.goals;
    if (sortBy === 'assists') return b.assists - a.assists;
    if (sortBy === 'appearances') return b.appearances - a.appearances;
    return 0;
  });

  return (
    <div className="min-h-screen py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-12">
        <h1 className="text-4xl sm:text-5xl font-bold mb-4">Players</h1>
        <p className="text-lg text-slate-400 max-w-2xl">
          Browse all Premier League players with detailed statistics and performance metrics.
        </p>
      </div>

      {/* Search and Filters */}
      <div className="mb-8 space-y-4">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={20} />
          <input
            type="text"
            placeholder="Search players or teams..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-field pl-12 w-full"
          />
        </div>

        {/* Position Filter */}
        <div className="flex flex-wrap gap-2">
          {positions.map((pos) => (
            <button
              key={pos}
              onClick={() => setPositionFilter(pos)}
              className={`px-4 py-2 rounded-lg font-semibold transition-all text-sm ${
                positionFilter === pos
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {pos === 'all' ? 'All Positions' : pos}
            </button>
          ))}
        </div>

        {/* Sort Buttons */}
        <div className="flex flex-wrap gap-3">
          {(['rating', 'goals', 'assists', 'appearances'] as const).map((sort) => (
            <button
              key={sort}
              onClick={() => setSortBy(sort)}
              className={`px-4 py-2 rounded-lg font-semibold transition-all text-sm ${
                sortBy === sort
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {sort === 'rating' ? 'By Rating' : sort === 'goals' ? 'By Goals' : sort === 'assists' ? 'By Assists' : 'By Apps'}
            </button>
          ))}
        </div>
      </div>

      {/* Players Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
        {sorted.map((player) => (
          <PlayerCard key={player.id} player={player} />
        ))}
      </div>

      {/* No Results */}
      {sorted.length === 0 && (
        <div className="text-center py-12">
          <p className="text-lg text-slate-400">
            No players found matching your filters
          </p>
        </div>
      )}

      {/* Stats Summary */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-8">
        <h2 className="text-2xl font-bold mb-6">League Statistics</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-sm opacity-70 mb-2">Total Players</div>
            <div className="text-3xl font-bold">{PLAYERS.length}</div>
          </div>
          <div>
            <div className="text-sm opacity-70 mb-2">Top Scorer</div>
            <div className="text-2xl font-bold text-red-400">
              {PLAYERS.reduce((max, p) => p.goals > max.goals ? p : max).name.split(' ')[1]}
            </div>
            <div className="text-xs text-slate-400">
              {PLAYERS.reduce((max, p) => p.goals > max.goals ? p : max).goals} goals
            </div>
          </div>
          <div>
            <div className="text-sm opacity-70 mb-2">Most Assists</div>
            <div className="text-2xl font-bold text-blue-400">
              {PLAYERS.reduce((max, p) => p.assists > max.assists ? p : max).name.split(' ')[1]}
            </div>
            <div className="text-xs text-slate-400">
              {PLAYERS.reduce((max, p) => p.assists > max.assists ? p : max).assists} assists
            </div>
          </div>
          <div>
            <div className="text-sm opacity-70 mb-2">Avg Rating</div>
            <div className="text-3xl font-bold text-yellow-400">
              {(PLAYERS.reduce((sum, p) => sum + p.rating, 0) / PLAYERS.length).toFixed(1)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
