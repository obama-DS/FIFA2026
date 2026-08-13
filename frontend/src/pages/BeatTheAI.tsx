import React, { useState, useEffect } from 'react';
import { Trophy, Clock, Lock, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';

interface Fixture {
  id: number;
  home_team: string;
  away_team: string;
  kickoff: string;
  status: 'upcoming' | 'live' | 'completed';
  actual_result?: 'H' | 'D' | 'A';
  actual_score?: {
    home: number;
    away: number;
  };
}

interface UserPrediction {
  fixture_id: number;
  home_team: string;
  away_team: string;
  predicted_score: {
    home: number;
    away: number;
  };
  points: number | null;
  locked: boolean;
}

const GAMEWEEK_FIXTURES: Fixture[] = [
  {
    id: 1,
    home_team: 'Arsenal',
    away_team: 'Chelsea',
    kickoff: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
    status: 'upcoming',
  },
  {
    id: 2,
    home_team: 'Manchester United',
    away_team: 'Liverpool',
    kickoff: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
    status: 'upcoming',
  },
  {
    id: 3,
    home_team: 'Manchester City',
    away_team: 'Tottenham',
    kickoff: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
    status: 'upcoming',
  },
  {
    id: 4,
    home_team: 'Brighton',
    away_team: 'Newcastle',
    kickoff: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
    status: 'upcoming',
  },
];

const SAMPLE_LEADERBOARD = [
  { rank: 1, username: 'AlexPredicts', points: 487, gameweeks: 5, accuracy: '72%', badge: '🥇' },
  { rank: 2, username: 'FootballPro', points: 465, gameweeks: 5, accuracy: '68%', badge: '🥈' },
  { rank: 3, username: 'MatchMaster', points: 451, gameweeks: 5, accuracy: '65%', badge: '🥉' },
  { rank: 4, username: 'PredictionKing', points: 438, gameweeks: 5, accuracy: '62%', badge: '⭐' },
  { rank: 5, username: 'DataNerd', points: 425, gameweeks: 5, accuracy: '61%', badge: '⭐' },
];

interface FixtureCardProps {
  fixture: Fixture;
  prediction: UserPrediction | undefined;
  onPredictionChange: (fixture_id: number, home: number, away: number) => void;
  isDeadlinePassed: boolean;
}

function FixtureCard({ fixture, prediction, onPredictionChange, isDeadlinePassed }: FixtureCardProps) {
  const isAfterDeadline = new Date(fixture.kickoff) <= new Date();
  const isLocked = isAfterDeadline || isDeadlinePassed;

  const statusColor = 
    fixture.status === 'upcoming' ? 'text-blue-400' :
    fixture.status === 'live' ? 'text-red-400' :
    'text-slate-400';

  const statusLabel = 
    fixture.status === 'upcoming' ? '⏳ Upcoming' :
    fixture.status === 'live' ? '🔴 Live' :
    '✅ Completed';

  return (
    <div className={`p-6 rounded-xl border transition-all ${
      isLocked
        ? 'bg-slate-900/30 border-slate-700/30 opacity-75'
        : 'bg-slate-800/50 border-slate-700/50 hover:border-slate-600'
    }`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className={`text-xs font-semibold mb-2 ${statusColor}`}>
            {statusLabel}
          </div>
          <div className="text-sm text-slate-400">
            {new Date(fixture.kickoff).toLocaleString()}
          </div>
        </div>
        {isLocked && (
          <div className="flex items-center gap-1 text-xs text-slate-500">
            <Lock size={14} /> Locked
          </div>
        )}
      </div>

      {/* Match Info */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <span className="font-bold flex-1">{fixture.home_team}</span>
          <span className="text-center text-sm text-slate-400">vs</span>
          <span className="font-bold flex-1 text-right">{fixture.away_team}</span>
        </div>
      </div>

      {/* Prediction Input */}
      {!isLocked && !fixture.actual_result ? (
        <div className="flex gap-2">
          <div className="flex-1">
            <input
              type="number"
              min="0"
              max="9"
              value={prediction?.predicted_score.home || ''}
              onChange={(e) => onPredictionChange(fixture.id, parseInt(e.target.value) || 0, prediction?.predicted_score.away || 0)}
              placeholder="0"
              className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-center font-bold text-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              disabled={isLocked}
            />
          </div>
          <div className="flex-1">
            <input
              type="number"
              min="0"
              max="9"
              value={prediction?.predicted_score.away || ''}
              onChange={(e) => onPredictionChange(fixture.id, prediction?.predicted_score.home || 0, parseInt(e.target.value) || 0)}
              placeholder="0"
              className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-center font-bold text-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              disabled={isLocked}
            />
          </div>
        </div>
      ) : fixture.actual_result ? (
        <div className="bg-slate-900/50 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-white mb-2">
            {fixture.actual_score?.home} - {fixture.actual_score?.away}
          </div>
          <div className="text-xs text-slate-400">Final Result</div>
          {prediction && (
            <div className="mt-3 text-sm">
              <div className={prediction.points === 3 ? 'text-green-400' : 'text-slate-400'}>
                Your prediction: {prediction.predicted_score.home} - {prediction.predicted_score.away}
              </div>
              {prediction.points !== null && (
                <div className={`mt-1 font-bold ${prediction.points === 3 ? 'text-green-400' : prediction.points === 1 ? 'text-yellow-400' : 'text-red-400'}`}>
                  {prediction.points} points
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="text-sm text-slate-400 text-center py-2">
          Awaiting actual result...
        </div>
      )}

      {/* Info Text */}
      {!isLocked && (
        <div className="mt-4 text-xs text-slate-500">
          Deadline: {new Date(fixture.kickoff).toLocaleString()}
        </div>
      )}
    </div>
  );
}

export default function BeatTheAI() {
  const [currentGameweek, setCurrentGameweek] = useState(1);
  const [predictions, setPredictions] = useState<UserPrediction[]>([]);
  const [gameweekPoints, setGameweekPoints] = useState(0);
  const [seasonPoints, setSeasonPoints] = useState(385); // Cumulative from previous gameweeks
  const [submitted, setSubmitted] = useState(false);
  const [deadline, setDeadline] = useState<string>('');

  useEffect(() => {
    // Calculate deadline (Friday 11:00 AM)
    const now = new Date();
    const dayOfWeek = now.getDay();
    const daysUntilFriday = (5 - dayOfWeek + 7) % 7 || 7;
    
    const deadlineDate = new Date(now);
    deadlineDate.setDate(deadlineDate.getDate() + daysUntilFriday);
    deadlineDate.setHours(11, 0, 0, 0);
    
    setDeadline(deadlineDate.toISOString());
  }, []);

  const isDeadlinePassed = new Date() > new Date(deadline);

  const handlePredictionChange = (fixture_id: number, home: number, away: number) => {
    setPredictions(prev => {
      const existing = prev.find(p => p.fixture_id === fixture_id);
      if (existing) {
        return prev.map(p => p.fixture_id === fixture_id
          ? { ...p, predicted_score: { home, away } }
          : p
        );
      } else {
        const fixture = GAMEWEEK_FIXTURES.find(f => f.id === fixture_id);
        if (!fixture) return prev;
        return [...prev, {
          fixture_id,
          home_team: fixture.home_team,
          away_team: fixture.away_team,
          predicted_score: { home, away },
          points: null,
          locked: false,
        }];
      }
    });
  };

  const handleSubmit = () => {
    if (predictions.length === 0) {
      alert('Please make at least one prediction');
      return;
    }
    
    // Calculate points (mock scoring)
    const newPredictions = predictions.map(p => ({
      ...p,
      points: Math.floor(Math.random() * 4), // 0-3 points per fixture
      locked: true,
    }));
    
    const totalPoints = newPredictions.reduce((sum, p) => sum + (p.points || 0), 0);
    setGameweekPoints(totalPoints);
    setPredictions(newPredictions);
    setSubmitted(true);
  };

  const timeRemaining = deadline ? new Date(deadline).getTime() - new Date().getTime() : 0;
  const days = Math.floor(timeRemaining / (1000 * 60 * 60 * 24));
  const hours = Math.floor((timeRemaining % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((timeRemaining % (1000 * 60 * 60)) / (1000 * 60));

  return (
    <div className="min-h-screen py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-12">
        <h1 className="text-4xl sm:text-5xl font-bold mb-4 flex items-center gap-3">
          <Trophy className="text-yellow-400" size={40} />
          Beat the AI
        </h1>
        <p className="text-lg text-slate-400 max-w-2xl">
          Make your predictions for Gameweek {currentGameweek} and compete on the leaderboard.
        </p>
      </div>

      {/* Deadline Banner */}
      <div className="mb-8 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 border border-yellow-500/50 rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Clock className="text-yellow-400" size={24} />
            <div>
              <div className="font-bold text-lg">Deadline Countdown</div>
              <div className="text-sm text-slate-400">Gameweek {currentGameweek} closes at</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-yellow-400">
              {days}d {hours}h {minutes}m
            </div>
            <div className="text-xs text-slate-400">
              {new Date(deadline).toLocaleString()}
            </div>
          </div>
        </div>

        {isDeadlinePassed && (
          <div className="mt-4 flex items-center gap-2 text-red-400">
            <AlertCircle size={18} />
            <span className="font-semibold">Predictions locked - deadline has passed</span>
          </div>
        )}
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
          <div className="text-sm opacity-70 mb-2">Gameweek Points</div>
          <div className="text-4xl font-bold text-blue-400">{gameweekPoints}</div>
          <div className="text-xs text-slate-400 mt-2">This gameweek</div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
          <div className="text-sm opacity-70 mb-2">Season Total</div>
          <div className="text-4xl font-bold text-purple-400">{seasonPoints + gameweekPoints}</div>
          <div className="text-xs text-slate-400 mt-2">Overall points</div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
          <div className="text-sm opacity-70 mb-2">Predictions Made</div>
          <div className="text-4xl font-bold text-green-400">{predictions.length}</div>
          <div className="text-xs text-slate-400 mt-2">Of {GAMEWEEK_FIXTURES.length} fixtures</div>
        </div>
      </div>

      {/* Submitted State */}
      {submitted && (
        <div className="mb-8 bg-green-500/10 border border-green-500/50 rounded-xl p-6 flex items-center gap-3">
          <CheckCircle className="text-green-400" size={24} />
          <div>
            <div className="font-bold">Predictions Submitted!</div>
            <div className="text-sm text-slate-400">
              Earned <strong>{gameweekPoints} points</strong> this gameweek. Check back after matches for final results.
            </div>
          </div>
        </div>
      )}

      {/* Fixtures */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
        {GAMEWEEK_FIXTURES.map(fixture => (
          <FixtureCard
            key={fixture.id}
            fixture={fixture}
            prediction={predictions.find(p => p.fixture_id === fixture.id)}
            onPredictionChange={handlePredictionChange}
            isDeadlinePassed={isDeadlinePassed}
          />
        ))}
      </div>

      {/* Submit Button */}
      {!isDeadlinePassed && !submitted && (
        <div className="flex gap-4 mb-16">
          <button
            onClick={handleSubmit}
            disabled={predictions.length === 0}
            className="flex-1 btn-primary text-lg py-4 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Submit Predictions
          </button>
          <button
            onClick={() => setPredictions([])}
            className="btn-secondary py-4"
          >
            Clear All
          </button>
        </div>
      )}

      {/* Leaderboard */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden">
        <div className="p-6 bg-slate-900/50 border-b border-slate-700/50">
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Trophy size={28} className="text-yellow-400" />
            Global Leaderboard
          </h2>
          <p className="text-sm text-slate-400 mt-2">Top performers this season</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-900/30 border-b border-slate-700/50">
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-400">Rank</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-400">Username</th>
                <th className="px-6 py-4 text-center text-sm font-semibold text-slate-400">Points</th>
                <th className="px-6 py-4 text-center text-sm font-semibold text-slate-400">Gameweeks</th>
                <th className="px-6 py-4 text-center text-sm font-semibold text-slate-400">Accuracy</th>
              </tr>
            </thead>
            <tbody>
              {SAMPLE_LEADERBOARD.map((entry) => (
                <tr key={entry.rank} className="border-b border-slate-700/50 hover:bg-slate-800/30 transition-colors">
                  <td className="px-6 py-4">
                    <span className="text-2xl">{entry.badge}</span>
                  </td>
                  <td className="px-6 py-4 font-semibold">{entry.username}</td>
                  <td className="px-6 py-4 text-center font-bold text-blue-400">{entry.points}</td>
                  <td className="px-6 py-4 text-center">{entry.gameweeks}</td>
                  <td className="px-6 py-4 text-center font-semibold text-green-400">{entry.accuracy}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
