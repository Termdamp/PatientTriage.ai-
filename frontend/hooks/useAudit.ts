'use client';
import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { AuditListResponse } from '@/types';
import { MOCK_AUDIT_EVENTS } from '@/lib/mockData';

export function useAudit(patientId?: string) {
  const [data, setData] = useState<AuditListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAudit = useCallback(async () => {
    try {
      const result = patientId
        ? await api.getPatientAudit(patientId)
        : await api.getAudit();
      setData(result);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load audit events');
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => { fetchAudit(); }, [fetchAudit]);

  return { data, loading, error, refetch: fetchAudit };
}
