import React from 'react';
import { PREDICTION_RESULTS } from '../utils/constants';

interface ProbabilityBarProps {
  homeWin: number;
  draw: number;
  awayWin: number;
  homeTeam: string;
  awayTeam: string;
  compact?: boolean;
}

export default function ProbabilityBar({
  homeWin,
  draw,
  awayWin,
  homeTeam,
  awayTeam,
  compact = false,
}: ProbabilityBarProps) {
  const total = homeWin + draw + awayWin;
  const homePercent = (homeWin / total) * 100;
  const drawPercent = (draw / total) * 100;
  const awayPercent = (awayWin / total) * 100;

  if (compact) {
    return (
      <div className="space-y-2">
        <div className="flex gap-2">
          <div className="flex-1">
            <div className="text-xs font-semibold mb-1 text-center">{homeTeam}</div>
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-green-500 to-emerald-500"
                style={{ width: `${homePercent}%` }}
              />
            </div>
            <div className="text-xs text-center mt-1">{(homeWin * 100).toFixed(0)}%</div>
          </div>
          <div className="flex-1">
            <div className="text-xs font-semibold mb-1 text-center">Draw</div>
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-yellow-500 to-amber-500"
                style={{ width: `${drawPercent}%` }}
              />
            </div>
            <div className="text-xs text-center mt-1">{(draw * 100).toFixed(0)}%</div>
          </div>
          <div className="flex-1">
            <div className="text-xs font-semibold mb-1 text-center">{awayTeam}</div>
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-red-500 to-rose-500"
                style={{ width: `${awayPercent}%` }}
              />
            </div>
            <div className="text-xs text-center mt-1">{(awayWin * 100).toFixed(0)}%</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <div className="flex justify-between items-center mb-2">
          <span className="font-semibold">{homeTeam} Win</span>
          <span className="text-lg font-bold text-green-400">{(homeWin * 100).toFixed(1)}%</span>
        </div>
        <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-green-500 to-emerald-500 transition-all duration-300"
            style={{ width: `${homePercent}%` }}
          />
        </div>
      </div>

      <div>
        <div className="flex justify-between items-center mb-2">
          <span className="font-semibold">Draw</span>
          <span className="text-lg font-bold text-yellow-400">{(draw * 100).toFixed(1)}%</span>
        </div>
        <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-yellow-500 to-amber-500 transition-all duration-300"
            style={{ width: `${drawPercent}%` }}
          />
        </div>
      </div>

      <div>
        <div className="flex justify-between items-center mb-2">
          <span className="font-semibold">{awayTeam} Win</span>
          <span className="text-lg font-bold text-red-400">{(awayWin * 100).toFixed(1)}%</span>
        </div>
        <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-red-500 to-rose-500 transition-all duration-300"
            style={{ width: `${awayPercent}%` }}
          />
        </div>
      </div>
    </div>
  );
}
