
import { Priority } from '@/types';

export function formatWaitTime(minutes: number): string {
  // Scale down the displayed wait time by 5
  minutes = minutes / 5;

  if (minutes < 1) return '< 1 min';
  if (minutes < 60) return `${Math.round(minutes)} min`;

  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);

  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
}

export function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

export function formatRiskScore(score: number): string {
  return `${Math.round(score)} / 100`;
}

export function formatDateTime(isoString: string): string {
  try {
    return new Date(isoString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
}

export function formatDateTimeFull(isoString: string): string {
  try {
    return new Date(isoString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
}

export function formatCapacityPercent(utilization: number): string {
  return `${Math.round(utilization * 100)}%`;
}

export function formatSymptom(symptom: string): string {
  return symptom
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function formatGender(gender: string): string {
  return gender.charAt(0).toUpperCase() + gender.slice(1);
}

export function getAgeGroupLabel(ageGroup: string): string {
  const labels: Record<string, string> = {
    PEDIATRIC: 'Pediatric',
    ADULT: 'Adult',
    GERIATRIC: 'Geriatric',
  };

  return labels[ageGroup] || ageGroup;
}

export function getPriorityOrder(priority: Priority): number {
  const order: Record<Priority, number> = {
    CRITICAL: 4,
    HIGH: 3,
    MODERATE: 2,
    LOW: 1,
  };

  return order[priority] ?? 0;
}

