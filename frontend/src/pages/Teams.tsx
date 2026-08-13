import React, { useState } from 'react';
import { Search, TrendingUp, Shield, Target, Users } from 'lucide-react';

interface Team {
  id: number;
  name: string;
  badge: string;
  form: string;
  win_rate: number;
  attack_strength: number;
  defense_strength: number;
  goals_for: number;
  goals_against: number;
  position: number;
  points: number;
  next_fixtures?: {
    opponent: string;
    home: boolean;
    date: string;
  }[];
}

const TEAMS: Team[] = [
  {
    id: 1,
    name: 'Manchester City',
    badge: '🔵',
    form: 'WWWWW',
    win_rate: 78,
    attack_strength: 92,
    defense_strength: 88,
    goals_for: 89,
    goals_against: 28,
    position: 1,
    points: 86,
    next_fixtures: [
      { opponent: 'Arsenal', home: false, date: '2026-08-17' },
      { opponent: 'Brighton', home: true, date: '2026-08-24' },
    ],
  },
  {
    id: 2,
    name: 'Arsenal',
    badge: '🔴',
    form: 'WWWDW',
    win_rate: 71,
    attack_strength: 88,
    defense_strength: 85,
    goals_for: 84,
    goals_against: 35,
    position: 2,
    points: 82,
    next_fixtures: [
      { opponent: 'Manchester City', home: true, date: '2026-08-17' },
      { opponent: 'Tottenham', home: false, date: '2026-08-25' },
    ],
  },
  {
    id: 3,
    name: 'Liverpool',
    badge: '🔴',
    form: 'WWWWD',
    win_rate: 68,
    attack_strength: 85,
    defense_strength: 82,
    goals_for: 81,
    goals_against: 38,
    position: 3,
    points: 79,
    next_fixtures: [
      { opponent: 'Manchester United', home: true, date: '2026-08-18' },
      { opponent: 'Fulham', home: false, date: '2026-08-26' },
    ],
  },
  {
    id: 4,
    name: 'Manchester United',
    badge: '🔴',
    form: 'WWDWW',
    win_rate: 65,
    attack_strength: 80,
    defense_strength: 78,
    goals_for: 76,
    goals_against: 42,
    position: 4,
    points: 75,
    next_fixtures: [
      { opponent: 'Liverpool', home: false, date: '2026-08-18' },
      { opponent: 'Chelsea', home: true, date: '2026-08-27' },
    ],
  },
  {
    id: 5,
    name: 'Tottenham',
    badge: '⚪',
    form: 'WDWWW',
    win_rate: 62,
    attack_strength: 82,
    defense_strength: 76,
    goals_for: 73,
    goals_against: 45,
    position: 5,
    points: 72,
    next_fixtures: [
      { opponent: 'Newcastle', home: true, date: '2026-08-19' },
      { opponent: 'Arsenal', home: true, date: '2026-08-25' },
    ],
  },
  {
    id: 6,
    name: 'Chelsea',
    badge: '🔵',
    form: 'WDWWD',
    win_rate: 58,
    attack_strength: 78,
    defense_strength: 75,
    goals_for: 68,
    goals_against: 48,
    position: 6,
    points: 67,
    next_fixtures: [
      { opponent: 'Brighton', home: false, date: '2026-08-20' },
      { opponent: 'Manchester United', home: false, date: '2026-08-27' },
    ],
  },
  {
    id: 7,
    name: 'Newcastle',
    badge: '⚫',
    form: 'WDWDW',
    win_rate: 55,
    attack_strength: 75,
    defense_strength: 78,
    goals_for: 62,
    goals_against: 44,
    position: 7,
    points: 64,
    next_fixtures: [
      { opponent: 'Tottenham', home: false, date: '2026-08-19' },
      { opponent: 'Brighton', home: true, date: '2026-08-28' },
    ],
  },
  {
    id: 8,
    name: 'Brighton',
    badge: '💙',
    form: 'WDWDW',
    win_rate: 52,
    attack_strength: 72,
    defense_strength: 80,
    goals_for: 58,
    goals_against: 40,
    position: 8,
    points: 60,
    next_fixtures: [
      { opponent: 'Manchester City', home: false, date: '2026-08-24' },
      { opponent: 'Chelsea', home: true, date: '2026-08-20' },
    ],
  },
];

interface TeamCardProps {
  team: Team;
}

function TeamCard({ team }: TeamCardProps) {
  const formEmojis: { [key: string]: string } = {
    'W': '✅',
    'D': '⚽',
    'L': '❌',
  };

  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden hover:border-slate-600 transition-all group">
      {/* Team Header */}
      <div className="p-6 bg-gradient-to-r from-slate-800/50 to-slate-900/50 border-b border-slate-700/50">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <span className="text-4xl">{team.badge}</span>
            <div>
              <div className="text-2xl font-bold">{team.name}</div>
              <div className="text-sm text-slate-400">Position #{team.position}</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-blue-400">{team.points}</div>
            <div className="text-xs text-slate-400">Points</div>
          </div>
        </div>

        {/* Recent Form */}
        <div className="flex gap-1">
          {team.form.split('').map((result, idx) => (
            <div 
              key={idx}
              title={result === 'W' ? 'Win' : result === 'D' ? 'Draw' : 'Loss'}
              className={`w-6 h-6 rounded flex items-center justify-center text-xs font-bold ${
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

      {/* Stats Grid */}
      <div className="p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          {/* Attack */}
          <div className="bg-slate-700/30 rounded-lg p-3">
            <div className="text-xs opacity-70 mb-2 flex items-center gap-1">
              <Target size={14} /> Attack
            </div>
            <div className="text-lg font-bold">{team.attack_strength}</div>
            <div className="w-full bg-slate-600/50 rounded-full h-1 mt-2">
              <div 
                className="bg-gradient-to-r from-blue-500 to-purple-600 h-1 rounded-full"
                style={{ width: `${team.attack_strength}%` }}
              />
            </div>
          </div>

          {/* Defense */}
          <div className="bg-slate-700/30 rounded-lg p-3">
            <div className="text-xs opacity-70 mb-2 flex items-center gap-1">
              <Shield size={14} /> Defense
            </div>
            <div className="text-lg font-bold">{team.defense_strength}</div>
            <div className="w-full bg-slate-600/50 rounded-full h-1 mt-2">
              <div 
                className="bg-gradient-to-r from-green-500 to-emerald-600 h-1 rounded-full"
                style={{ width: `${team.defense_strength}%` }}
              />
            </div>
          </div>

          {/* Goals For */}
          <div className="bg-slate-700/30 rounded-lg p-3">
            <div className="text-xs opacity-70 mb-2">Goals For</div>
            <div className="text-lg font-bold text-blue-400">{team.goals_for}</div>
          </div>

          {/* Goals Against */}
          <div className="bg-slate-700/30 rounded-lg p-3">
            <div className="text-xs opacity-70 mb-2">Goals Against</div>
            <div className="text-lg font-bold text-red-400">{team.goals_against}</div>
          </div>
        </div>

        {/* Win Rate */}
        <div>
          <div className="text-sm opacity-70 mb-2 flex items-center gap-2">
            <TrendingUp size={16} /> Win Rate
          </div>
          <div className="flex items-center gap-3">
            <div className="flex-1 bg-slate-700/50 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-green-500 to-emerald-600 h-2 rounded-full"
                style={{ width: `${team.win_rate}%` }}
              />
            </div>
            <span className="text-lg font-bold text-green-400">{team.win_rate}%</span>
          </div>
        </div>

        {/* Next Fixtures */}
        {team.next_fixtures && team.next_fixtures.length > 0 && (
          <div className="mt-6 pt-6 border-t border-slate-700/50">
            <div className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Users size={16} /> Upcoming Fixtures
            </div>
            <div className="space-y-2">
              {team.next_fixtures.map((fixture, idx) => (
                <div key={idx} className="flex items-center justify-between text-sm">
                  <span className={fixture.home ? 'text-blue-400' : 'text-slate-400'}>
                    {fixture.home ? '🏠' : '🚗'} {fixture.opponent}
                  </span>
                  <span className="text-xs opacity-70">
                    {new Date(fixture.date).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Teams() {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'points' | 'attack' | 'defense' | 'name'>('points');

  const filtered = TEAMS.filter(team =>
    team.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'points') return b.points - a.points;
    if (sortBy === 'attack') return b.attack_strength - a.attack_strength;
    if (sortBy === 'defense') return b.defense_strength - a.defense_strength;
    if (sortBy === 'name') return a.name.localeCompare(b.name);
    return 0;
  });

  return (
    <div className="min-h-screen py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-12">
        <h1 className="text-4xl sm:text-5xl font-bold mb-4">Teams</h1>
        <p className="text-lg text-slate-400 max-w-2xl">
          Explore all 20 Premier League teams with detailed statistics, form, and upcoming fixtures.
        </p>
      </div>

      {/* Search and Filters */}
      <div className="mb-8 space-y-4">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={20} />
          <input
            type="text"
            placeholder="Search teams..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-field pl-12 text-white"
          />
        </div>

        {/* Sort Buttons */}
        <div className="flex flex-wrap gap-3">
          {(['points', 'attack', 'defense', 'name'] as const).map((sort) => (
            <button
              key={sort}
              onClick={() => setSortBy(sort)}
              className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                sortBy === sort
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {sort === 'points' ? 'By Points' : sort === 'attack' ? 'By Attack' : sort === 'defense' ? 'By Defense' : 'By Name'}
            </button>
          ))}
        </div>
      </div>

      {/* Teams Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
        {sorted.map((team) => (
          <TeamCard key={team.id} team={team} />
        ))}
      </div>

      {/* No Results */}
      {sorted.length === 0 && (
        <div className="text-center py-12">
          <p className="text-lg text-slate-400">No teams found matching "{searchQuery}"</p>
        </div>
      )}

      {/* League Summary */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-8">
        <h2 className="text-2xl font-bold mb-6">League Overview</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-sm opacity-70 mb-2">Total Teams</div>
            <div className="text-3xl font-bold">{TEAMS.length}</div>
          </div>
          <div>
            <div className="text-sm opacity-70 mb-2">Avg Goals/Team</div>
            <div className="text-3xl font-bold">
              {(TEAMS.reduce((sum, t) => sum + t.goals_for, 0) / TEAMS.length).toFixed(1)}
            </div>
          </div>
          <div>
            <div className="text-sm opacity-70 mb-2">Avg Points/Team</div>
            <div className="text-3xl font-bold">
              {(TEAMS.reduce((sum, t) => sum + t.points, 0) / TEAMS.length).toFixed(0)}
            </div>
          </div>
          <div>
            <div className="text-sm opacity-70 mb-2">Total Matches (Played)</div>
            <div className="text-3xl font-bold">{TEAMS[0].position * 2 - 1}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
