export type AlertSeverity = 'CRITICAL' | 'WARNING' | 'INFO';
export type AlertType = 'DETERIORATION' | 'WAITING_BREACH' | 'CAPACITY' | 'SYSTEM';

export interface Alert {
  id: string;
  patientId: string | null;
  type: AlertType;
  severity: AlertSeverity;
  message: string;
  metadata: Record<string, unknown> | null;
  acknowledged: boolean;
  createdAt: string;
  resolvedAt: string | null;
}

export interface AlertListResponse {
  alerts: Alert[];
  totalCount: number;
  unacknowledgedCount: number;
}
