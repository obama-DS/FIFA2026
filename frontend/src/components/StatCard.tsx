import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { getFormColor } from '../utils/helpers';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  gradient: string;
  subtext?: string;
  trend?: 'up' | 'down' | null;
  trendValue?: string;
}

export default function StatCard({
  label,
  value,
  icon,
  gradient,
  subtext,
  trend,
  trendValue,
}: StatCardProps) {
  return (
    <div className="p-6 rounded-xl bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm hover:border-slate-600 transition-all group">
      <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${gradient} p-3 mb-4 group-hover:scale-110 transition-transform flex items-center justify-center`}>
        {typeof icon === 'string' ? <span className="text-xl">{icon}</span> : icon}
      </div>
      <div className="text-sm opacity-70 mb-2">{label}</div>
      <div className="text-3xl font-bold mb-2">{value}</div>
      {subtext && <div className="text-xs text-slate-400">{subtext}</div>}
      {trend && trendValue && (
        <div className={`mt-3 flex items-center gap-1 ${trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
          {trend === 'up' ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
          <span className="text-sm font-semibold">{trendValue}</span>
        </div>
      )}
    </div>
  );
}
