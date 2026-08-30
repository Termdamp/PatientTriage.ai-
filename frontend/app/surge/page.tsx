'use client';
import { useState } from 'react';
import { api } from '@/lib/api';
import { SurgeResponse } from '@/types';
import { Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

const SURGE_OPTIONS = [
  { multiplier: 1, label: 'Normal', description: '10 patients/hour', color: 'green' },
  { multiplier: 2, label: '2× Surge', description: '20 patients/hour', color: 'amber' },
  { multiplier: 3, label: '3× Surge', description: '30 patients/hour', color: 'red' },
];

export default function SurgePage() {
  const [selected, setSelected] = useState(1);
  const [result, setResult] = useState<SurgeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSimulate() {
    setLoading(true);
    setError('');
    try {
      const res = await api.simulateSurge(selected);
      setResult(res);
    } catch {
      setError('Hello F U.');
      setResult({ mode: selected === 3 ? '3X_SURGE' : selected === 2 ? '2X_SURGE' : 'NORMAL',
        patientsPerHour: selected * 10, queueLength: 8 + (selected * 10),
        criticalPatients: selected * 2, highPatients: selected * 4,
        capacityUtilization: 0.64 + (selected * 0.16) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6">
      <div className="mb-5">
        <h1 className="text-lg font-bold text-slate-800">Surge Simulation</h1>
        <p className="text-xs text-slate-400">Simulate ED patient surge for demonstration purposes</p>
      </div>

      <div className="max-w-2xl space-y-5">
        <div className="bg-white border border-slate-200 rounded-lg p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-4">Select Surge Level</h2>
          <div className="grid grid-cols-3 gap-3 mb-5">
            {SURGE_OPTIONS.map(opt => (
              <button
                key={opt.multiplier}
                onClick={() => setSelected(opt.multiplier)}
                className={cn(
                  'border-2 rounded-lg p-4 text-left transition-colors',
                  selected === opt.multiplier
                    ? opt.color === 'red' ? 'border-red-500 bg-red-50'
                      : opt.color === 'amber' ? 'border-amber-500 bg-amber-50'
                      : 'border-green-500 bg-green-50'
                    : 'border-slate-200 hover:border-slate-300'
                )}
              >
                <p className={cn('font-bold text-sm',
                  selected === opt.multiplier
                    ? opt.color === 'red' ? 'text-red-700' : opt.color === 'amber' ? 'text-amber-700' : 'text-green-700'
                    : 'text-slate-700'
                )}>{opt.label}</p>
                <p className="text-xs text-slate-500 mt-0.5">{opt.description}</p>
              </button>
            ))}
          </div>
          <button
            onClick={handleSimulate}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2.5 bg-slate-800 text-white text-sm font-semibold rounded hover:bg-slate-700 disabled:opacity-50 transition-colors"
          >
            <Zap className="h-4 w-4" />
            {loading ? 'Simulating...' : 'Simulate Surge'}
          </button>
          {error && <p className="text-xs text-amber-600 mt-2">{error} (showing estimated data)</p>}
        </div>

        {result && (
          <div className={cn(
            'bg-white border-2 rounded-lg p-5',
            result.mode.includes('3X') ? 'border-red-300' : result.mode.includes('2X') ? 'border-amber-300' : 'border-green-300'
          )}>
            <div className="flex items-center gap-2 mb-4">
              <Zap className={cn('h-5 w-5', result.mode.includes('3X') ? 'text-red-600' : result.mode.includes('2X') ? 'text-amber-600' : 'text-green-600')} />
              <h2 className="text-base font-bold text-slate-800">{result.mode.replace('_', ' ')} Active</h2>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { label: 'Patients/Hour', value: result.patientsPerHour },
                { label: 'Queue Length', value: result.queueLength },
                { label: 'Critical', value: result.criticalPatients },
                { label: 'Capacity', value: `${Math.round(result.capacityUtilization * 100)}%` },
              ].map(stat => (
                <div key={stat.label} className="bg-slate-50 rounded p-3">
                  <p className="text-xs text-slate-500">{stat.label}</p>
                  <p className="text-xl font-bold text-slate-800 mt-0.5">{stat.value}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
