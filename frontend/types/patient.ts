import { Vitals, VitalSnapshot } from './vitals';

export type Gender = 'male' | 'female' | 'other';

export type PatientStatus = 'WAITING' | 'IN_REVIEW' | 'IN_TREATMENT' | 'COMPLETED';

export interface Patient {
  id: string;
  name: string;
  age: number;
  gender: Gender;
  chiefComplaint: string;
  symptoms: string[];
  medicalHistory: string[] | null;
  historyAvailable: boolean;
  arrivalTime: string;
  status: PatientStatus;
  createdAt: string;
  updatedAt: string;
  latestAssessment?: Assessment | null;
  latestVitals?: Vitals | null;
  vitalHistory?: VitalSnapshot[];
  assessmentHistory?: AssessmentSummary[];
}

export interface Assessment {
  id: string;
  priority: Priority;
  riskScore: number;
  confidence: number;
  safetyFlags: string[];
  reasons: ReasonItem[];
  recommendedAction: RecommendedAction;
  deteriorating: boolean;
  ageGroup: AgeGroup;
  createdAt: string;
  safetyFloor?: Priority | null;
  deteriorationSeverity?: string | null;
}

export interface AssessmentSummary {
  id: string;
  priority: Priority;
  riskScore: number;
  confidence: number;
  deteriorating: boolean;
  createdAt: string;
}

export type Priority = 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW';
export type AgeGroup = 'PEDIATRIC' | 'ADULT' | 'GERIATRIC';
export type RecommendedAction =
  | 'IMMEDIATE_CLINICIAN_REASSESSMENT'
  | 'URGENT_CLINICIAN_REVIEW'
  | 'CLINICIAN_REVIEW'
  | 'ROUTINE_REVIEW';

export interface ReasonItem {
  code: string;
  message: string;
}
