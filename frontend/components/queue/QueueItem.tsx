import { QueuePatient } from '@/types';
import { PriorityBadge } from './PriorityBadge';
import { WaitTimeBadge } from './WaitTimeBadge';
import { AlertTriangle, TrendingDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import Link from 'next/link';

interface QueueItemProps {
  patient: QueuePatient;
  rank: number;
}

const PRIORITY_BORDER: Record<string, string> = {
  CRITICAL: 'border-l-red-500 bg-red-50/30',
  HIGH: 'border-l-orange-500 bg-orange-50/20',
  MODERATE: 'border-l-amber-500',
  LOW: 'border-l-green-500',
};

export function QueueItem({ patient, rank }: QueueItemProps) {
  return (
    <Link href={`/patients/${patient.id}`}>
      <div className={cn(
        'border-l-4 border border-slate-200 rounded-r p-3 hover:shadow-md transition-shadow cursor-pointer',
        PRIORITY_BORDER[patient.priority]
      )}>
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-xs font-bold text-slate-400 w-5 flex-shrink-0">#{rank}</span>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-slate-800 text-sm">{patient.name}</span>
                <span className="text-xs text-slate-400">{patient.id}</span>
                {patient.deteriorating && (
                  <span className="inline-flex items-center gap-1 text-xs font-bold text-red-600 bg-red-50 border border-red-200 px-1.5 py-0.5 rounded">
                    <TrendingDown className="h-3 w-3" /> DETERIORATING
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {patient.age}y • {patient.gender} • {patient.chiefComplaint}
              </p>
            </div>
          </div>
          <PriorityBadge priority={patient.priority} />
        </div>

        <div className="flex items-center gap-4 mt-2 pl-7">
          <span className="text-xs text-slate-600">
            Risk <span className="font-semibold">{Math.round(patient.riskScore)}</span>
          </span>
          <span className="text-xs text-slate-600">
            Confidence <span className="font-semibold">{Math.round(patient.confidence * 100)}%</span>
          </span>
          <WaitTimeBadge minutes={patient.waitMinutes} />
          {patient.safetyFlags.length > 0 && (
            <span className="flex items-center gap-1 text-xs text-red-600">
              <AlertTriangle className="h-3 w-3" />
              {patient.safetyFlags.length} safety flag{patient.safetyFlags.length > 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
