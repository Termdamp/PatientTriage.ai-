import { cn } from '@/lib/utils';
import { Priority } from '@/types';

const PRIORITY_STYLES: Record<Priority, string> = {
  CRITICAL: 'bg-red-100 text-red-700 border border-red-300 font-bold',
  HIGH: 'bg-orange-100 text-orange-700 border border-orange-300 font-bold',
  MODERATE: 'bg-amber-100 text-amber-700 border border-amber-300 font-semibold',
  LOW: 'bg-green-100 text-green-700 border border-green-300 font-semibold',
};

const PRIORITY_DOTS: Record<Priority, string> = {
  CRITICAL: 'bg-red-500',
  HIGH: 'bg-orange-500',
  MODERATE: 'bg-amber-500',
  LOW: 'bg-green-500',
};

interface PriorityBadgeProps {
  priority: Priority;
  size?: 'sm' | 'md' | 'lg';
  showDot?: boolean;
}

export function PriorityBadge({ priority, size = 'md', showDot = true }: PriorityBadgeProps) {
  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-xs px-2 py-1',
    lg: 'text-sm px-3 py-1.5',
  };

  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded', PRIORITY_STYLES[priority], sizeClasses[size])}>
      {showDot && <span className={cn('h-1.5 w-1.5 rounded-full flex-shrink-0', PRIORITY_DOTS[priority])} />}
      {priority}
    </span>
  );
}
