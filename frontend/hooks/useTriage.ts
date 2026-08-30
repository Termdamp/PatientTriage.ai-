'use client';
import { useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { TriageRequest, TriageResponse } from '@/types';

export function useTriage() {
  const [result, setResult] = useState<TriageResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitTriage = useCallback(async (data: TriageRequest) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.triagePatient(data);
      setResult(response);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Triage failed';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { result, loading, error, submitTriage, reset: () => setResult(null) };
}
