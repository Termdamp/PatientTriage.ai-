'use client';
import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { Patient } from '@/types';
import { MOCK_PATIENTS } from '@/lib/mockData';

export function usePatient(id: string) {
  const [data, setData] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPatient = useCallback(async () => {
    try {
      const result = await api.getPatient(id);
      setData(result);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load patient details');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { fetchPatient(); }, [fetchPatient]);

  return { data, loading, error, refetch: fetchPatient };
}
