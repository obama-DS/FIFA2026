import React, { useState, useEffect } from 'react';
import { TrendingUp, Trophy, Target, AlertCircle, RefreshCw, Loader } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, ScatterChart, Scatter } from 'recharts';
import apiService from '../services/api';

interface TeamProjection {
  title_probability: number;
  top4_probability: number;
  top6_probability: number;
  relegation_probability: number;
  expected_points: number;
  expected_position: number;
  median_position: number;
  position_distribution: { [key: string]: number };
}

interface SeasonData {
  timestamp: string;
  simulations: number;
  season: string;
  teams: { [team: string]: TeamProjection };
  most_likely_table: Array<{
    position: number;
    team: string;
    expected_points: number;
    title_probability: number;
    top4_probability: number;
    top6_probability: number;
    relegation_probability: number;
  }>;
}

const TOP_TEAMS = ['Manchester City', 'Arsenal', 'Liverpool', 'Manchester United'];
const TEAM_COLORS: { [key: string]: string } = {
  'Manchester City': '#3b82f6',
  'Arsenal': '#ef4444',
  'Liverpool': '#10b981',
  'Manchester United': '#f59e0b',
  'Tottenham': '#8b5cf6',
  'Chelsea': '#06b6d4',
  'Newcastle': '#6b7280',
  'Brighton': '#06b6d4',
  'Aston Villa': '#7c2d12',
  'Fulham': '#1e293b',
  'West Ham': '#7c2d12',
  'Brentford': '#dc2626',
  'Crystal Palace': '#2563eb',
  'Bournemouth': '#dc2626',
  'Everton': '#1e40af',
  'Nottingham Forest': '#dc2626',
  'Ipswich Town': '#1e40af',
  'Leicester City': '#2563eb',
  'Wolverhampton': '#f59e0b',
  'Southampton': '#dc2626',
  'Luton Town': '#dc2626',
};

export default function SeasonOracle() {
  const [data, setData] = useState<SeasonData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'points' | 'title' | 'top4' | 'relegation'>('points');
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);

  useEffect(() => {
    loadSeasonData();
  }, []);

  const loadSeasonData = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiService.getSeasonProjections();
      
      if (!result || !result.teams || Object.keys(result.teams).length === 0) {
        setError('No season projection data available');
        setData(null);
      } else {
        setData(result);
      }
    } catch (err) {
      console.error('Failed to load season data:', err);
      setError('Failed to load season projections. Make sure the backend is running.');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
          <h1 className="text-4xl sm:text-5xl font-bold mb-4">Season Oracle</h1>
          <p className="text-lg text-slate-400">
            Loading season projections...
          </p>
        </div>
        
        <div className="flex flex-col items-center justify-center py-24">
          <Loader className="w-12 h-12 text-blue-400 animate-spin mb-4" />
          <p className="text-slate-400 text-lg">Generating Monte Carlo simulations...</p>
          <p className="text-slate-500 text-sm mt-2">(This may take a few minutes on first run)</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
          <h1 className="text-4xl sm:text-5xl font-bold mb-4">Season Oracle</h1>
        </div>
        
        <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-8 mb-8">
          <div className="flex items-start gap-4">
            <AlertCircle className="text-red-400 flex-shrink-0 mt-1" size={24} />
            <div className="flex-1">
              <h3 className="font-bold text-lg mb-2">Unable to Load Season Projections</h3>
              <p className="text-slate-300 mb-4">{error}</p>
              <button
                onClick={loadSeasonData}
                className="inline-flex items-center gap-2 px-4 py-2 bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg transition-all"
              >
                <RefreshCw size={18} />
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Prepare data for charts
  const titleOdds = Object.entries(data.teams)
    .sort((a, b) => b[1].title_probability - a[1].title_probability)
    .slice(0, 8)
    .map(([team, stats]) => ({
      team,
      probability: stats.title_probability,
    }));

  const topTeamsData = TOP_TEAMS.filter(t => t in data.teams).map(team => ({
    team,
    title: data.teams[team].title_probability,
    top4: data.teams[team].top4_probability,
    top6: data.teams[team].top6_probability,
    expected_points: data.teams[team].expected_points,
  }));

  // Sort table based on selected sort
  const sortedTable = [...(data.most_likely_table || [])].sort((a, b) => {
    if (sortBy === 'points') return b.expected_points - a.expected_points;
    if (sortBy === 'title') return b.title_probability - a.title_probability;
    if (sortBy === 'top4') return b.top4_probability - a.top4_probability;
    if (sortBy === 'relegation') return b.relegation_probability - a.relegation_probability;
    return 0;
  });

  const selectedTeamData = selectedTeam && data.teams[selectedTeam] ? {
    team: selectedTeam,
    ...data.teams[selectedTeam],
  } : null;

  // Get position distribution for selected team
  const positionDistData = selectedTeamData 
    ? Object.entries(selectedTeamData.position_distribution)
        .map(([pos, count]) => ({
          position: parseInt(pos),
          frequency: count,
        }))
        .sort((a, b) => a.position - b.position)
    : [];

  return (
    <div className="min-h-screen py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-12">
        <h1 className="text-4xl sm:text-5xl font-bold mb-4">Season Oracle</h1>
        <p className="text-lg text-slate-400 max-w-2xl">
          AI-powered 2026/27 season projections using Monte Carlo simulations.
          <span className="block mt-2 text-sm">
            <strong className="text-blue-400">{data.simulations.toLocaleString()}</strong> simulations • Results as of {new Date(data.timestamp).toLocaleDateString()}
          </span>
        </p>
      </div>

      {/* Top Contenders Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
        {/* Title Odds */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-8">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <Trophy size={28} className="text-yellow-400" />
            Championship Odds
          </h2>
          
          <div className="space-y-4">
            {titleOdds.map((item, idx) => (
              <div key={item.team}>
                <div className="flex justify-between items-center mb-2">
                  <span className="font-semibold">{idx + 1}. {item.team}</span>
                  <span className="text-lg font-bold text-blue-400">{item.probability.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-slate-700/50 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all"
                    style={{ width: `${Math.max(item.probability / 100 * 100, 2)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-6 border-t border-slate-700/50 text-sm text-slate-400">
            <p>Based on {data.simulations.toLocaleString()} season simulations</p>
            <p>Higher percentages indicate stronger likelihood of winning the title</p>
          </div>
        </div>

        {/* Qualification Odds */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-8">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <Target size={28} className="text-blue-400" />
            Qualification Probabilities
          </h2>
          
          <div className="space-y-4">
            {topTeamsData.map((item) => (
              <div key={item.team} className="space-y-2">
                <div className="font-semibold text-sm">{item.team}</div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <div className="text-xs opacity-70 mb-1">Title</div>
                    <div className="text-sm font-bold text-yellow-400">{item.title.toFixed(0)}%</div>
                  </div>
                  <div>
                    <div className="text-xs opacity-70 mb-1">Top 4</div>
                    <div className="text-sm font-bold text-green-400">{item.top4.toFixed(0)}%</div>
                  </div>
                  <div>
                    <div className="text-xs opacity-70 mb-1">Top 6</div>
                    <div className="text-sm font-bold text-blue-400">{item.top6.toFixed(0)}%</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Contenders Comparison Chart */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-8 mb-12">
        <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <TrendingUp size={28} className="text-blue-400" />
          Top Teams - Qualification Comparison
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={topTeamsData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(100, 116, 139, 0.1)" />
            <XAxis dataKey="team" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
              cursor={{ fill: '#3b82f6' }}
            />
            <Legend />
            <Bar dataKey="title" fill="#fbbf24" name="Title %" />
            <Bar dataKey="top4" fill="#10b981" name="Top 4 %" />
            <Bar dataKey="top6" fill="#3b82f6" name="Top 6 %" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* League Table Controls */}
      <div className="flex flex-wrap gap-3 mb-8">
        {(['points', 'title', 'top4', 'relegation'] as const).map((sort) => (
          <button
            key={sort}
            onClick={() => setSortBy(sort)}
            className={`px-4 py-2 rounded-lg font-semibold transition-all ${
              sortBy === sort
                ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            {sort === 'points' ? 'By Points' : sort === 'title' ? 'Title Odds' : sort === 'top4' ? 'Top 4' : 'Relegation'}
          </button>
        ))}
      </div>

      {/* Most Likely Final League Table */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden mb-12">
        <div className="bg-slate-900/50 border-b border-slate-700/50 p-6">
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Trophy size={28} className="text-yellow-400" />
            Most Likely Final League Table
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-900/30 border-b border-slate-700/50">
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-400">Pos</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-400">Team</th>
                <th className="px-6 py-4 text-center text-sm font-semibold text-slate-400">Points</th>
                <th className="px-6 py-4 text-center text-sm font-semibold text-slate-400">Title %</th>
                <th className="px-6 py-4 text-center text-sm font-semibold text-slate-400">Top 4 %</th>
                <th className="px-6 py-4 text-center text-sm font-semibold text-slate-400">Top 6 %</th>
                {sortBy === 'relegation' && (
                  <th className="px-6 py-4 text-right text-sm font-semibold text-slate-400">Rel. %</th>
                )}
              </tr>
            </thead>
            <tbody>
              {sortedTable.map((team, idx) => {
                let rowBg = '';
                if (team.position <= 4) rowBg = 'bg-green-500/5 border-l-4 border-green-500';
                else if (team.position >= 18) rowBg = 'bg-red-500/5 border-l-4 border-red-500';
                else if (team.position <= 7) rowBg = 'bg-blue-500/5 border-l-4 border-blue-500';

                return (
                  <tr 
                    key={team.team}
                    onClick={() => setSelectedTeam(team.team)}
                    className={`border-b border-slate-700/50 hover:bg-slate-800/70 transition-colors cursor-pointer ${rowBg}`}
                  >
                    <td className="px-6 py-4 font-bold">{team.position}</td>
                    <td className="px-6 py-4 font-semibold">{team.team}</td>
                    <td className="px-6 py-4 text-center font-bold text-lg">{team.expected_points.toFixed(0)}</td>
                    <td className="px-6 py-4 text-center">
                      <span className={`px-2 py-1 rounded text-sm font-bold ${
                        team.title_probability > 20 ? 'bg-yellow-500/20 text-yellow-400' :
                        team.title_probability > 5 ? 'bg-orange-500/20 text-orange-400' :
                        'text-slate-400'
                      }`}>
                        {team.title_probability.toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`px-2 py-1 rounded text-sm font-bold ${
                        team.top4_probability > 50 ? 'bg-green-500/20 text-green-400' :
                        'text-slate-400'
                      }`}>
                        {team.top4_probability.toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`px-2 py-1 rounded text-sm font-bold ${
                        team.top6_probability > 50 ? 'bg-blue-500/20 text-blue-400' :
                        'text-slate-400'
                      }`}>
                        {team.top6_probability.toFixed(0)}%
                      </span>
                    </td>
                    {sortBy === 'relegation' && (
                      <td className="px-6 py-4 text-right">
                        <span className={`px-2 py-1 rounded text-sm font-bold ${
                          team.relegation_probability > 50 ? 'bg-red-500/20 text-red-400' :
                          'text-slate-400'
                        }`}>
                          {team.relegation_probability.toFixed(1)}%
                        </span>
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Team Details */}
      {selectedTeamData && (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-8 mb-12">
          <div className="flex items-start justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold mb-2">{selectedTeamData.team}</h2>
              <p className="text-slate-400">Detailed simulation breakdown</p>
            </div>
            <button
              onClick={() => setSelectedTeam(null)}
              className="text-slate-400 hover:text-slate-200 text-2xl"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-slate-700/30 rounded-lg p-6">
              <div className="text-sm opacity-70 mb-2">Championship Probability</div>
              <div className="text-3xl font-bold text-yellow-400">{selectedTeamData.title_probability.toFixed(1)}%</div>
            </div>

            <div className="bg-slate-700/30 rounded-lg p-6">
              <div className="text-sm opacity-70 mb-2">Top 4 Probability</div>
              <div className="text-3xl font-bold text-green-400">{selectedTeamData.top4_probability.toFixed(1)}%</div>
            </div>

            <div className="bg-slate-700/30 rounded-lg p-6">
              <div className="text-sm opacity-70 mb-2">Expected Points</div>
              <div className="text-3xl font-bold text-blue-400">{selectedTeamData.expected_points.toFixed(0)}</div>
            </div>

            <div className="bg-slate-700/30 rounded-lg p-6">
              <div className="text-sm opacity-70 mb-2">Expected Position</div>
              <div className="text-3xl font-bold text-purple-400">{selectedTeamData.expected_position.toFixed(1)}</div>
            </div>
          </div>

          {/* Position Distribution Chart */}
          {positionDistData.length > 0 && (
            <div>
              <h3 className="text-lg font-bold mb-4">Finish Position Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={positionDistData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(100, 116, 139, 0.1)" />
                  <XAxis dataKey="position" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                    cursor={{ fill: '#3b82f6' }}
                  />
                  <Bar dataKey="frequency" fill="#3b82f6" name="Frequency" />
                </BarChart>
              </ResponsiveContainer>
              <p className="text-sm text-slate-400 mt-4">
                Most likely position: <strong>#{selectedTeamData.median_position}</strong>
              </p>
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="font-semibold">Champions League</span>
          </div>
          <p className="text-sm text-slate-400">Positions 1-4</p>
        </div>
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            <span className="font-semibold">Europa League</span>
          </div>
          <p className="text-sm text-slate-400">Positions 5-7</p>
        </div>
        <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 rounded-full bg-orange-500" />
            <span className="font-semibold">Mid-Table</span>
          </div>
          <p className="text-sm text-slate-400">Positions 8-17</p>
        </div>
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span className="font-semibold">Relegation Zone</span>
          </div>
          <p className="text-sm text-slate-400">Positions 18-20</p>
        </div>
      </div>
    </div>
  );
}
