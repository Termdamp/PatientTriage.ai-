import { API_BASE_URL } from './constants';
import {
  Patient,
  QueueResponse,
  AlertListResponse,
  Capacity,
  AuditListResponse,
  TriageRequest,
  TriageResponse,
  SurgeResponse,
} from '@/types';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const err = await response.json();
      detail = err.detail || detail;
    } catch {}
    throw new ApiError(response.status, detail);
  }
  return response.json();
}

export const api = {
  // Health
  health: () => request<{ status: string; database: string; version: string }>('/health'),

  // Patients
  getPatients: (status?: string) =>
    request<Patient[]>(`/patients${status ? `?status=${status}` : ''}`) ,

  getPatient: (id: string) => request<Patient>(`/patients/${id}`),

  // Triage
  triagePatient: (data: TriageRequest) =>
    request<TriageResponse>('/triage', { method: 'POST', body: JSON.stringify(data) }),

  // Queue
  getQueue: () => request<QueueResponse>('/queue'),

  // Alerts
  getAlerts: (unacknowledgedOnly?: boolean) =>
    request<AlertListResponse>(`/alerts${unacknowledgedOnly ? '?unacknowledged_only=true' : ''}`),

  acknowledgeAlert: (id: string) =>
    request<{ id: string; acknowledged: boolean }>(`/alerts/${id}/acknowledge`, { method: 'POST' }),

  // Capacity
  getCapacity: () => request<Capacity>('/capacity'),

  // Override
  overridePatient: (data: {
    patientId: string;
    assessmentId: string;
    newPriority: string;
    reason: string;
    clinicianId: string;
  }) => request('/override', { method: 'POST', body: JSON.stringify(data) }),

  // Audit
  getAudit: (limit?: number) =>
    request<AuditListResponse>(`/audit${limit ? `?limit=${limit}` : ''}`),

  getPatientAudit: (id: string) =>
    request<AuditListResponse>(`/patients/${id}/audit`),

  // Simulation
  simulateSurge: (multiplier: number) =>
    request<SurgeResponse>('/simulate/surge', {
      method: 'POST',
      body: JSON.stringify({ multiplier }),
    }),

  simulateDeterioration: (patientId: string) =>
    request('/simulate/deterioration/' + patientId, { method: 'POST' }),

  // Bed & Resource management
  updateResources: (data: any) =>
    request('/capacity/resources', { method: 'PUT', body: JSON.stringify(data) }),

  allocateBed: (patientId: string, bedId: string) =>
    request('/capacity/beds/allocate', { method: 'POST', body: JSON.stringify({ patientId, bedId }) }),

  releaseBed: (bedId: string, patientStatus: string) =>
    request('/capacity/beds/release', { method: 'POST', body: JSON.stringify({ bedId, patientStatus }) }),

  reallocateBeds: (data: any) =>
    request('/capacity/beds/reallocate', { method: 'POST', body: JSON.stringify(data) }),

  addBeds: (type: 'GENERAL' | 'CRITICAL_CARE', count: number = 1) =>
    request('/capacity/beds', { method: 'POST', body: JSON.stringify({ type, count }) }),

  removeBed: (bedId: string) =>
    request(`/capacity/beds/${bedId}`, { method: 'DELETE' }),

  setBedTotals: (generalBeds: number, criticalBeds: number) =>
    request('/capacity/beds/totals', { method: 'PUT', body: JSON.stringify({ generalBeds, criticalBeds }) }),

  updatePatientStatus: (patientId: string, status: string, reason?: string) =>
    request(`/patients/${patientId}/status`, { method: 'PATCH', body: JSON.stringify({ status, reason }) }),
};
