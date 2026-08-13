import React from 'react';
import { AlertCircle, Loader } from 'lucide-react';

interface LoadingProps {
  message?: string;
}

export function LoadingSpinner({ message = 'Loading...' }: LoadingProps) {
  return (
    <div className="flex flex-col items-center justify-center py-24">
      <div className="w-12 h-12 rounded-full border-4 border-slate-700 border-t-blue-500 animate-spin mb-4" />
      <p className="text-slate-400">{message}</p>
    </div>
  );
}

interface ErrorProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ title = 'Error', message, onRetry }: ErrorProps) {
  return (
    <div className="flex flex-col items-center justify-center py-24">
      <AlertCircle className="w-16 h-16 text-red-500 mb-4" />
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-slate-400 text-center max-w-md mb-6">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-lg transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  );
}

interface EmptyStateProps {
  title?: string;
  message: string;
  icon?: React.ReactNode;
}

export function EmptyState({
  title = 'No Data',
  message,
  icon,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-24">
      <div className="text-6xl mb-4">{icon || '📭'}</div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-slate-400 text-center max-w-md">{message}</p>
    </div>
  );
}

interface SkeletonProps {
  className?: string;
}

export function SkeletonCard({ className = '' }: SkeletonProps) {
  return (
    <div className={`p-6 rounded-xl bg-slate-800/50 border border-slate-700/50 ${className}`}>
      <div className="space-y-4">
        <div className="h-4 bg-slate-700 rounded w-3/4 animate-pulse" />
        <div className="h-8 bg-slate-700 rounded w-1/2 animate-pulse" />
        <div className="space-y-2">
          <div className="h-3 bg-slate-700 rounded animate-pulse" />
          <div className="h-3 bg-slate-700 rounded w-5/6 animate-pulse" />
        </div>
      </div>
    </div>
  );
}
