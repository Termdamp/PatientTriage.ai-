'use client';
import { useCapacity } from '@/hooks/useCapacity';
import { cn } from '@/lib/utils';

export default function CapacityPage() {
  const { data, loading } = useCapacity();

  return (
    <div className="p-6">
      <div className="mb-5">
        <h1 className="text-lg font-bold text-slate-800">ED Capacity</h1>
        <p className="text-xs text-slate-400">Bed utilization and availability</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1,2,3].map(i => <div key={i} className="h-32 bg-slate-100 rounded-lg animate-pulse" />)}
        </div>
      ) : data ? (
        <div className="space-y-6">
          {data.warningMessage && (
            <div className={cn('border rounded-lg p-4', data.status === 'CRITICAL' ? 'bg-red-50 border-red-300' : 'bg-amber-50 border-amber-300')}>
              <p className={cn('text-sm font-semibold', data.status === 'CRITICAL' ? 'text-red-700' : 'text-amber-700')}>
                ⚠ {data.warningMessage}
              </p>
              <p className="text-xs text-slate-500 mt-1">Decision support only — clinician review required for capacity decisions.</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[{ label: 'Total Beds', value: data.totalBeds, sub: 'ED capacity' },
              { label: 'Occupied', value: data.occupiedBeds, sub: `${Math.round(data.utilization * 100)}% utilized` },
              { label: 'Available', value: data.availableBeds, sub: 'General beds' },
              { label: 'Critical Available', value: data.criticalAvailable, sub: `${data.criticalOccupied}/${data.criticalBeds} occupied` }
            ].map(stat => (
              <div key={stat.label} className="bg-white border border-slate-200 rounded-lg p-4">
                <p className="text-xs text-slate-500 uppercase tracking-wide">{stat.label}</p>
                <p className="text-3xl font-bold text-slate-800 mt-1">{stat.value}</p>
                <p className="text-xs text-slate-400 mt-0.5">{stat.sub}</p>
              </div>
            ))}
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-4">
            <h2 className="text-sm font-semibold text-slate-700">Utilization</h2>
            <div>
              <div className="flex justify-between text-xs text-slate-600 mb-1">
                <span>General Capacity</span>
                <span className="font-semibold">{data.occupiedBeds}/{data.totalBeds} ({Math.round(data.utilization*100)}%)</span>
              </div>
              <div className="h-4 bg-slate-100 rounded-full overflow-hidden">
                <div className={cn('h-full rounded-full', data.utilization > 0.85 ? 'bg-red-500' : data.utilization > 0.7 ? 'bg-amber-500' : 'bg-green-500')}
                  style={{ width: `${data.utilization * 100}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs text-slate-600 mb-1">
                <span>Critical Beds</span>
                <span className="font-semibold">{data.criticalOccupied}/{data.criticalBeds} ({Math.round(data.criticalUtilization*100)}%)</span>
              </div>
              <div className="h-4 bg-slate-100 rounded-full overflow-hidden">
                <div className={cn('h-full rounded-full', data.criticalUtilization > 0.9 ? 'bg-red-600' : 'bg-orange-500')}
                  style={{ width: `${data.criticalUtilization * 100}%` }} />
              </div>
            </div>
          </div>
        </div>
      ) : <p className="text-slate-400">No capacity data available</p>}
    </div>
  );
}
