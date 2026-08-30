'use client';
import { useQueue } from '@/hooks/useQueue';
import { TriageQueue } from '@/components/queue/TriageQueue';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useCallback } from 'react';

export default function QueuePage() {
  const { data, loading, refetch } = useQueue();

  const handleMessage = useCallback((msg: { event: string }) => {
    if (['QUEUE_UPDATED', 'DETERIORATION', 'PATIENT_UPDATED'].includes(msg.event)) refetch();
  }, [refetch]);
  useWebSocket(handleMessage);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-lg font-bold text-slate-800">Patient Priority Queue</h1>
        <p className="text-xs text-slate-400 mt-0.5">Ordered by priority → deterioration → wait time</p>
      </div>
      <div className="bg-white border border-slate-200 rounded-lg p-5">
        <TriageQueue data={data} loading={loading} onRefresh={refetch} />
      </div>
    </div>
  );
}
