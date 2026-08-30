'use client';
import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { AlertListResponse } from '@/types';
import { MOCK_ALERTS } from '@/lib/mockData';
import { POLLING_INTERVAL } from '@/lib/constants';

export function useAlerts() {
  const [data, setData] = useState<AlertListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = useCallback(async () => {
    try {
      const result = await api.getAlerts();
      setData(result);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load alerts');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, POLLING_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  const acknowledge = useCallback(async (id: string) => {
    try {
      await api.acknowledgeAlert(id);
      await fetchAlerts();
    } catch {}
  }, [fetchAlerts]);

  return { data, loading, error, refetch: fetchAlerts, acknowledge };
}
