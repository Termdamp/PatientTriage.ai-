import {
  LayoutDashboard,
  Users,
  ClipboardList,
  ListOrdered,
  Bell,
  BedDouble,
  Zap,
  ScrollText,
  Monitor,
} from 'lucide-react';
import { LucideIcon } from 'lucide-react';

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  badge?: string;
}

export const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Command Center', href: '/command-center', icon: Monitor },
  { label: 'Patients', href: '/patients', icon: Users },
  { label: 'Triage', href: '/triage', icon: ClipboardList },
  { label: 'Queue', href: '/queue', icon: ListOrdered },
  { label: 'Alerts', href: '/alerts', icon: Bell },
  { label: 'Capacity', href: '/capacity', icon: BedDouble },
  { label: 'Surge Simulation', href: '/surge', icon: Zap },
  { label: 'Audit', href: '/audit', icon: ScrollText },
];
