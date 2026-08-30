'use client';
import { useQueue } from '@/hooks/useQueue';
import { useAlerts } from '@/hooks/useAlerts';
import { useCapacity } from '@/hooks/useCapacity';
import { useWebSocket } from '@/hooks/useWebSocket';
import { TriageQueue } from '@/components/queue/TriageQueue';
import { AlertCard } from '@/components/alerts/AlertCard';
import { PriorityBadge } from '@/components/queue/PriorityBadge';
import { formatWaitTime, formatCapacityPercent } from '@/lib/formatters';
import { Users, AlertTriangle, TrendingUp, Clock, BedDouble, TrendingDown, RefreshCw, Zap } from 'lucide-react';
import { useCallback, useState } from 'react';
import { api } from '@/lib/api';
import Link from 'next/link';
import { cn } from '@/lib/utils';

function StatCard({ label, value, sub, icon: Icon, color = 'blue' }: {
  label: string; value: string | number; sub?: string;
  icon: React.ElementType; color?: string;
}) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600',
    red: 'bg-red-50 text-red-600',
    orange: 'bg-orange-50 text-orange-600',
    green: 'bg-green-50 text-green-600',
    amber: 'bg-amber-50 text-amber-600',
  };
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">{label}</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{value}</p>
          {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
        </div>
        <div className={cn('p-2.5 rounded-lg', colors[color])}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { data: queue, loading: queueLoading, error: queueError, refetch: refetchQueue } = useQueue();
  const { data: alertsData, loading: alertsLoading, error: alertsError, acknowledge } = useAlerts();
  const { data: capacity, error: capacityError } = useCapacity();
  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState<string | null>(null);

  const handleWebSocketMessage = useCallback((msg: { event: string }) => {
    if (['QUEUE_UPDATED', 'PATIENT_UPDATED', 'DETERIORATION'].includes(msg.event)) {
      refetchQueue();
    }
  }, [refetchQueue]);

  useWebSocket(handleWebSocketMessage);

  const activeAlerts = alertsData?.alerts.filter(a => !a.acknowledged) || [];
  const avgWait = queue?.patients.length
    ? queue.patients.reduce((sum, p) => sum + p.waitMinutes, 0) / queue.patients.length
    : 0;

  const connectionError = queueError || alertsError || capacityError;

  async function handleDeterioration() {
    setSimulating(true);
    setSimResult(null);
    try {
      await api.simulateDeterioration('P009');
      await refetchQueue();
      setSimResult('P009 deterioration simulated → priority escalated');
    } catch {
      setSimResult('Could not simulate (check backend is running)');
    } finally {
      setSimulating(false);
    }
  }

  return (
    <div className="p-6 space-y-6">
      {connectionError && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-xs text-red-700 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-red-500 flex-shrink-0" />
          <span><strong>Backend Connection Offline:</strong> Unable to reach the triage backend. Please start the FastAPI backend server on port 8000 to resume real-time operations.</span>
        </div>
      )}
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-800">Emergency Department Overview</h1>
          <p className="text-xs text-slate-400 mt-0.5">AI-assisted clinical decision support • Simulated data</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDeterioration}
            disabled={simulating}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 text-white text-xs font-semibold rounded hover:bg-red-700 disabled:opacity-50 transition-colors"
          >
            <TrendingDown className="h-3.5 w-3.5" />
            {simulating ? 'Simulating...' : 'Demo: P009 Deterioration'}
          </button>
          <Link href="/surge" className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500 text-white text-xs font-semibold rounded hover:bg-amber-600 transition-colors">
            <Zap className="h-3.5 w-3.5" /> Surge Sim
          </Link>
        </div>
      </div>

      {simResult && (
        <div className="bg-blue-50 border border-blue-200 rounded p-2 text-xs text-blue-700">
          ✓ {simResult}
        </div>
      )}

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <StatCard label="Patients Waiting" value={queue?.totalCount || 0} icon={Users} color="blue" />
        <StatCard label="Critical" value={queue?.criticalCount || 0} sub="Needs immediate attention" icon={AlertTriangle} color="red" />
        <StatCard label="High Risk" value={queue?.highCount || 0} icon={TrendingUp} color="orange" />
        <StatCard label="Avg Wait" value={formatWaitTime(avgWait)} icon={Clock} color="amber" />
        <StatCard
          label="Capacity"
          value={capacity ? formatCapacityPercent(capacity.utilization) : '—'}
          sub={capacity ? `${capacity.occupiedBeds}/${capacity.totalBeds} beds` : undefined}
          icon={BedDouble}
          color={capacity?.status === 'CRITICAL' ? 'red' : capacity?.status === 'WARNING' ? 'amber' : 'green'}
        />
      </div>

      {/* Disclaimer */}
      <div className="bg-slate-50 border border-slate-200 rounded px-3 py-2">
        <p className="text-xs text-slate-500">
          ⚕️ <strong>Decision-support prototype using simulated data.</strong> AI recommendations are not a substitute for clinical judgment. All triage decisions require clinician review.
        </p>
      </div>

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Queue */}
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <TriageQueue data={queue} loading={queueLoading} onRefresh={refetchQueue} maxItems={8} />
          {queue && queue.totalCount > 8 && (
            <Link href="/queue" className="block text-center text-xs text-blue-600 hover:underline mt-3">
              View all {queue.totalCount} patients →
            </Link>
          )}
        </div>

        {/* Right column */}
        <div className="space-y-4">
          {/* Active Alerts */}
          <div className="bg-white border border-slate-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">Active Alerts</h2>
              {activeAlerts.length > 0 && (
                <span className="text-xs font-bold text-red-700 bg-red-100 px-2 py-0.5 rounded">
                  {activeAlerts.length} unacknowledged
                </span>
              )}
            </div>
            {alertsLoading ? (
              <div className="space-y-2">
                {[1,2].map(i => <div key={i} className="h-14 bg-slate-100 rounded animate-pulse" />)}
              </div>
            ) : activeAlerts.length > 0 ? (
              <div className="space-y-2">
                {activeAlerts.slice(0, 5).map(alert => (
                  <AlertCard key={alert.id} alert={alert} onAcknowledge={acknowledge} />
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 text-center py-4">No active alerts</p>
            )}
            <Link href="/alerts" className="block text-center text-xs text-blue-600 hover:underline mt-3">
              View all alerts →
            </Link>
          </div>

          {/* Capacity */}
          {capacity && (
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-3">ED Capacity</h2>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs text-slate-600 mb-1">
                    <span>General</span>
                    <span className="font-semibold">{capacity.occupiedBeds}/{capacity.totalBeds}</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={cn('h-full rounded-full transition-all', capacity.utilization > 0.85 ? 'bg-red-500' : capacity.utilization > 0.7 ? 'bg-amber-500' : 'bg-green-500')}
                      style={{ width: `${capacity.utilization * 100}%` }}
                    />
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">{Math.round(capacity.utilization * 100)}% utilized</p>
                </div>
                <div>
                  <div className="flex justify-between text-xs text-slate-600 mb-1">
                    <span>Critical Beds</span>
                    <span className="font-semibold">{capacity.criticalOccupied}/{capacity.criticalBeds}</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={cn('h-full rounded-full transition-all', capacity.criticalUtilization > 0.9 ? 'bg-red-600' : 'bg-orange-500')}
                      style={{ width: `${capacity.criticalUtilization * 100}%` }}
                    />
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">{capacity.criticalAvailable} available</p>
                </div>
                {capacity.warningMessage && (
                  <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2">
                    ⚠ {capacity.warningMessage}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
