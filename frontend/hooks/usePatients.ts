'use client';
import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { Patient } from '@/types';
import { MOCK_PATIENTS } from '@/lib/mockData';

export function usePatients() {
  const [data, setData] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPatients = useCallback(async () => {
    try {
      const result = await api.getPatients();
      setData(result);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load patients');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchPatients(); }, [fetchPatients]);

  return { data, loading, error, refetch: fetchPatients };
}
