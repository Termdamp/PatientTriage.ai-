import { Priority, RecommendedAction, ReasonItem } from './patient';

export interface QueuePatient {
  id: string;
  name: string;
  age: number;
  gender: string;
  chiefComplaint: string;
  priority: Priority;
  riskScore: number;
  confidence: number;
  waitMinutes: number;
  deteriorating: boolean;
  safetyFlags: string[];
  reasons: ReasonItem[];
  recommendedAction: RecommendedAction;
  queuePosition: number;
  overrideApplied?: boolean;
}

export interface QueueResponse {
  patients: QueuePatient[];
  totalCount: number;
  criticalCount: number;
  highCount: number;
  moderateCount: number;
  lowCount: number;
  updatedAt: string;
}
