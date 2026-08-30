import { Priority, RecommendedAction, ReasonItem, AgeGroup } from './patient';

export interface TriageRequest {
  patientId?: string;
  name?: string;
  age: number;
  gender: string;
  chiefComplaint: string;
  symptoms: string[];
  historyAvailable: boolean;
  medicalHistory?: string[];
  vitals: {
    heartRate?: number;
    systolicBp?: number;
    diastolicBp?: number;
    spo2?: number;
    temperature?: number;
    respiratoryRate?: number;
  };
}

export interface TriageResponse {
  patientId: string;
  priority: Priority;
  riskScore: number;
  confidence: number;
  confidenceLevel: 'HIGH' | 'MODERATE' | 'LOW';
  safetyFloor: Priority | null;
  safetyFlags: string[];
  reasons: ReasonItem[];
  recommendedAction: RecommendedAction;
  ageGroup: AgeGroup;
  dataQuality: number;
  limitations: string[];
  modelVersion: string;
  deteriorating: boolean;
  deteriorationSeverity: string | null;
}
