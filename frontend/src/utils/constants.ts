// Premier League team names and colors
export const PREMIER_LEAGUE_TEAMS = [
  'Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton',
  'Chelsea', 'Crystal Palace', 'Everton', 'Fulham', 'Ipswich Town',
  'Leicester City', 'Liverpool', 'Manchester City', 'Manchester United',
  'Newcastle United', 'Nottingham Forest', 'Southampton', 'Tottenham',
  'West Ham United', 'Wolverhampton Wanderers'
];

export const TEAM_COLORS: { [key: string]: string } = {
  'Arsenal': '#EF0107',
  'Aston Villa': '#95BFE5',
  'Bournemouth': '#DA291C',
  'Brentford': '#B30E0E',
  'Brighton': '#0087DC',
  'Chelsea': '#0051BA',
  'Crystal Palace': '#1B50BE',
  'Everton': '#003DA5',
  'Fulham': '#000000',
  'Ipswich Town': '#0053A0',
  'Leicester City': '#0053B8',
  'Liverpool': '#C8102E',
  'Manchester City': '#6CABDA',
  'Manchester United': '#DA291C',
  'Newcastle United': '#241F20',
  'Nottingham Forest': '#DD0000',
  'Southampton': '#005EB8',
  'Tottenham': '#132257',
  'West Ham United': '#122F67',
  'Wolverhampton Wanderers': '#FDB913',
};

export const TEAM_BADGES: { [key: string]: string } = {
  'Arsenal': '🔴',
  'Aston Villa': '🔵',
  'Bournemouth': '🔴',
  'Brentford': '⚪',
  'Brighton': '⚪',
  'Chelsea': '🔵',
  'Crystal Palace': '🔵',
  'Everton': '🔵',
  'Fulham': '⚫',
  'Ipswich Town': '🔵',
  'Leicester City': '🔵',
  'Liverpool': '🔴',
  'Manchester City': '🔵',
  'Manchester United': '🔴',
  'Newcastle United': '⚫',
  'Nottingham Forest': '🔴',
  'Southampton': '🔴',
  'Tottenham': '⚪',
  'West Ham United': '🔵',
  'Wolverhampton Wanderers': '🟡',
};

export const PREDICTION_RESULTS = {
  'H': { label: 'Home Win', color: 'from-green-500 to-emerald-500', bg: 'bg-green-500/20' },
  'D': { label: 'Draw', color: 'from-yellow-500 to-amber-500', bg: 'bg-yellow-500/20' },
  'A': { label: 'Away Win', color: 'from-red-500 to-rose-500', bg: 'bg-red-500/20' },
};

export const GAMEWEEK_DEADLINE_DAY = 5; // Friday
export const GAMEWEEK_DEADLINE_HOUR = 11; // 11:00 AM

// Chart color schemes
export const CHART_COLORS = {
  primary: '#3b82f6',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#06b6d4',
};
