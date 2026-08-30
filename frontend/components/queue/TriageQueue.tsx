'use client';
import { QueueResponse } from '@/types';
import { QueueItem } from './QueueItem';
import { RefreshCw } from 'lucide-react';

interface TriageQueueProps {
  data: QueueResponse | null;
  loading?: boolean;
  onRefresh?: () => void;
  maxItems?: number;
}

export function TriageQueue({ data, loading, onRefresh, maxItems }: TriageQueueProps) {
  const patients = maxItems ? data?.patients.slice(0, maxItems) : data?.patients;

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">Dynamic Triage Queue</h2>
          {data && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold text-red-700 bg-red-100 px-1.5 py-0.5 rounded">{data.criticalCount} Critical</span>
              <span className="text-xs font-bold text-orange-700 bg-orange-100 px-1.5 py-0.5 rounded">{data.highCount} High</span>
            </div>
          )}
        </div>
        {onRefresh && (
          <button onClick={onRefresh} className="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1">
            <RefreshCw className="h-3 w-3" /> Refresh
          </button>
        )}
      </div>

      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-16 bg-slate-100 rounded animate-pulse" />
          ))}
        </div>
      ) : patients && patients.length > 0 ? (
        <div className="space-y-2">
          {patients.map((patient, idx) => (
            <QueueItem key={patient.id} patient={patient} rank={idx + 1} />
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-slate-400 text-sm border border-dashed border-slate-200 rounded">
          No patients in queue
        </div>
      )}
    </div>
  );
}
