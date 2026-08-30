'use client';
import { Bell, Wifi, WifiOff } from 'lucide-react';
import { useWebSocket } from '@/hooks/useWebSocket';
import Link from 'next/link';

export function Header() {
  const { status } = useWebSocket();

  const isLive = status === 'connected';
  const isPolling = status === 'polling' || status === 'disconnected';

  return (
    <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6 flex-shrink-0">
      <div className="flex items-center gap-4">
        <h1 className="text-sm font-semibold text-slate-700">Emergency Department Clinical Decision Support</h1>
        <span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs font-semibold rounded border border-amber-200">
          SIMULATED DATA
        </span>
      </div>

      <div className="flex items-center gap-4">
        {/* Connection status */}
        <div className="flex items-center gap-1.5">
          {isLive ? (
            <>
              <Wifi className="h-3.5 w-3.5 text-green-500" />
              <span className="text-xs text-green-600 font-medium">Live</span>
            </>
          ) : (
            <>
              <WifiOff className="h-3.5 w-3.5 text-amber-500" />
              <span className="text-xs text-amber-600 font-medium">Polling</span>
            </>
          )}
        </div>

        {/* Alerts link */}
        <Link href="/alerts" className="flex items-center gap-1.5 text-slate-500 hover:text-slate-700 transition-colors">
          <Bell className="h-4 w-4" />
        </Link>

        {/* Disclaimer */}
        <div className="text-xs text-slate-400 hidden lg:block">
          AI recommendations require clinician review
        </div>
      </div>
    </header>
  );
}
