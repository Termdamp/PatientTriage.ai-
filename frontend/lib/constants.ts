import { Priority } from '@/types';

export const PRIORITY_CONFIG: Record<Priority, {
  label: string;
  color: string;
  bgColor: string;
  borderColor: string;
  textColor: string;
  dotColor: string;
}> = {
  CRITICAL: {
    label: 'CRITICAL',
    color: 'red',
    bgColor: 'bg-red-100',
    borderColor: 'border-red-500',
    textColor: 'text-red-700',
    dotColor: 'bg-red-500',
  },
  HIGH: {
    label: 'HIGH',
    color: 'orange',
    bgColor: 'bg-orange-100',
    borderColor: 'border-orange-500',
    textColor: 'text-orange-700',
    dotColor: 'bg-orange-500',
  },
  MODERATE: {
    label: 'MODERATE',
    color: 'amber',
    bgColor: 'bg-amber-100',
    borderColor: 'border-amber-500',
    textColor: 'text-amber-700',
    dotColor: 'bg-amber-500',
  },
  LOW: {
    label: 'LOW',
    color: 'green',
    bgColor: 'bg-green-100',
    borderColor: 'border-green-500',
    textColor: 'text-green-700',
    dotColor: 'bg-green-500',
  },
};

export const API_BASE_URL = 'http://localhost:8000';
export const WS_URL = 'ws://localhost:8000/ws/queue';

export const POLLING_INTERVAL = 10000; // 10 seconds

export const RECOMMENDED_ACTION_LABELS: Record<string, string> = {
  IMMEDIATE_CLINICIAN_REASSESSMENT: 'Immediate Clinician Reassessment',
  URGENT_CLINICIAN_REVIEW: 'Urgent Clinician Review',
  CLINICIAN_REVIEW: 'Clinician Review',
  ROUTINE_REVIEW: 'Routine Review',
};

export const EVENT_TYPE_LABELS: Record<string, string> = {
  PATIENT_CREATED: 'Patient Registered',
  TRIAGE_COMPLETED: 'Triage Completed',
  ASSESSMENT_UPDATED: 'Assessment Updated',
  DETERIORATION_DETECTED: 'Deterioration Detected',
  ALERT_CREATED: 'Alert Generated',
  CLINICIAN_REVIEWED: 'Clinician Reviewed',
  CLINICIAN_OVERRIDE: 'Clinician Override',
  CAPACITY_UPDATED: 'Capacity Updated',
  SURGE_STARTED: 'Surge Simulation Started',
  ALERT_ACKNOWLEDGED: 'Alert Acknowledged',
};
