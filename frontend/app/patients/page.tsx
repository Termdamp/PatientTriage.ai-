'use client';
import { usePatients } from '@/hooks/usePatients';
import { PriorityBadge } from '@/components/queue/PriorityBadge';
import { WaitTimeBadge } from '@/components/queue/WaitTimeBadge';
import { formatWaitTime, formatSymptom } from '@/lib/formatters';
import { useState } from 'react';
import Link from 'next/link';
import { Search, TrendingDown } from 'lucide-react';
import { Patient, Priority } from '@/types';
import { cn } from '@/lib/utils';

const FILTERS = ['ALL', 'CRITICAL', 'HIGH', 'MODERATE', 'LOW'] as const;

function getWaitMinutes(patient: Patient): number {
  return (Date.now() - new Date(patient.arrivalTime).getTime()) / 60000;
}

export default function PatientsPage() {
  const { data: patients, loading } = usePatients();
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<typeof FILTERS[number]>('ALL');

  const filtered = patients.filter(p => {
    const priority = p.latestAssessment?.priority;
    const matchesPriority = filter === 'ALL' || priority === filter;
    const matchesSearch = !search ||
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.id.toLowerCase().includes(search.toLowerCase()) ||
      p.chiefComplaint.toLowerCase().includes(search.toLowerCase());
    return matchesPriority && matchesSearch;
  });

  return (
    <div className="p-6">
      <div className="mb-5">
        <h1 className="text-lg font-bold text-slate-800">Patients</h1>
        <p className="text-xs text-slate-400">{patients.length} total patients</p>
      </div>

      {/* Filters & Search */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-lg p-1">
          {FILTERS.map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                'px-3 py-1 text-xs font-semibold rounded transition-colors',
                filter === f ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'
              )}
            >
              {f}
            </button>
          ))}
        </div>
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search patient..."
            className="w-full pl-8 pr-3 py-1.5 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Table */}
      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50">
              {['ID', 'Patient', 'Age', 'Chief Complaint', 'Priority', 'Risk', 'Confidence', 'Wait', 'Status'].map(h => (
                <th key={h} className="px-3 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 9 }).map((_, j) => (
                    <td key={j} className="px-3 py-3">
                      <div className="h-4 bg-slate-100 rounded animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-3 py-8 text-center text-sm text-slate-400">
                  No patients match your filters
                </td>
              </tr>
            ) : (
              filtered.map(patient => {
                const assessment = patient.latestAssessment;
                const waitMin = getWaitMinutes(patient);
                return (
                  <tr key={patient.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-3 py-2.5">
                      <Link href={`/patients/${patient.id}`} className="text-xs font-mono font-semibold text-blue-600 hover:underline">
                        {patient.id}
                      </Link>
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-1.5">
                        <Link href={`/patients/${patient.id}`} className="text-sm font-medium text-slate-800 hover:text-blue-600">
                          {patient.name}
                        </Link>
                        {assessment?.deteriorating && (
                          <TrendingDown className="h-3.5 w-3.5 text-red-500" />
                        )}
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-sm text-slate-600">{patient.age}</td>
                    <td className="px-3 py-2.5 text-xs text-slate-600 max-w-32 truncate">{patient.chiefComplaint}</td>
                    <td className="px-3 py-2.5">
                      {assessment ? <PriorityBadge priority={assessment.priority} size="sm" /> : <span className="text-xs text-slate-400">—</span>}
                    </td>
                    <td className="px-3 py-2.5 text-sm font-medium text-slate-700">
                      {assessment ? Math.round(assessment.riskScore) : '—'}
                    </td>
                    <td className="px-3 py-2.5 text-sm text-slate-600">
                      {assessment ? `${Math.round(assessment.confidence * 100)}%` : '—'}
                    </td>
                    <td className="px-3 py-2.5">
                      <WaitTimeBadge minutes={waitMin} />
                    </td>
                    <td className="px-3 py-2.5">
                      <span className={cn(
                        'text-xs px-2 py-0.5 rounded font-medium',
                        patient.status === 'WAITING' ? 'bg-blue-100 text-blue-700' :
                        patient.status === 'IN_REVIEW' ? 'bg-amber-100 text-amber-700' :
                        patient.status === 'IN_TREATMENT' ? 'bg-purple-100 text-purple-700' :
                        'bg-green-100 text-green-700'
                      )}>
                        {patient.status.replace('_', ' ')}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
