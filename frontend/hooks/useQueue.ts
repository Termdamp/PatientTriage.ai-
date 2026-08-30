'use client';
import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { QueueResponse } from '@/types';
import { MOCK_QUEUE_RESPONSE } from '@/lib/mockData';
import { POLLING_INTERVAL } from '@/lib/constants';

export function useQueue() {
  const [data, setData] = useState<QueueResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQueue = useCallback(async () => {
    try {
      const result = await api.getQueue();
      setData(result);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load queue');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchQueue();
    const interval = setInterval(fetchQueue, POLLING_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchQueue]);

  return { data, loading, error, refetch: fetchQueue };
}
