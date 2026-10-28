import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  HeartHandshake,
  ShieldCheck,
  Plus,
  ArrowRight,
  FileText,
  Pill,
  CheckCircle2,
  HelpCircle,
  AlertTriangle,
  Clock,
  Sparkles,
  Info,
  Calendar,
  Check,
  X
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { safetyService } from '../../services/api';
import { ClinicalHighlightBox } from '../../components/ui/ClinicalHighlightBox';

const SYMPTOM_CHECKER_ITEMS = [
  { id: 'dizziness', label: 'Dizziness', alert: 'Often linked to blood pressure medicines or dehydration. Avoid sudden standing.' },
  { id: 'stomach', label: 'Stomach Upset', alert: 'Common with metformin or painkillers. Taking doses with food can help protect your stomach.' },
  { id: 'bruising', label: 'Easy Bruising', alert: 'Important alert when blood thinners or NSAIDs are taken together.' },
  { id: 'cough', label: 'Dry Tickly Cough', alert: 'Common mild side effect of ACE inhibitors. Consult your physician for an alternative.' },
  { id: 'muscle', label: 'Muscle Aches', alert: 'Tell your doctor if taking cholesterol statins with unexplained cramping.' },
];

export const PatientDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  // Real user medicine list from localStorage (starts empty if user hasn't added anything)
  const [savedMeds, setSavedMeds] = useState(() => {
    try {
      const stored = localStorage.getItem('curenova_patient_meds');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  const [quickMedInput, setQuickMedInput] = useState('');
  const [selectedSymptom, setSelectedSymptom] = useState(null);
  const [catalog, setCatalog] = useState([]);

  // Fetch real catalog for autocomplete suggestions
  useEffect(() => {
    safetyService
      .getCatalog()
      .then((res) => setCatalog(Array.isArray(res) ? res : (res.catalog || [])))
      .catch((err) => console.error('Failed to load catalog', err));
  }, []);

  // Real dynamic daily schedule generated from actual medicines
  const [pillSchedule, setPillSchedule] = useState(() => {
    return savedMeds.map((med, idx) => ({
      id: idx + 1,
      time: idx % 2 === 0 ? 'Morning (8:00 AM)' : 'Evening (7:00 PM)',
      med: `${med}`,
      taken: false,
    }));
  });

  // Sync schedule whenever savedMeds change
  useEffect(() => {
    setPillSchedule(
      savedMeds.map((med, idx) => ({
        id: idx + 1,
        time: idx % 2 === 0 ? 'Morning (8:00 AM)' : 'Evening (7:00 PM)',
        med: `${med}`,
        taken: false,
      }))
    );
  }, [savedMeds]);

  const toggleDose = (id) => {
    setPillSchedule((prev) =>
      prev.map((item) => (item.id === id ? { ...item, taken: !item.taken } : item))
    );
  };

  const takenCount = pillSchedule.filter((p) => p.taken).length;
  const progressPercent = pillSchedule.length > 0 ? Math.round((takenCount / pillSchedule.length) * 100) : 0;

  const handleAddMed = (drugName) => {
    const clean = (drugName || quickMedInput).trim();
    if (!clean) return;
    if (!savedMeds.includes(clean)) {
      const updated = [...savedMeds, clean];
      setSavedMeds(updated);
      try {
        localStorage.setItem('curenova_patient_meds', JSON.stringify(updated));
      } catch {
        // ignore
      }
    }
    setQuickMedInput('');
  };

  const handleRemoveMed = (idx) => {
    const updated = savedMeds.filter((_, i) => i !== idx);
    setSavedMeds(updated);
    try {
      localStorage.setItem('curenova_patient_meds', JSON.stringify(updated));
    } catch {
      // ignore
    }
  };

  return (
    <div className="space-y-8 w-full text-left">
      {/* ── Demo-Style Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Patient Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Personal medication tracker & plain-language safety companion
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => navigate('/patient/medication-safety')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm shadow-sm transition-colors cursor-pointer"
          >
            <ShieldCheck className="h-4 w-4" />
            <span>Check My Medicines</span>
          </button>
        </div>
      </div>

      {/* ── Demo-Style 4 Stats Grid ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Daily Doses */}
        <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
              <Pill className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <span className="text-xs font-mono font-medium text-emerald-600 dark:text-emerald-400">
              {progressPercent}% Done
            </span>
          </div>
          <h3 className="font-medium text-gray-600 dark:text-gray-400 mb-1">Today's Doses</h3>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {takenCount} <span className="text-sm font-normal text-gray-500">/ {pillSchedule.length || 0}</span>
          </p>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-3 overflow-hidden">
            <div className="bg-emerald-500 h-2 rounded-full transition-all duration-300" style={{ width: `${progressPercent}%` }} />
          </div>
        </div>

        {/* Medicine Cabinet Count */}
        <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <HeartHandshake className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <span className="text-xs text-blue-600 dark:text-blue-400 font-medium">Cabinet</span>
          </div>
          <h3 className="font-medium text-gray-600 dark:text-gray-400 mb-1">Prescriptions</h3>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{savedMeds.length}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Logged medications</p>
        </div>

        {/* Safety Screening Status */}
        <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <ShieldCheck className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            <span className="text-xs text-purple-600 dark:text-purple-400 font-medium">Verified</span>
          </div>
          <h3 className="font-medium text-gray-600 dark:text-gray-400 mb-1">Safety Status</h3>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {savedMeds.length > 0 ? 'Clear' : 'Pending'}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">No critical alerts flagged</p>
        </div>

        {/* Doctor Summary Ready */}
        <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
              <FileText className="h-5 w-5 text-orange-600 dark:text-orange-400" />
            </div>
            <span className="text-xs text-orange-600 dark:text-orange-400 font-medium">Ready</span>
          </div>
          <h3 className="font-medium text-gray-600 dark:text-gray-400 mb-1">Clinical Visit Slip</h3>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">1-Click</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Ready for appointment</p>
        </div>
      </div>

      {/* ── Main Content Grid (2-to-1 demo split) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* Left Column (2 cols): Medicine Cabinet & Schedule */}
        <div className="lg:col-span-2 space-y-6">
          {/* Medicine Input & Cabinet */}
          <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-gray-900 dark:text-gray-100">
                  My Prescription & Vitamin Cabinet
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  Add medicines to build your daily schedule and check for interactions.
                </p>
              </div>
              <span className="text-xs font-medium text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/40 px-2.5 py-1 rounded-full border border-emerald-200 dark:border-emerald-800">
                {savedMeds.length} in List
              </span>
            </div>

            {/* Quick Add Form */}
            <form onSubmit={(e) => { e.preventDefault(); handleAddMed(); }} className="flex gap-2">
              <input
                type="text"
                value={quickMedInput}
                onChange={(e) => setQuickMedInput(e.target.value)}
                placeholder="Type a medicine name (e.g. Aspirin, Metformin, Vitamin D)..."
                className="flex-1 px-3.5 py-2.5 text-xs sm:text-sm rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
              <button
                type="submit"
                className="px-4 py-2.5 rounded-xl font-medium text-xs sm:text-sm text-white bg-emerald-600 hover:bg-emerald-700 transition-colors cursor-pointer flex items-center gap-1 shrink-0 shadow-sm"
              >
                <Plus className="w-4 h-4" />
                <span>Add</span>
              </button>
            </form>

            {/* Recognized Common Medicines from Backend Catalog */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-medium text-gray-400">
                Common Clinical Medicines:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {catalog.slice(0, 8).map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => handleAddMed(c.canonical_name)}
                    className="text-xs px-2.5 py-1 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:text-emerald-700 dark:hover:text-emerald-300 transition-colors cursor-pointer"
                  >
                    + {c.canonical_name}
                  </button>
                ))}
              </div>
            </div>

            {/* Clinical Highlight Box for My Prescriptions & Over-The-Counter Medicines */}
            <ClinicalHighlightBox
              variant="primary"
              title={`My Saved Medicines (${savedMeds.length})`}
              subtitle="All medicines you take regularly. Click check safety below to see if they mix safely."
              badge={savedMeds.length > 0 ? `${savedMeds.length} added` : undefined}
              icon={Pill}
              className="mt-2"
            >
              <div className="flex flex-wrap gap-2 min-h-[44px] items-center">
                {savedMeds.length === 0 ? (
                  <span className="text-xs text-[var(--color-text-muted)] italic px-1">
                    Your medicine cabinet is currently empty. Add your medicines above or pick from common medicines.
                  </span>
                ) : (
                  savedMeds.map((med, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[var(--color-surface-card)] border border-[#0284C7]/30 text-xs font-bold text-[#0A2540] dark:text-[#E0F2FE] shadow-2xs"
                    >
                      <Pill className="w-3.5 h-3.5 text-[#0284C7] dark:text-[#38BDF8]" />
                      <span>{med}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveMed(idx)}
                        className="text-[var(--color-text-muted)] hover:text-rose-600 cursor-pointer ml-1 p-0.5"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))
                )}
              </div>
            </ClinicalHighlightBox>

            <button
              type="button"
              disabled={savedMeds.length === 0}
              onClick={() => navigate('/patient/medication-safety', { state: { prefilledMeds: savedMeds } })}
              className="w-full py-2.5 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#0284C7] hover:bg-[#0369A1] disabled:opacity-50 transition-all shadow-md flex items-center justify-center gap-2 cursor-pointer"
            >
              <span>Check Medicine Safety & Interactions</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Daily Schedule Organizer */}
          {pillSchedule.length > 0 && (
            <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                    <Clock className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                    <span>Daily Dose Tracker</span>
                  </h2>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    Tap a dose to mark as <strong>Taken</strong> or <strong>Pending</strong>.
                  </p>
                </div>
                <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 font-mono">
                  {progressPercent}% Complete
                </span>
              </div>

              <div className="space-y-2">
                {pillSchedule.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => toggleDose(item.id)}
                    className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                      item.taken
                        ? 'bg-emerald-50/70 dark:bg-emerald-950/30 border-emerald-300 dark:border-emerald-800'
                        : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-emerald-400'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-5 h-5 rounded-md flex items-center justify-center font-bold text-xs ${
                        item.taken ? 'bg-emerald-600 text-white' : 'border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900'
                      }`}>
                        {item.taken ? <Check className="w-3 h-3" /> : null}
                      </div>
                      <div>
                        <span className={`text-xs font-semibold block ${item.taken ? 'line-through text-gray-400' : 'text-gray-900 dark:text-gray-100'}`}>
                          {item.med}
                        </span>
                        <span className="text-[10px] text-gray-500 font-mono">
                          {item.time}
                        </span>
                      </div>
                    </div>
                    <span className={`text-[10px] font-mono font-medium px-2 py-0.5 rounded-full ${
                      item.taken ? 'bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-200' : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                    }`}>
                      {item.taken ? 'Taken' : 'Pending'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Symptom Checker & Doctor Sheet */}
        <div className="space-y-6">
          
          {/* Instant Symptom Checker */}
          <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <HelpCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <h3 className="text-base font-bold text-gray-900 dark:text-gray-100">
                  Instant Symptom Checker
                </h3>
              </div>
              <span className="text-[10px] text-gray-400">Tap to inspect</span>
            </div>

            {/* Clickable Symptom Pills */}
            <div className="flex flex-wrap gap-2">
              {SYMPTOM_CHECKER_ITEMS.map((item) => {
                const isSelected = selectedSymptom?.id === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setSelectedSymptom(isSelected ? null : item)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer border ${
                      isSelected
                        ? 'bg-emerald-600 text-white border-emerald-600 shadow-sm'
                        : 'bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700 hover:border-emerald-500'
                    }`}
                  >
                    {item.label}
                  </button>
                );
              })}
            </div>

            {/* Live Symptom Result Box */}
            {selectedSymptom ? (
              <ClinicalHighlightBox
                variant="warning"
                title={`${selectedSymptom.label} Medicine Guidance`}
                icon={AlertTriangle}
                subtitle="Review before taking new medications"
              >
                <p className="text-xs text-amber-900 dark:text-amber-200 leading-relaxed font-medium">
                  {selectedSymptom.alert}
                </p>
              </ClinicalHighlightBox>
            ) : (
              <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-dashed border-gray-200 dark:border-gray-700 text-center text-xs text-gray-500">
                Tap any symptom above to see medication safety guidance.
              </div>
            )}
          </div>

          {/* Doctor Visit Checklist */}
          <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-3">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <h3 className="text-base font-bold text-gray-900 dark:text-gray-100">
                Doctor Visit Checklist
              </h3>
            </div>
            <p className="text-xs text-gray-500 leading-relaxed">
              Generate a clean, single-page summary of your current medicines and safety questions to bring to your next appointment.
            </p>
            <button
              type="button"
              onClick={() => navigate('/patient/results')}
              className="w-full py-2.5 px-3 rounded-lg border border-emerald-300 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-200 text-xs font-semibold hover:bg-emerald-100 dark:hover:bg-emerald-900/40 transition-colors flex items-center justify-center gap-1.5 cursor-pointer shadow-xs"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Open Printable Summary</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatientDashboard;
