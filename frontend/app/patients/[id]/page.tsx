'use client';
import { useParams } from 'next/navigation';
import { usePatient } from '@/hooks/usePatient';
import { useAudit } from '@/hooks/useAudit';
import { PriorityBadge } from '@/components/queue/PriorityBadge';
import { WaitTimeBadge } from '@/components/queue/WaitTimeBadge';
import { AlertTriangle, TrendingDown, User, Clock, Activity, Shield, Brain, ChevronLeft } from 'lucide-react';
import { formatWaitTime, formatDateTime, formatDateTimeFull, formatSymptom, getAgeGroupLabel } from '@/lib/formatters';
import { RECOMMENDED_ACTION_LABELS, EVENT_TYPE_LABELS } from '@/lib/constants';
import { useState } from 'react';
import { api } from '@/lib/api';
import Link from 'next/link';
import { cn } from '@/lib/utils';

function VitalCard({ label, value, unit, abnormal }: { label: string; value: number | null; unit: string; abnormal?: boolean }) {
  return (
    <div className={cn('border rounded-lg p-3', abnormal ? 'border-red-300 bg-red-50' : 'border-slate-200 bg-white')}>
      <p className="text-xs text-slate-500 font-medium">{label}</p>
      <p className={cn('text-xl font-bold mt-1', abnormal ? 'text-red-700' : 'text-slate-800')}>
        {value ?? '—'}
        <span className="text-xs font-normal text-slate-400 ml-1">{unit}</span>
      </p>
      {abnormal && <p className="text-xs text-red-600 font-medium mt-0.5">⚠ Abnormal</p>}
    </div>
  );
}

function OverrideDialog({ patient, assessment, onClose, onSuccess }: {
  patient: { id: string; name: string };
  assessment: { id: string; priority: string };
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [newPriority, setNewPriority] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit() {
    if (!newPriority || !reason.trim()) { setError('Priority and reason are required'); return; }
    setLoading(true);
    try {
      await api.overridePatient({
        patientId: patient.id,
        assessmentId: assessment.id,
        newPriority,
        reason,
        clinicianId: 'CLINICIAN_DEMO',
      });
      onSuccess();
      onClose();
    } catch (e) {
      setError('Override failed. Check backend connection.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <h2 className="text-lg font-bold text-slate-800 mb-1">Clinician Override</h2>
        <p className="text-xs text-slate-500 mb-4">Overriding AI recommendation for {patient.name}</p>

        <div className="space-y-3">
          <div>
            <p className="text-xs font-medium text-slate-600 mb-1">AI Recommendation</p>
            <PriorityBadge priority={assessment.priority as any} size="lg" />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-600 block mb-1">New Priority</label>
            <select
              value={newPriority}
              onChange={e => setNewPriority(e.target.value)}
              className="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select priority...</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MODERATE">MODERATE</option>
              <option value="LOW">LOW</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-600 block mb-1">Clinical Reason</label>
            <textarea
              value={reason}
              onChange={e => setReason(e.target.value)}
              placeholder="Reason for override..."
              rows={3}
              className="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>

          {error && <p className="text-xs text-red-600">{error}</p>}
        </div>

        <div className="flex gap-2 mt-4">
          <button onClick={onClose} className="flex-1 px-4 py-2 border border-slate-300 rounded text-sm text-slate-700 hover:bg-slate-50">Cancel</button>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded text-sm font-semibold hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Saving...' : 'Confirm Override'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: patient, loading, refetch } = usePatient(id);
  const { data: auditData } = useAudit(id);
  const [showOverride, setShowOverride] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [simMessage, setSimMessage] = useState('');

  const waitMinutes = patient ? (Date.now() - new Date(patient.arrivalTime).getTime()) / 60000 : 0;

  async function handleDeterioration() {
    if (!patient) return;
    setSimulating(true);
    setSimMessage('');
    try {
      const result = await api.simulateDeterioration(patient.id);
      await refetch();
      setSimMessage(`Deterioration simulated → ${(result as any).newPriority}`);
    } catch {
      setSimMessage('Simulation failed (check backend)');
    } finally {
      setSimulating(false);
    }
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="space-y-4">
          <div className="h-24 bg-slate-100 rounded-lg animate-pulse" />
          <div className="grid grid-cols-3 gap-4">
            {[1,2,3].map(i => <div key={i} className="h-20 bg-slate-100 rounded-lg animate-pulse" />)}
          </div>
        </div>
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="p-6 text-center">
        <p className="text-slate-500">Patient not found</p>
        <Link href="/patients" className="text-blue-600 hover:underline text-sm mt-2 block">← Back to patients</Link>
      </div>
    );
  }

  const assessment = patient.latestAssessment;
  const vitals = patient.latestVitals;

  return (
    <div className="p-6 space-y-5 max-w-5xl">
      {/* Back nav */}
      <Link href="/patients" className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700">
        <ChevronLeft className="h-3.5 w-3.5" /> Back to Patients
      </Link>

      {/* Patient Header */}
      <div className="bg-white border border-slate-200 rounded-lg p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="h-12 w-12 bg-slate-100 rounded-full flex items-center justify-center">
              <User className="h-6 w-6 text-slate-400" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-bold text-slate-800">{patient.name}</h1>
                <span className="text-sm text-slate-400 font-mono">{patient.id}</span>
                {assessment?.deteriorating && (
                  <span className="inline-flex items-center gap-1 text-xs font-bold text-red-600 bg-red-50 border border-red-200 px-2 py-1 rounded">
                    <TrendingDown className="h-3.5 w-3.5" /> DETERIORATING
                  </span>
                )}
              </div>
              <p className="text-sm text-slate-600">{patient.age} years • {patient.gender} • {assessment ? getAgeGroupLabel(assessment.ageGroup) : ''}</p>
              <p className="text-sm font-medium text-slate-700 mt-1">Chief complaint: {patient.chiefComplaint}</p>
              <div className="flex items-center gap-4 mt-2">
                <span className="flex items-center gap-1 text-xs text-slate-500">
                  <Clock className="h-3.5 w-3.5" /> Arrived {formatDateTime(patient.arrivalTime)}
                </span>
                <WaitTimeBadge minutes={waitMinutes} />
                <span className={cn(
                  'text-xs px-2 py-0.5 rounded font-medium',
                  patient.status === 'WAITING' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
                )}>{patient.status.replace('_', ' ')}</span>
              </div>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            {assessment && <PriorityBadge priority={assessment.priority} size="lg" />}
            <div className="flex gap-2">
              {patient.id === 'P009' && (
                <button
                  onClick={handleDeterioration}
                  disabled={simulating}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-orange-500 text-white text-xs font-semibold rounded hover:bg-orange-600 disabled:opacity-50"
                >
                  <TrendingDown className="h-3.5 w-3.5" />
                  {simulating ? 'Simulating...' : 'Simulate Deterioration'}
                </button>
              )}
              {assessment && (
                <button
                  onClick={() => setShowOverride(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded hover:bg-blue-700"
                >
                  <Shield className="h-3.5 w-3.5" /> Override
                </button>
              )}
            </div>
          </div>
        </div>
        {simMessage && (
          <div className="mt-3 text-xs text-blue-700 bg-blue-50 border border-blue-200 rounded p-2">
            ✓ {simMessage}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left: AI Assessment */}
        <div className="lg:col-span-2 space-y-4">

          {/* Risk + Safety + Confidence */}
          {assessment && (
            <div className="bg-white border border-slate-200 rounded-lg p-5">
              <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4 flex items-center gap-2">
                <Brain className="h-3.5 w-3.5" /> AI Recommendation
              </h2>
              <p className="text-xs text-slate-400 mb-3">Clinical Decision Support — Clinician review required</p>

              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="border border-slate-200 rounded-lg p-3 text-center">
                  <p className="text-xs text-slate-500 mb-1">Recommended Priority</p>
                  <PriorityBadge priority={assessment.priority} size="lg" />
                  {assessment.safetyFloor && assessment.safetyFloor !== assessment.priority && (
                    <p className="text-xs text-red-600 mt-1">Safety floor: {assessment.safetyFloor}</p>
                  )}
                </div>
                <div className="border border-slate-200 rounded-lg p-3 text-center">
                  <p className="text-xs text-slate-500 mb-1">Risk Score</p>
                  <p className="text-2xl font-bold text-slate-800">{Math.round(assessment.riskScore)}</p>
                  <p className="text-xs text-slate-400">out of 100</p>
                </div>
                <div className="border border-slate-200 rounded-lg p-3 text-center">
                  <p className="text-xs text-slate-500 mb-1">Confidence</p>
                  <p className="text-2xl font-bold text-slate-800">{Math.round(assessment.confidence * 100)}%</p>
                  <p className="text-xs text-slate-400">{assessment.confidence >= 0.75 ? 'HIGH' : assessment.confidence >= 0.5 ? 'MODERATE' : 'LOW'}</p>
                </div>
              </div>

              {/* Recommended action */}
              <div className="bg-slate-50 border border-slate-200 rounded p-3 mb-4">
                <p className="text-xs text-slate-500 mb-0.5">Recommended Action</p>
                <p className="text-sm font-semibold text-slate-700">
                  {RECOMMENDED_ACTION_LABELS[assessment.recommendedAction] || assessment.recommendedAction}
                </p>
              </div>

              {/* Safety flags */}
              {assessment.safetyFlags.length > 0 && (
                <div className="border border-red-200 bg-red-50 rounded p-3 mb-4">
                  <p className="text-xs font-semibold text-red-700 mb-2 flex items-center gap-1">
                    <AlertTriangle className="h-3.5 w-3.5" /> Safety Flags
                  </p>
                  <div className="space-y-1">
                    {assessment.safetyFlags.map(flag => (
                      <p key={flag} className="text-xs text-red-700">🚨 {flag.replace(/_/g, ' ')}</p>
                    ))}
                  </div>
                </div>
              )}

              {/* Reasons */}
              {assessment.reasons.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-slate-600 mb-2">Why this recommendation?</p>
                  <div className="space-y-1.5">
                    {assessment.reasons.map((reason, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <span className="text-blue-500 mt-0.5 flex-shrink-0">›</span>
                        <p className="text-xs text-slate-600">{reason.message}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Vitals */}
          {vitals && (
            <div className="bg-white border border-slate-200 rounded-lg p-5">
              <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4 flex items-center gap-2">
                <Activity className="h-3.5 w-3.5" /> Current Vitals
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <VitalCard label="Heart Rate" value={vitals.heartRate} unit="bpm"
                  abnormal={!!(vitals.heartRate && (vitals.heartRate > 100 || vitals.heartRate < 55))} />
                <VitalCard label="Blood Pressure" value={vitals.systolicBp} unit={`/${vitals.diastolicBp || '?'} mmHg`}
                  abnormal={!!(vitals.systolicBp && vitals.systolicBp < 100)} />
                <VitalCard label="SpO₂" value={vitals.spo2} unit="%"
                  abnormal={!!(vitals.spo2 && vitals.spo2 < 95)} />
                <VitalCard label="Temperature" value={vitals.temperature} unit="°C"
                  abnormal={!!(vitals.temperature && (vitals.temperature > 38.5 || vitals.temperature < 36))} />
                <VitalCard label="Respiratory Rate" value={vitals.respiratoryRate} unit="/min"
                  abnormal={!!(vitals.respiratoryRate && vitals.respiratoryRate > 20)} />
              </div>
              <p className="text-xs text-slate-400 mt-3">Recorded at {formatDateTime(vitals.timestamp)}</p>
              <p className="text-xs text-slate-400">⚕ Abnormal indicators are for display only. Clinical assessment is performed by the backend engine.</p>
            </div>
          )}
        </div>

        {/* Right: Patient info + Timeline */}
        <div className="space-y-4">
          {/* Medical History */}
          <div className="bg-white border border-slate-200 rounded-lg p-4">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Medical History</h3>
            {!patient.historyAvailable ? (
              <div className="bg-amber-50 border border-amber-200 rounded p-2">
                <p className="text-xs font-semibold text-amber-700">⚠ History unavailable</p>
                <p className="text-xs text-amber-600 mt-0.5">Confidence is reduced. Conservative assessment applied.</p>
              </div>
            ) : patient.medicalHistory && patient.medicalHistory.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {patient.medicalHistory.map(h => (
                  <span key={h} className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                    {formatSymptom(h)}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400">No significant medical history</p>
            )}
          </div>

          {/* Symptoms */}
          <div className="bg-white border border-slate-200 rounded-lg p-4">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Reported Symptoms</h3>
            {patient.symptoms.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {patient.symptoms.map(s => (
                  <span key={s} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded border border-blue-100">
                    {formatSymptom(s)}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400">None specified</p>
            )}
          </div>

          {/* Audit Timeline */}
          {auditData && auditData.events.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Timeline</h3>
              <div className="space-y-3">
                {auditData.events.slice(0, 8).map((event, i) => (
                  <div key={event.id} className="flex items-start gap-2">
                    <div className="flex flex-col items-center">
                      <div className="h-2 w-2 rounded-full bg-blue-400 flex-shrink-0 mt-1" />
                      {i < auditData.events.length - 1 && <div className="w-px h-6 bg-slate-200 mt-1" />}
                    </div>
                    <div>
                      <p className="text-xs font-medium text-slate-700">
                        {EVENT_TYPE_LABELS[event.eventType] || event.eventType}
                      </p>
                      <p className="text-xs text-slate-400">{formatDateTimeFull(event.createdAt)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Clinician actions */}
          {assessment && (
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Clinician Actions</h3>
              <p className="text-xs text-slate-400 mb-3">AI recommendation requires clinician review. Final decision remains with clinician.</p>
              <div className="space-y-2">
                <button className="w-full px-3 py-2 bg-green-600 text-white text-xs font-semibold rounded hover:bg-green-700 transition-colors">
                  ✓ Accept Recommendation
                </button>
                <button
                  onClick={() => setShowOverride(true)}
                  className="w-full px-3 py-2 border border-blue-300 text-blue-700 text-xs font-semibold rounded hover:bg-blue-50 transition-colors"
                >
                  Override Priority
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Override Dialog */}
      {showOverride && assessment && (
        <OverrideDialog
          patient={{ id: patient.id, name: patient.name }}
          assessment={{ id: assessment.id, priority: assessment.priority }}
          onClose={() => setShowOverride(false)}
          onSuccess={refetch}
        />
      )}
    </div>
  );
}
