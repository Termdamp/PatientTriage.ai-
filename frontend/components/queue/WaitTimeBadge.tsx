import { Clock, AlertTriangle } from 'lucide-react';
import { formatWaitTime } from '@/lib/formatters';
import { cn } from '@/lib/utils';

interface WaitTimeBadgeProps {
  minutes: number;
  breach?: boolean;
  className?: string;
}

export function WaitTimeBadge({ minutes, breach, className }: WaitTimeBadgeProps) {
  if (breach) {
    return (
      <span className={cn('inline-flex items-center gap-1 text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-300 px-2 py-0.5 rounded', className)}>
        <AlertTriangle className="h-3 w-3" />
        WAITING BREACH — {formatWaitTime(minutes)}
      </span>
    );
  }
  return (
    <span className={cn('inline-flex items-center gap-1 text-xs text-slate-500', className)}>
      <Clock className="h-3 w-3" />
      {formatWaitTime(minutes)}
    </span>
  );
}
