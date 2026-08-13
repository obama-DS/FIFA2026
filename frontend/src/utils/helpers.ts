// Utility functions for common operations
import { GAMEWEEK_DEADLINE_DAY, GAMEWEEK_DEADLINE_HOUR } from './constants';

export const calculateDeadlineCountdown = (): {
  days: number;
  hours: number;
  minutes: number;
  total_seconds: number;
  is_locked: boolean;
} => {
  const now = new Date();
  const dayOfWeek = now.getDay();
  const daysUntilDeadline = (GAMEWEEK_DEADLINE_DAY - dayOfWeek + 7) % 7 || 7;

  const deadline = new Date(now);
  deadline.setDate(deadline.getDate() + daysUntilDeadline);
  deadline.setHours(GAMEWEEK_DEADLINE_HOUR, 0, 0, 0);

  const diff = deadline.getTime() - now.getTime();
  const is_locked = diff <= 0;

  const days = Math.max(0, Math.floor(diff / (1000 * 60 * 60 * 24)));
  const hours = Math.max(0, Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)));
  const minutes = Math.max(0, Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)));
  const total_seconds = Math.max(0, Math.floor(diff / 1000));

  return { days, hours, minutes, total_seconds, is_locked };
};

export const formatCountdown = (countdown: ReturnType<typeof calculateDeadlineCountdown>): string => {
  if (countdown.is_locked) return 'LOCKED';
  return `${countdown.days}d ${countdown.hours}h ${countdown.minutes}m`;
};

export const getWinProbability = (
  home_confidence: number,
  draw_confidence: number,
  away_confidence: number,
  result: 'H' | 'D' | 'A'
): number => {
  switch (result) {
    case 'H':
      return home_confidence;
    case 'D':
      return draw_confidence;
    case 'A':
      return away_confidence;
    default:
      return 0;
  }
};

export const formatProbability = (prob: number): string => {
  return `${(prob * 100).toFixed(0)}%`;
};

export const formatGoals = (goals: number): string => {
  return goals.toFixed(2);
};

export const predictResult = (home_goals: number, away_goals: number): 'H' | 'D' | 'A' => {
  const diff = home_goals - away_goals;
  if (diff > 0.5) return 'H';
  if (diff < -0.5) return 'A';
  return 'D';
};

export const calculateForm = (goalsFor: number, goalsAgainst: number, matches: number): number => {
  if (matches === 0) return 0;
  return parseFloat(((goalsFor - goalsAgainst) / matches).toFixed(2));
};

export const getFormColor = (form: number): string => {
  if (form > 0.5) return 'text-green-400';
  if (form > 0) return 'text-yellow-400';
  return 'text-red-400';
};

export const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
};

export const searchFilter = (items: any[], query: string, fields: string[]): any[] => {
  if (!query.trim()) return items;
  const lowerQuery = query.toLowerCase();
  return items.filter((item) =>
    fields.some((field) =>
      String(item[field]).toLowerCase().includes(lowerQuery)
    )
  );
};
