import { Alert } from '@/types';
import { AlertTriangle, Bell, Wifi, CheckCircle, TrendingDown, Clock } from 'lucide-react';
import { formatDateTimeFull } from '@/lib/formatters';
import { cn } from '@/lib/utils';

const ALERT_ICON: Record<string, React.ElementType> = {
  DETERIORATION: TrendingDown,
  WAITING_BREACH: Clock,
  CAPACITY: AlertTriangle,
  SYSTEM: Bell,
};

const SEVERITY_STYLES: Record<string, string> = {
  CRITICAL: 'border-l-red-500 bg-red-50',
  WARNING: 'border-l-amber-500 bg-amber-50',
  INFO: 'border-l-blue-500 bg-blue-50',
};

const SEVERITY_ICON_COLOR: Record<string, string> = {
  CRITICAL: 'text-red-600',
  WARNING: 'text-amber-600',
  INFO: 'text-blue-600',
};

interface AlertCardProps {
  alert: Alert;
  onAcknowledge?: (id: string) => void;
}

export function AlertCard({ alert, onAcknowledge }: AlertCardProps) {
  const Icon = ALERT_ICON[alert.type] || Bell;

  return (
    <div className={cn(
      'border-l-4 border border-slate-200 rounded-r p-3',
      SEVERITY_STYLES[alert.severity],
      alert.acknowledged && 'opacity-60'
    )}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-2 flex-1 min-w-0">
          <Icon className={cn('h-4 w-4 mt-0.5 flex-shrink-0', SEVERITY_ICON_COLOR[alert.severity])} />
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={cn('text-xs font-bold', SEVERITY_ICON_COLOR[alert.severity])}>
                {alert.severity}
              </span>
              <span className="text-xs text-slate-500">{alert.type.replace('_', ' ')}</span>
              {alert.patientId && (
                <span className="text-xs font-mono text-slate-600">{alert.patientId}</span>
              )}
            </div>
            <p className="text-xs text-slate-700 mt-0.5 leading-relaxed">{alert.message}</p>
            <p className="text-xs text-slate-400 mt-1">{formatDateTimeFull(alert.createdAt)}</p>
          </div>
        </div>

        {!alert.acknowledged && onAcknowledge && (
          <button
            onClick={() => onAcknowledge(alert.id)}
            className="flex-shrink-0 flex items-center gap-1 text-xs text-slate-500 hover:text-green-600 border border-slate-200 hover:border-green-300 rounded px-2 py-1 transition-colors"
          >
            <CheckCircle className="h-3 w-3" /> Ack
          </button>
        )}
      </div>
    </div>
  );
}
