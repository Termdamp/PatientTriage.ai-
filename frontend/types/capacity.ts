export interface Capacity {
  totalBeds: number;
  occupiedBeds: number;
  availableBeds: number;
  criticalBeds: number;
  criticalOccupied: number;
  criticalAvailable: number;
  utilization: number;
  criticalUtilization: number;
  status: 'NORMAL' | 'WARNING' | 'CRITICAL';
  warningMessage: string | null;
}

export interface SurgeResponse {
  mode: string;
  patientsPerHour: number;
  queueLength: number;
  criticalPatients: number;
  highPatients: number;
  moderatePatients?: number;
  capacityUtilization: number;
}
