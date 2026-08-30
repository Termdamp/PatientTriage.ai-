'use client';

import { useQueue } from '@/hooks/useQueue';
import { useAlerts } from '@/hooks/useAlerts';
import { useWebSocket } from '@/hooks/useWebSocket';
import { api } from '@/lib/api';
import { PriorityBadge } from '@/components/queue/PriorityBadge';
import { cn } from '@/lib/utils';
import {
  TrendingDown,
  Clock,
  Activity,
  Settings,
  ShieldAlert,
  Plus,
  X,
  RefreshCw,
  Eye,
  UserCheck
} from 'lucide-react';
import { useState, useCallback, useEffect } from 'react';

interface ReallocationRecommendation {
  type: string;
  priority: string;
  message: string;
  metadata: {
    stepDownPatientId?: string;
    currentBedId?: string;
    newGeneralBedId?: string;
    incomingPatientId?: string;
    patientId?: string;
    bedId?: string;
  };
}

export default function CommandCenterPage() {
  const { data: queue, refetch: refetchQueue } = useQueue();
  const { data: alertsData, acknowledge, refetch: refetchAlerts } = useAlerts();
  const [capacityData, setCapacityData] = useState<any>(null);
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const [selectedPatientDetail, setSelectedPatientDetail] = useState<any>(null);
  const [overridePriority, setOverridePriority] = useState<string>('');
  const [overrideReason, setOverrideReason] = useState<string>('');
  const [overrideError, setOverrideError] = useState<string | null>(null);
  const [overrideSuccess, setOverrideSuccess] = useState<boolean>(false);
  const [showConfigModal, setShowConfigModal] = useState<boolean>(false);
  const [showAllAlerts, setShowAllAlerts] = useState<boolean>(false);
  const [bedActionError, setBedActionError] = useState<string | null>(null);

  // Form states for resource / bed configuration (modal)
  const [docTotal, setDocTotal] = useState(5);
  const [docActive, setDocActive] = useState(3);
  const [nurseTotal, setNurseTotal] = useState(12);
  const [nurseActive, setNurseActive] = useState(8);
  const [ventTotal, setVentTotal] = useState(4);
  const [ventActive, setVentActive] = useState(1);
  const [monTotal, setMonTotal] = useState(8);
  const [monActive, setMonActive] = useState(2);
  const [generalBedsTotal, setGeneralBedsTotal] = useState(0);
  const [criticalBedsTotal, setCriticalBedsTotal] = useState(0);

  const fetchCapacityDetails = useCallback(async () => {
    try {
      const result = await api.getCapacity() as any;
      setCapacityData(result);
      if (result.resources) {
        setDocTotal(result.resources.doctorsTotal);
        setDocActive(result.resources.doctorsActive);
        setNurseTotal(result.resources.nursesTotal);
        setNurseActive(result.resources.nursesActive);
        setVentTotal(result.resources.ventilatorsTotal);
        setVentActive(result.resources.ventilatorsActive);
        setMonTotal(result.resources.monitorsTotal);
        setMonActive(result.resources.monitorsActive);
      }
      setGeneralBedsTotal(result.totalBeds - result.criticalBeds);
      setCriticalBedsTotal(result.criticalBeds);
    } catch (err) {
      console.error('Failed to fetch capacity details:', err);
    }
  }, []);

  const refreshAll = useCallback(() => {
    refetchQueue();
    refetchAlerts();
    fetchCapacityDetails();
  }, [refetchQueue, refetchAlerts, fetchCapacityDetails]);

  const handleWebSocketMessage = useCallback((msg: { event: string }) => {
    if (['QUEUE_UPDATED', 'PATIENT_UPDATED', 'DETERIORATION', 'ALERT_CREATED'].includes(msg.event)) {
      refreshAll();
    }
  }, [refreshAll]);

  useWebSocket(handleWebSocketMessage);

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  useEffect(() => {
    if (!selectedPatientId) {
      setSelectedPatientDetail(null);
      return;
    }
    setOverrideSuccess(false);
    setOverrideError(null);
    api.getPatient(selectedPatientId)
      .then(res => {
        setSelectedPatientDetail(res);
        if (res.latestAssessment) {
          setOverridePriority(res.latestAssessment.priority);
        }
      })
      .catch(err => console.error('Failed to load patient detail:', err));
  }, [selectedPatientId]);

  const handleOverride = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPatientDetail || !overridePriority) return;
    setOverrideError(null);
    setOverrideSuccess(false);
    try {
      await api.overridePatient({
        patientId: selectedPatientDetail.id,
        assessmentId: selectedPatientDetail.latestAssessment?.id || 'manual',
        newPriority: overridePriority,
        reason: overrideReason || 'Clinician override',
        clinicianId: 'DR_COMMAND_CENTER'
      });
      setOverrideSuccess(true);
      setOverrideReason('');
      refreshAll();
      const updated = await api.getPatient(selectedPatientDetail.id);
      setSelectedPatientDetail(updated);
    } catch (err: any) {
      setOverrideError(err.message || 'Failed to submit priority override');
    }
  };

  const handleSaveResources = async () => {
    try {
      await api.updateResources({
        doctorsTotal: docTotal,
        doctorsActive: docActive,
        nursesTotal: nurseTotal,
        nursesActive: nurseActive,
        ventilatorsTotal: ventTotal,
        ventilatorsActive: ventActive,
        monitorsTotal: monTotal,
        monitorsActive: monActive
      });
      // Reconcile bed totals in the same save action
      await api.setBedTotals(generalBedsTotal, criticalBedsTotal);
      setShowConfigModal(false);
      fetchCapacityDetails();
    } catch (err: any) {
      alert(err.message || 'Failed to save configuration');
    }
  };

  const handleAllocateBed = async (patientId: string, bedId: string) => {
    try {
      await api.allocateBed(patientId, bedId);
      refreshAll();
      const updated = await api.getPatient(patientId);
      setSelectedPatientDetail(updated);
    } catch (err: any) {
      alert(err.message || 'Failed to allocate bed');
    }
  };

  const handleReleaseBed = async (bedId: string, finalStatus: string) => {
    try {
      await api.releaseBed(bedId, finalStatus);
      refreshAll();
      if (selectedPatientDetail && selectedPatientDetail.bedId === bedId) {
        const updated = await api.getPatient(selectedPatientDetail.id);
        setSelectedPatientDetail(updated);
      }
    } catch (err: any) {
      alert(err.message || 'Failed to release bed');
    }
  };

  const handleExecuteReallocation = async (rec: ReallocationRecommendation) => {
    try {
      await api.reallocateBeds(rec.metadata);
      refreshAll();
      if (selectedPatientId) {
        const updated = await api.getPatient(selectedPatientId);
        setSelectedPatientDetail(updated);
      }
    } catch (err: any) {
      alert(err.message || 'Failed to execute reallocation');
    }
  };

  // Mark a patient treated/discharged directly — removes them from the queue
  // even if they were never assigned a bed. Releases the bed too if they had one.
  const handleMarkTreated = async (patientId: string) => {
    if (!confirm('Mark this patient as treated and remove them from the queue?')) return;
    try {
      await api.updatePatientStatus(patientId, 'COMPLETED', 'Treated via Command Center');
      refreshAll();
      setSelectedPatientId(null);
    } catch (err: any) {
      alert(err.message || 'Failed to update patient status');
    }
  };

  // Quick, in-place bed count controls (used directly on the bed matrix)
  const handleAddBed = async (type: 'GENERAL' | 'CRITICAL_CARE') => {
    setBedActionError(null);
    try {
      await api.addBeds(type, 1);
      fetchCapacityDetails();
    } catch (err: any) {
      setBedActionError(err.message || 'Failed to add bed');
    }
  };

  const handleRemoveBed = async (bedId: string) => {
    setBedActionError(null);
    try {
      await api.removeBed(bedId);
      fetchCapacityDetails();
    } catch (err: any) {
      setBedActionError(err.message || 'Failed to remove bed');
    }
  };

  const activeAlerts = alertsData?.alerts.filter(a => !a.acknowledged) || [];
  const visibleAlerts = showAllAlerts ? activeAlerts : activeAlerts.slice(0, 3);

  return (
    <div className="p-6 space-y-5 bg-slate-950 text-slate-100 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Activity className="h-6 w-6 text-blue-500 animate-pulse" />
            ED Clinical Command Center
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Live patient queue, bed capacity, and clinician decision support.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowConfigModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded transition-colors text-white border border-slate-700"
          >
            <Settings className="h-3.5 w-3.5 text-slate-400" />
            Configure Resources & Beds
          </button>
          <button
            onClick={refreshAll}
            className="p-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-slate-300"
            title="Refresh All"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Compact stat strip — replaces the old separate "Resource Gauges" card */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        {[
          { label: 'Doctors', value: capacityData ? `${capacityData.resources?.doctorsActive}/${capacityData.resources?.doctorsTotal}` : '—' },
          { label: 'Nurses', value: capacityData ? `${capacityData.resources?.nursesActive}/${capacityData.resources?.nursesTotal}` : '—' },
          { label: 'Ventilators', value: capacityData ? `${capacityData.resources?.ventilatorsActive}/${capacityData.resources?.ventilatorsTotal}` : '—' },
          { label: 'Monitors', value: capacityData ? `${capacityData.resources?.monitorsActive}/${capacityData.resources?.monitorsTotal}` : '—' },
          { label: 'Bed Occupancy', value: capacityData ? `${Math.round(capacityData.utilization * 100)}%` : '—', highlight: capacityData?.status },
          { label: 'ICU Occupancy', value: capacityData ? `${Math.round(capacityData.criticalUtilization * 100)}%` : '—' },
        ].map((stat) => (
          <div key={stat.label} className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2">
            <p className="text-[10px] text-slate-400 uppercase tracking-wider">{stat.label}</p>
            <p className={cn(
              'text-base font-bold mt-0.5',
              stat.highlight === 'CRITICAL' ? 'text-red-400' : stat.highlight === 'WARNING' ? 'text-amber-400' : 'text-white'
            )}>
              {stat.value}
            </p>
          </div>
        ))}
      </div>

      {/* Main Grid: 3 focused sections instead of 6 stacked cards */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">

        {/* Section 1: Patient Flow (Alerts + Queue merged) */}
        <div className="xl:col-span-1 bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Patient Flow</h2>
            {activeAlerts.length > 0 && (
              <span className="text-[10px] font-bold text-red-400 bg-red-950/60 border border-red-900 px-2 py-0.5 rounded-full">
                {activeAlerts.length} alert{activeAlerts.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>

          {activeAlerts.length > 0 && (
            <div className="space-y-1.5">
              {visibleAlerts.map((alert: any) => (
                <div
                  key={alert.id}
                  className={cn(
                    'border rounded p-2 text-xs flex items-center justify-between gap-2',
                    alert.severity === 'CRITICAL'
                      ? 'bg-red-950/20 border-red-900/60 text-red-300'
                      : 'bg-amber-950/20 border-amber-900/60 text-amber-300'
                  )}
                >
                  <p className="truncate">{alert.message}</p>
                  <button
                    onClick={() => acknowledge(alert.id).then(refreshAll)}
                    className="shrink-0 px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-[10px] font-medium rounded border border-slate-700 text-slate-300"
                  >
                    Ack
                  </button>
                </div>
              ))}
              {activeAlerts.length > 3 && (
                <button
                  onClick={() => setShowAllAlerts(v => !v)}
                  className="text-[10px] text-slate-400 hover:text-slate-200"
                >
                  {showAllAlerts ? 'Show fewer' : `Show ${activeAlerts.length - 3} more`}
                </button>
              )}
            </div>
          )}

          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
              Triage Priority Queue
            </p>
            {queue?.patients && queue.patients.length > 0 ? (
              <div className="space-y-1.5 max-h-[440px] overflow-y-auto pr-1 scrollbar-thin">
                {queue.patients.map((pat: any) => {
                  const isSelected = selectedPatientId === pat.id;
                  const isOverdue = pat.nextReassessmentDue
                    ? new Date(pat.nextReassessmentDue).getTime() < Date.now()
                    : false;

                  return (
                    <div
                      key={pat.id}
                      onClick={() => setSelectedPatientId(pat.id)}
                      className={cn(
                        'p-2.5 rounded border text-xs cursor-pointer transition-all flex items-center justify-between gap-3',
                        isSelected
                          ? 'bg-blue-950/40 border-blue-600 shadow-md'
                          : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                      )}
                    >
                      <div className="space-y-0.5 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-white truncate">{pat.name}</span>
                          <span className="text-slate-500 shrink-0">{pat.age}{pat.gender[0].toUpperCase()}</span>
                        </div>
                        <p className="text-slate-400 text-[11px] truncate max-w-[170px]">{pat.chiefComplaint}</p>
                        {isOverdue && (
                          <div className="text-[10px] flex items-center gap-1 font-mono text-red-400 font-bold">
                            <Clock className="h-3 w-3" /> Reassessment overdue
                          </div>
                        )}
                      </div>
                      <div className="flex flex-col items-end gap-1 shrink-0">
                        <PriorityBadge priority={pat.priority} />
                        {pat.deteriorating && (
                          <span className="flex items-center gap-0.5 text-[10px] font-semibold text-red-400">
                            <TrendingDown className="h-3 w-3" /> Det.
                          </span>
                        )}
                        <span className="text-[10px] text-slate-500 font-mono">{Math.round(pat.waitMinutes)}m</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-slate-500 text-center py-10">Queue empty. No active waiting patients.</p>
            )}
          </div>
        </div>

        {/* Section 2: Bed Matrix (recommendation banner folded in, plus quick add/remove) */}
        <div className="xl:col-span-1 bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              ED Bed Matrix
            </span>
            {capacityData && (
              <span className="text-[10px] text-slate-400 font-semibold font-mono">
                {capacityData.occupiedBeds}/{capacityData.totalBeds} occupied
              </span>
            )}
          </div>

          {capacityData?.recommendations && capacityData.recommendations.length > 0 && (
            <div className="bg-amber-950/20 border border-amber-900/60 rounded p-2.5 space-y-2">
              {capacityData.recommendations.map((rec: any, idx: number) => (
                <div key={idx} className="text-xs space-y-1.5">
                  <p className="text-amber-200 flex items-start gap-1.5">
                    <ShieldAlert className="h-3.5 w-3.5 shrink-0 mt-0.5 text-amber-400" />
                    {rec.message}
                  </p>
                  {rec.type === 'STEP_DOWN' && (
                    <button
                      onClick={() => handleExecuteReallocation(rec)}
                      className="w-full py-1 bg-amber-600 hover:bg-amber-700 text-[10px] font-semibold text-white rounded transition-colors"
                    >
                      Execute Reallocation / Transfer
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {bedActionError && (
            <p className="text-red-400 text-[10px]">{bedActionError}</p>
          )}

          {capacityData?.beds ? (
            <div className="space-y-4">
              {/* Critical Care Beds */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <p className="text-[10px] font-bold text-red-400 uppercase tracking-wider font-mono">
                    ICU/Critical ({capacityData.criticalOccupied}/{capacityData.criticalBeds})
                  </p>
                  <button
                    onClick={() => handleAddBed('CRITICAL_CARE')}
                    className="flex items-center gap-0.5 text-[10px] text-slate-400 hover:text-white"
                    title="Add a critical care bed"
                  >
                    <Plus className="h-3 w-3" /> Add
                  </button>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {capacityData.beds.filter((b: any) => b.type === 'CRITICAL_CARE').map((bed: any) => (
                    <div
                      key={bed.id}
                      className={cn(
                        'group relative p-2 rounded border text-xs text-center cursor-pointer transition-all flex flex-col justify-between h-20',
                        bed.status === 'AVAILABLE'
                          ? 'bg-emerald-950/15 border-emerald-900/60 hover:bg-emerald-950/20'
                          : 'bg-red-950/20 border-red-900 hover:border-red-600'
                      )}
                      onClick={() => bed.patientId && setSelectedPatientId(bed.patientId)}
                    >
                      {bed.status === 'AVAILABLE' && (
                        <button
                          onClick={(e) => { e.stopPropagation(); handleRemoveBed(bed.id); }}
                          className="hidden group-hover:flex absolute -top-1.5 -right-1.5 h-4 w-4 items-center justify-center rounded-full bg-slate-800 border border-slate-600 text-slate-300 hover:text-red-400 hover:border-red-500"
                          title="Remove this bed"
                        >
                          <X className="h-2.5 w-2.5" />
                        </button>
                      )}
                      <div className="flex items-center justify-between gap-1 border-b border-slate-800 pb-0.5">
                        <span className="font-mono text-[9px] font-bold tracking-wide text-slate-400">{bed.id}</span>
                        <span className={cn('h-1.5 w-1.5 rounded-full', bed.status === 'AVAILABLE' ? 'bg-emerald-400' : 'bg-red-500')} />
                      </div>
                      {bed.status === 'OCCUPIED' ? (
                        <div className="flex-1 flex flex-col justify-center py-1">
                          <p className="font-semibold text-white truncate text-[11px]">{bed.patientName}</p>
                          <p className="text-[9px] text-red-300 font-mono mt-0.5">{bed.patientPriority}</p>
                        </div>
                      ) : (
                        <p className="text-slate-500 text-[10px] py-3">Empty</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* General Beds */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <p className="text-[10px] font-bold text-blue-400 uppercase tracking-wider font-mono">
                    General ({capacityData.occupiedBeds - capacityData.criticalOccupied}/{capacityData.totalBeds - capacityData.criticalBeds})
                  </p>
                  <button
                    onClick={() => handleAddBed('GENERAL')}
                    className="flex items-center gap-0.5 text-[10px] text-slate-400 hover:text-white"
                    title="Add a general bed"
                  >
                    <Plus className="h-3 w-3" /> Add
                  </button>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-56 overflow-y-auto pr-1 scrollbar-thin">
                  {capacityData.beds.filter((b: any) => b.type === 'GENERAL').map((bed: any) => (
                    <div
                      key={bed.id}
                      className={cn(
                        'group relative p-2 rounded border text-xs text-center cursor-pointer transition-all flex flex-col justify-between h-20',
                        bed.status === 'AVAILABLE'
                          ? 'bg-slate-900 border-slate-850 hover:bg-slate-800'
                          : 'bg-blue-950/15 border-blue-900 hover:border-blue-600'
                      )}
                      onClick={() => bed.patientId && setSelectedPatientId(bed.patientId)}
                    >
                      {bed.status === 'AVAILABLE' && (
                        <button
                          onClick={(e) => { e.stopPropagation(); handleRemoveBed(bed.id); }}
                          className="hidden group-hover:flex absolute -top-1.5 -right-1.5 h-4 w-4 items-center justify-center rounded-full bg-slate-800 border border-slate-600 text-slate-300 hover:text-red-400 hover:border-red-500"
                          title="Remove this bed"
                        >
                          <X className="h-2.5 w-2.5" />
                        </button>
                      )}
                      <div className="flex items-center justify-between gap-1 border-b border-slate-800 pb-0.5">
                        <span className="font-mono text-[9px] font-bold tracking-wide text-slate-400">{bed.id}</span>
                        <span className={cn('h-1.5 w-1.5 rounded-full', bed.status === 'AVAILABLE' ? 'bg-slate-600' : 'bg-blue-400')} />
                      </div>
                      {bed.status === 'OCCUPIED' ? (
                        <div className="flex-1 flex flex-col justify-center py-1">
                          <p className="font-semibold text-white truncate text-[11px]">{bed.patientName}</p>
                          <p className="text-[9px] text-blue-300 font-mono mt-0.5">{bed.patientPriority}</p>
                        </div>
                      ) : (
                        <p className="text-slate-500 text-[10px] py-3">Empty</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-44 bg-slate-800 animate-pulse rounded" />
          )}
        </div>

        {/* Section 3: Selected Patient — vitals, AI assessment and actions merged into one panel */}
        <div className="xl:col-span-1 bg-slate-900 border border-slate-800 rounded-lg p-4">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 border-b border-slate-800 pb-2 flex items-center gap-1.5">
            <Eye className="h-4 w-4 text-blue-500" />
            Patient Detail
          </h2>

          {selectedPatientDetail ? (
            <div className="space-y-4 text-xs">
              {/* Summary */}
              <div className="flex justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="font-bold text-white text-sm">{selectedPatientDetail.name}</h3>
                  <p className="text-slate-400 mt-0.5">
                    Age {selectedPatientDetail.age} • {selectedPatientDetail.gender} • Arrived {new Date(selectedPatientDetail.arrivalTime).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </p>
                </div>
                <div className="text-right">
                  <PriorityBadge priority={selectedPatientDetail.latestAssessment?.priority || 'LOW'} />
                  <p className="text-[10px] text-slate-500 mt-1 font-mono">
                    Bed: {selectedPatientDetail.bedId || 'Unallocated'}
                  </p>
                </div>
              </div>

              {/* Latest vitals (single line, not full history) */}
              {selectedPatientDetail.vitalHistory && selectedPatientDetail.vitalHistory.length > 0 && (
                <div className="bg-slate-950 rounded p-2.5 border border-slate-850 font-mono text-[11px] flex justify-between items-center">
                  <span>
                    HR: <span className="font-bold text-white">{selectedPatientDetail.vitalHistory[0].heartRate}</span> •{' '}
                    BP: <span className="font-bold text-white">{selectedPatientDetail.vitalHistory[0].systolicBp}/{selectedPatientDetail.vitalHistory[0].diastolicBp}</span> •{' '}
                    SpO2: <span className="font-bold text-white">{selectedPatientDetail.vitalHistory[0].spo2}%</span>
                  </span>
                  {selectedPatientDetail.latestAssessment?.deteriorating && (
                    <span className="text-red-400 flex items-center font-bold text-[10px]">
                      <TrendingDown className="h-3.5 w-3.5 mr-0.5" /> Det.
                    </span>
                  )}
                </div>
              )}

              {/* AI Assessment (decision trace + Qwen explanation combined) */}
              <div className="bg-slate-950 rounded p-3 border border-slate-850 space-y-2">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-800 pb-1.5">
                  <Activity className="h-3.5 w-3.5 text-blue-400" />
                  AI Assessment
                </p>

                {selectedPatientDetail.latestAssessment ? (
                  <div className="space-y-2">
                    <div className="flex justify-between text-[11px]">
                      <span className="text-slate-400">Risk score:</span>
                      <span className="font-bold text-white font-mono">{selectedPatientDetail.latestAssessment.riskScore}/100</span>
                    </div>

                    {selectedPatientDetail.latestAssessment.safetyFlags?.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {selectedPatientDetail.latestAssessment.safetyFlags.map((flag: string) => (
                          <span key={flag} className="px-1.5 py-0.5 bg-red-950/40 text-red-400 border border-red-900/60 rounded text-[9px] font-semibold">
                            {flag.replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    )}

                    <p className="text-slate-300 text-[11px] leading-relaxed pt-1 border-t border-slate-900">
                      {selectedPatientDetail.latestAssessment?.explanation ||
                        selectedPatientDetail.latestAssessment.reasons?.map((r: any) => r.message).join(' ') ||
                        'No explanation available.'}
                    </p>
                  </div>
                ) : (
                  <p className="text-slate-500 text-[10px]">No assessment data available.</p>
                )}
              </div>

              {/* Bed Allocation Actions */}
              <div className="border-t border-slate-800 pt-3 space-y-2">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Bed Control</p>
                {selectedPatientDetail.bedId ? (
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleReleaseBed(selectedPatientDetail.bedId, 'COMPLETED')}
                      className="flex-1 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white rounded transition-colors border border-slate-700"
                    >
                      Discharge (Release Bed)
                    </button>
                    <button
                      onClick={() => handleReleaseBed(selectedPatientDetail.bedId, 'WAITING')}
                      className="flex-1 py-1.5 bg-slate-850 hover:bg-slate-750 text-xs font-semibold text-slate-300 rounded transition-colors border border-slate-700"
                    >
                      Return to Lobby
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <p className="text-[10px] text-slate-500">Select an empty bed to admit:</p>
                    <div className="grid grid-cols-3 gap-1">
                      {capacityData?.beds?.filter((b: any) => b.status === 'AVAILABLE').slice(0, 6).map((bed: any) => (
                        <button
                          key={bed.id}
                          onClick={() => handleAllocateBed(selectedPatientDetail.id, bed.id)}
                          className="py-1 px-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-[10px] font-medium rounded text-slate-300"
                        >
                          {bed.id}
                        </button>
                      ))}
                    </div>
                    <p className="text-[10px] text-slate-500 pt-1">
                      Treated without needing a bed (e.g. fast-track)?
                    </p>
                    <button
                      onClick={() => handleMarkTreated(selectedPatientDetail.id)}
                      className="w-full py-1.5 bg-emerald-900/40 hover:bg-emerald-900/60 border border-emerald-800 text-xs font-semibold text-emerald-300 rounded transition-colors"
                    >
                      Mark Treated — Remove from Queue
                    </button>
                  </div>
                )}
              </div>

              {/* Clinician Priority Override */}
              <div className="border-t border-slate-800 pt-3 space-y-2">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Priority Override</p>
                <form onSubmit={handleOverride} className="space-y-2">
                  <div className="flex gap-2">
                    <select
                      value={overridePriority}
                      onChange={(e) => setOverridePriority(e.target.value)}
                      className="w-28 bg-slate-950 border border-slate-850 rounded px-2 py-1 text-xs text-white"
                    >
                      <option value="CRITICAL">CRITICAL</option>
                      <option value="HIGH">HIGH</option>
                      <option value="MODERATE">MODERATE</option>
                      <option value="LOW">LOW</option>
                    </select>
                    <input
                      type="text"
                      placeholder="Clinical justification..."
                      value={overrideReason}
                      onChange={(e) => setOverrideReason(e.target.value)}
                      required
                      className="flex-1 bg-slate-950 border border-slate-850 rounded px-2.5 py-1 text-xs text-white placeholder-slate-600"
                    />
                  </div>
                  {overrideError && <p className="text-red-400 text-[10px]">{overrideError}</p>}
                  {overrideSuccess && <p className="text-emerald-400 text-[10px]">Override applied.</p>}
                  <button
                    type="submit"
                    className="w-full py-1.5 bg-blue-600 hover:bg-blue-700 text-xs font-semibold text-white rounded transition-colors"
                  >
                    Submit Override
                  </button>
                </form>
              </div>
            </div>
          ) : (
            <div className="text-center py-20 text-slate-500 text-xs flex flex-col items-center gap-2">
              <UserCheck className="h-6 w-6 text-slate-700" />
              Select a patient from the queue or bed matrix to view details and clinical controls.
            </div>
          )}
        </div>
      </div>

      {/* Resource & Bed Configuration Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 w-full max-w-md text-xs space-y-4 shadow-xl max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="font-bold text-white text-sm">Configure ED Resources & Beds</span>
              <button onClick={() => setShowConfigModal(false)} className="text-slate-500 hover:text-white text-base font-bold">×</button>
            </div>

            {/* Bed counts */}
            <div className="space-y-2">
              <p className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">Bed Counts</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">General Beds</label>
                  <input
                    type="number"
                    min={0}
                    value={generalBedsTotal}
                    onChange={(e) => setGeneralBedsTotal(parseInt(e.target.value) || 0)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Critical Care Beds</label>
                  <input
                    type="number"
                    min={0}
                    value={criticalBedsTotal}
                    onChange={(e) => setCriticalBedsTotal(parseInt(e.target.value) || 0)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-white"
                  />
                </div>
              </div>
              <p className="text-[10px] text-slate-500">
                Lowering a count removes empty beds only — occupied beds are never removed automatically.
              </p>
            </div>

            {/* Staff / equipment counts */}
            <div className="space-y-3 border-t border-slate-800 pt-3">
              <p className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">Staff & Equipment</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">Total Doctors</label>
                  <input type="number" value={docTotal} onChange={(e) => setDocTotal(parseInt(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-white" />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Active Doctors</label>
                  <input type="number" value={docActive} onChange={(e) => setDocActive(parseInt(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-white" />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Total Nurses</label>
                  <input type="number" value={nurseTotal} onChange={(e) => setNurseTotal(parseInt(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-white" />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Active Nurses</label>
                  <input type="number" value={nurseActive} onChange={(e) => setNurseActive(parseInt(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-white" />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Total Ventilators</label>
                  <input type="number" value={ventTotal} onChange={(e) => setVentTotal(parseInt(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-white" />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Active Ventilators</label>
                  <input type="number" value={ventActive} onChange={(e) => setVentActive(parseInt(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-white" />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Total Monitors</label>
                  <input type="number" value={monTotal} onChange={(e) => setMonTotal(parseInt(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-white" />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Active Monitors</label>
                  <input type="number" value={monActive} onChange={(e) => setMonActive(parseInt(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-white" />
                </div>
              </div>
            </div>

            <div className="flex gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setShowConfigModal(false)}
                className="flex-1 py-1.5 bg-slate-800 hover:bg-slate-750 border border-slate-700 text-white font-semibold rounded text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveResources}
                className="flex-1 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded text-xs"
              >
                Save Configuration
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
