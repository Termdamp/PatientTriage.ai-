'use client';
import { useAudit } from '@/hooks/useAudit';
import { formatDateTimeFull } from '@/lib/formatters';
import { EVENT_TYPE_LABELS } from '@/lib/constants';
import { cn } from '@/lib/utils';

const EVENT_COLORS: Record<string, string> = {
  PATIENT_CREATED: 'bg-blue-400',
  TRIAGE_COMPLETED: 'bg-green-400',
  ASSESSMENT_UPDATED: 'bg-blue-500',
  DETERIORATION_DETECTED: 'bg-red-500',
  ALERT_CREATED: 'bg-red-400',
  CLINICIAN_REVIEWED: 'bg-purple-400',
  CLINICIAN_OVERRIDE: 'bg-orange-500',
  CAPACITY_UPDATED: 'bg-amber-400',
  SURGE_STARTED: 'bg-amber-500',
};

export default function AuditPage() {
  const { data, loading } = useAudit();

  return (
    <div className="p-6">
      <div className="mb-5">
        <h1 className="text-lg font-bold text-slate-800">Audit Trail</h1>
        <p className="text-xs text-slate-400">Chronological record of all system events</p>
      </div>

      <div className="max-w-2xl">
        {loading ? (
          <div className="space-y-4">
            {[1,2,3,4].map(i => <div key={i} className="h-14 bg-slate-100 rounded animate-pulse" />)}
          </div>
        ) : data && data.events.length > 0 ? (
          <div className="space-y-0">
            {data.events.map((event, i) => (
              <div key={event.id} className="flex items-start gap-3">
                <div className="flex flex-col items-center">
                  <div className={cn('h-3 w-3 rounded-full flex-shrink-0 mt-1', EVENT_COLORS[event.eventType] || 'bg-slate-400')} />
                  {i < data.events.length - 1 && <div className="w-px flex-1 bg-slate-200 my-1 min-h-4" />}
                </div>
                <div className="pb-4 flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-semibold text-slate-700">
                      {EVENT_TYPE_LABELS[event.eventType] || event.eventType}
                    </span>
                    {event.patientId && (
                      <span className="text-xs font-mono text-blue-600">{event.patientId}</span>
                    )}
                    <span className="text-xs text-slate-400">{event.actor}</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-0.5">{event.description}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{formatDateTimeFull(event.createdAt)}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-slate-400 text-sm border border-dashed border-slate-200 rounded">
            No audit events found
          </div>
        )}
      </div>
    </div>
  );
}
