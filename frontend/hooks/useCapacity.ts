'use client';
import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { Capacity } from '@/types';
import { MOCK_CAPACITY } from '@/lib/mockData';
import { POLLING_INTERVAL } from '@/lib/constants';

export function useCapacity() {
  const [data, setData] = useState<Capacity | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCapacity = useCallback(async () => {
    try {
      const result = await api.getCapacity();
      setData(result);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load capacity');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCapacity();
    const interval = setInterval(fetchCapacity, POLLING_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchCapacity]);

  return { data, loading, error, refetch: fetchCapacity };
}
