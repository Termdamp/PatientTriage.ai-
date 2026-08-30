export interface AuditEvent {
  id: string;
  patientId: string | null;
  eventType: string;
  actor: string;
  description: string;
  metadata: Record<string, unknown> | null;
  createdAt: string;
}

export interface AuditListResponse {
  events: AuditEvent[];
  totalCount: number;
}
