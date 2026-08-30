import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function priorityToNumeric(priority: string): number {
  const map: Record<string, number> = {
    CRITICAL: 4,
    HIGH: 3,
    MODERATE: 2,
    LOW: 1,
  };
  return map[priority] ?? 0;
}
