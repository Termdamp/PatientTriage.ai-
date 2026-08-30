'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { NAV_ITEMS } from '@/config/navigation';
import { Activity, Circle } from 'lucide-react';
import { cn } from '@/lib/utils';

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 bg-slate-900 flex flex-col h-screen flex-shrink-0">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-slate-700">
        <div className="flex items-center gap-2 mb-0.5">
          <Activity className="h-5 w-5 text-blue-400" />
          <span className="font-bold text-white text-sm tracking-wide">PATIENTTRIAGE</span>
          <span className="text-blue-400 font-bold text-sm">.AI</span>
        </div>
        <p className="text-xs text-slate-400 pl-7">ED Decision Support</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-0.5 overflow-y-auto scrollbar-thin">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              )}
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-slate-700">
        <div className="flex items-center gap-2 mb-1">
          <Circle className="h-2 w-2 fill-green-400 text-green-400" />
          <span className="text-xs text-slate-300 font-medium">System Online</span>
        </div>
        <p className="text-xs text-slate-500 pl-4">Prototype Mode</p>
        <p className="text-xs text-slate-600 pl-4 mt-0.5">Simulated Data</p>
      </div>
    </aside>
  );
}
