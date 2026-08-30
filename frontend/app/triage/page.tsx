'use client';
import { useState } from 'react';
import { useTriage } from '@/hooks/useTriage';
import { PriorityBadge } from '@/components/queue/PriorityBadge';
import { RECOMMENDED_ACTION_LABELS } from '@/lib/constants';
import { AlertTriangle } from 'lucide-react';
import Link from 'next/link';

const COMMON_SYMPTOMS = [
  'chest_pain', 'shortness_of_breath', 'weakness', 'confusion',
  'fever', 'headache', 'nausea', 'vomiting', 'abdominal_pain',
  'back_pain', 'dizziness', 'palpitations', 'fatigue',
  'altered_mental_status', 'syncope', 'loss_of_consciousness'
];

export default function TriagePage() {
  const { result, loading, error, submitTriage, reset } = useTriage();
  const [form, setForm] = useState({
    name: '', age: '', gender: 'male', chiefComplaint: '',
    symptoms: [] as string[], historyAvailable: true,
    medicalHistory: '',
    heartRate: '', systolicBp: '', diastolicBp: '',
    spo2: '', temperature: '', respiratoryRate: ''
  });

  function toggleSymptom(s: string) {
    setForm(f => ({ ...f, symptoms: f.symptoms.includes(s) ? f.symptoms.filter(x => x !== s) : [...f.symptoms, s] }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.age || !form.chiefComplaint) return;
    await submitTriage({
      name: form.name || undefined,
      age: parseInt(form.age),
      gender: form.gender,
      chiefComplaint: form.chiefComplaint,
      symptoms: form.symptoms,
      historyAvailable: form.historyAvailable,
      medicalHistory: form.medicalHistory ? form.medicalHistory.split(',').map(s => s.trim()).filter(Boolean) : undefined,
      vitals: {
        heartRate: form.heartRate ? parseFloat(form.heartRate) : undefined,
        systolicBp: form.systolicBp ? parseFloat(form.systolicBp) : undefined,
        diastolicBp: form.diastolicBp ? parseFloat(form.diastolicBp) : undefined,
        spo2: form.spo2 ? parseFloat(form.spo2) : undefined,
        temperature: form.temperature ? parseFloat(form.temperature) : undefined,
        respiratoryRate: form.respiratoryRate ? parseFloat(form.respiratoryRate) : undefined,
      }
    });
  }

  const inputClass = 'w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500';
  const labelClass = 'text-xs font-medium text-slate-600 block mb-1';

  return (
    <div className="p-6">
      <div className="mb-5">
        <h1 className="text-lg font-bold text-slate-800">Patient Triage</h1>
        <p className="text-xs text-slate-400">Enter patient information for AI-assisted triage assessment</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <form onSubmit={handleSubmit} className="space-y-5">

          {/* Patient Info */}
          <div className="bg-white border border-slate-200 rounded-lg p-5">
            <h2 className="text-sm font-semibold text-slate-700 mb-4">Patient Information</h2>
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <label className={labelClass}>Name (optional)</label>
                <input value={form.name} onChange={e => setForm(f => ({...f, name: e.target.value}))} className={inputClass} placeholder="Patient name" />
              </div>
              <div>
                <label className={labelClass}>Age *</label>
                <input type="number" min="0" max="150" required value={form.age} onChange={e => setForm(f => ({...f, age: e.target.value}))} className={inputClass} placeholder="Years" />
              </div>
              <div>
                <label className={labelClass}>Gender</label>
                <select value={form.gender} onChange={e => setForm(f => ({...f, gender: e.target.value}))} className={inputClass}>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="col-span-2">
                <label className={labelClass}>Chief Complaint *</label>
                <input required value={form.chiefComplaint} onChange={e => setForm(f => ({...f, chiefComplaint: e.target.value}))} className={inputClass} placeholder="Primary reason for visit" />
              </div>
            </div>
          </div>

          {/* Symptoms */}
          <div className="bg-white border border-slate-200 rounded-lg p-5">
            <h2 className="text-sm font-semibold text-slate-700 mb-3">Symptoms</h2>
            <div className="flex flex-wrap gap-2">
              {COMMON_SYMPTOMS.map(s => (
                <button type="button" key={s} onClick={() => toggleSymptom(s)}
                  className={`text-xs px-2.5 py-1 rounded border transition-colors ${
                    form.symptoms.includes(s) ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-slate-600 border-slate-300 hover:border-blue-300'
                  }`}>
                  {s.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* History */}
          <div className="bg-white border border-slate-200 rounded-lg p-5">
            <h2 className="text-sm font-semibold text-slate-700 mb-3">Medical History</h2>
            <label className="flex items-center gap-2 mb-3 cursor-pointer">
              <input type="checkbox" checked={form.historyAvailable} onChange={e => setForm(f => ({...f, historyAvailable: e.target.checked}))} className="rounded" />
              <span className="text-sm text-slate-700">History available</span>
            </label>
            {form.historyAvailable && (
              <div>
                <label className={labelClass}>Known conditions (comma-separated)</label>
                <input value={form.medicalHistory} onChange={e => setForm(f => ({...f, medicalHistory: e.target.value}))} className={inputClass} placeholder="e.g. hypertension, diabetes" />
              </div>
            )}
          </div>

          {/* Vitals */}
          <div className="bg-white border border-slate-200 rounded-lg p-5">
            <h2 className="text-sm font-semibold text-slate-700 mb-4">Vitals</h2>
            <div className="grid grid-cols-2 gap-3">
              {[
                { key: 'heartRate', label: 'Heart Rate', placeholder: 'bpm', min: 0, max: 300 },
                { key: 'systolicBp', label: 'Systolic BP', placeholder: 'mmHg', min: 0, max: 300 },
                { key: 'diastolicBp', label: 'Diastolic BP', placeholder: 'mmHg', min: 0, max: 200 },
                { key: 'spo2', label: 'SpO₂', placeholder: '%', min: 0, max: 100 },
                { key: 'temperature', label: 'Temperature', placeholder: '°C', min: 30, max: 45 },
                { key: 'respiratoryRate', label: 'Respiratory Rate', placeholder: '/min', min: 0, max: 100 },
              ].map(f => (
                <div key={f.key}>
                  <label className={labelClass}>{f.label}</label>
                  <input
                    type="number" step="0.1" min={f.min} max={f.max}
                    value={(form as any)[f.key]}
                    onChange={e => setForm(prev => ({...prev, [f.key]: e.target.value}))}
                    className={inputClass}
                    placeholder={f.placeholder}
                  />
                </div>
              ))}
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded p-3">
              <p className="text-xs text-red-600 flex items-center gap-1"><AlertTriangle className="h-3.5 w-3.5" /> {error}</p>
            </div>
          )}

          <button type="submit" disabled={loading}
            className="w-full py-3 bg-blue-600 text-white font-bold rounded hover:bg-blue-700 disabled:opacity-50 transition-colors">
            {loading ? 'Assessing...' : 'ASSESS PATIENT'}
          </button>
          <p className="text-xs text-slate-400 text-center">AI recommendation requires clinician review</p>
        </form>

        {/* Result panel */}
        {result && (
          <div className="space-y-4">
            <div className="bg-white border-2 border-slate-200 rounded-lg p-5">
              <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-4">AI Assessment Result</h2>
              <p className="text-xs text-slate-400 mb-4">Clinical Decision Support — Not a diagnosis</p>

              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="text-center border border-slate-200 rounded p-3">
                  <p className="text-xs text-slate-500 mb-1">Priority</p>
                  <PriorityBadge priority={result.priority} size="lg" />
                </div>
                <div className="text-center border border-slate-200 rounded p-3">
                  <p className="text-xs text-slate-500 mb-1">Risk Score</p>
                  <p className="text-2xl font-bold">{Math.round(result.riskScore)}</p>
                </div>
                <div className="text-center border border-slate-200 rounded p-3">
                  <p className="text-xs text-slate-500 mb-1">Confidence</p>
                  <p className="text-2xl font-bold">{Math.round(result.confidence * 100)}%</p>
                </div>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded p-3 mb-4">
                <p className="text-xs text-slate-500 mb-0.5">Recommended Action</p>
                <p className="text-sm font-semibold text-slate-700">{RECOMMENDED_ACTION_LABELS[result.recommendedAction] || result.recommendedAction}</p>
              </div>

              {result.safetyFlags.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded p-3 mb-4">
                  <p className="text-xs font-semibold text-red-700 mb-2">⚠ Safety Flags</p>
                  {result.safetyFlags.map(f => <p key={f} className="text-xs text-red-700">🚨 {f.replace(/_/g, ' ')}</p>)}
                </div>
              )}

              {result.reasons.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs font-semibold text-slate-600 mb-2">Why this recommendation?</p>
                  {result.reasons.slice(0, 5).map((r, i) => (
                    <p key={i} className="text-xs text-slate-600 mb-1">› {r.message}</p>
                  ))}
                </div>
              )}

              {result.limitations.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded p-3 mb-4">
                  <p className="text-xs font-semibold text-amber-700 mb-1">⚠ Assessment Limitations</p>
                  {result.limitations.map((l, i) => <p key={i} className="text-xs text-amber-600">• {l}</p>)}
                </div>
              )}

              <Link href={`/patients/${result.patientId}`}
                className="block text-center text-xs text-blue-600 hover:underline border border-blue-200 rounded py-2">
                View Patient Record →
              </Link>

              <button onClick={reset} className="w-full mt-2 text-xs text-slate-400 hover:text-slate-600">
                Assess another patient
              </button>
            </div>
          </div>
        )}

        {!result && (
          <div className="bg-slate-50 border border-dashed border-slate-200 rounded-lg p-8 flex items-center justify-center">
            <div className="text-center">
              <p className="text-slate-400 text-sm">Assessment result will appear here</p>
              <p className="text-slate-300 text-xs mt-1">Fill in patient data and click Assess Patient</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
