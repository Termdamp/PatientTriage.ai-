export interface Vitals {
  heartRate: number | null;
  systolicBp: number | null;
  diastolicBp: number | null;
  spo2: number | null;
  temperature: number | null;
  respiratoryRate: number | null;
  timestamp: string;
}

export interface VitalSnapshot extends Vitals {
  id: string;
  patientId: string;
}

export interface VitalInput {
  heartRate?: number;
  systolicBp?: number;
  diastolicBp?: number;
  spo2?: number;
  temperature?: number;
  respiratoryRate?: number;
}
