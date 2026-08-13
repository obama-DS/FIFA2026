import React from 'react';
import { PREDICTION_RESULTS, TEAM_BADGES } from '../utils/constants';

interface MatchHeaderProps {
  homeTeam: string;
  awayTeam: string;
  homeGoals: number;
  awayGoals: number;
  result: 'H' | 'D' | 'A';
  status?: 'scheduled' | 'live' | 'completed';
  kickoffTime?: string;
  gameweek?: number;
}

export default function MatchHeader({
  homeTeam,
  awayTeam,
  homeGoals,
  awayGoals,
  result,
  status = 'scheduled',
  kickoffTime,
  gameweek,
}: MatchHeaderProps) {
  const resultConfig = PREDICTION_RESULTS[result];
  const homeBadge = TEAM_BADGES[homeTeam] || '⚽';
  const awayBadge = TEAM_BADGES[awayTeam] || '⚽';

  const statusColor =
    status === 'completed'
      ? 'bg-slate-600'
      : status === 'live'
      ? 'bg-red-500/20 text-red-400'
      : 'bg-blue-500/20 text-blue-400';

  const statusLabel =
    status === 'completed' ? 'Final' : status === 'live' ? '🔴 LIVE' : 'Scheduled';

  return (
    <div className="space-y-3">
      {gameweek && (
        <div className="text-sm opacity-70">Gameweek {gameweek}</div>
      )}
      {kickoffTime && (
        <div className="text-sm text-slate-400">
          Kickoff: {new Date(kickoffTime).toLocaleString()}
        </div>
      )}

      <div className="flex items-center justify-between gap-4">
        {/* Home Team */}
        <div className="flex-1 text-right">
          <div className="text-2xl font-bold mb-1">{homeTeam}</div>
          <div className="text-3xl">{homeBadge}</div>
        </div>

        {/* Score and Result */}
        <div className="text-center space-y-2">
          <div className={`text-4xl font-black bg-gradient-to-r ${resultConfig.color} bg-clip-text text-transparent`}>
            {homeGoals.toFixed(1)} - {awayGoals.toFixed(1)}
          </div>
          <div className={`text-xs px-3 py-1 rounded-full bg-gradient-to-r ${resultConfig.color} text-white font-semibold w-fit mx-auto`}>
            {resultConfig.label}
          </div>
          <div className={`text-xs px-2 py-1 rounded font-semibold ${statusColor}`}>
            {statusLabel}
          </div>
        </div>

        {/* Away Team */}
        <div className="flex-1 text-left">
          <div className="text-2xl font-bold mb-1">{awayTeam}</div>
          <div className="text-3xl">{awayBadge}</div>
        </div>
      </div>
    </div>
  );
}
