'use client';
import { useAlerts } from '@/hooks/useAlerts';
import { AlertCard } from '@/components/alerts/AlertCard';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useCallback } from 'react';

export default function AlertsPage() {
  const { data, loading, refetch, acknowledge } = useAlerts();

  const handleMessage = useCallback((msg: { event: string }) => {
    if (['ALERT_CREATED', 'DETERIORATION'].includes(msg.event)) refetch();
  }, [refetch]);
  useWebSocket(handleMessage);

  const alerts = data?.alerts || [];
  const unacknowledged = alerts.filter(a => !a.acknowledged);
  const acknowledged = alerts.filter(a => a.acknowledged);

  return (
    <div className="p-6">
      <div className="mb-5">
        <h1 className="text-lg font-bold text-slate-800">Active Alerts</h1>
        <p className="text-xs text-slate-400">{data?.unacknowledgedCount ?? 0} unacknowledged alerts</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h2 className="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-3">Unacknowledged</h2>
          {loading ? (
            <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-16 bg-slate-100 rounded animate-pulse" />)}</div>
          ) : unacknowledged.length > 0 ? (
            <div className="space-y-2">
              {unacknowledged.map(a => <AlertCard key={a.id} alert={a} onAcknowledge={acknowledge} />)}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-400 text-sm border border-dashed border-slate-200 rounded">
              No active alerts
            </div>
          )}
        </div>
        <div>
          <h2 className="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-3">Acknowledged</h2>
          {acknowledged.length > 0 ? (
            <div className="space-y-2">
              {acknowledged.slice(0, 10).map(a => <AlertCard key={a.id} alert={a} />)}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-400 text-sm border border-dashed border-slate-200 rounded">
              No acknowledged alerts
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
