import React, { useState } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  AlertTriangle,
  FileText,
  Printer,
  ChevronLeft,
  CheckCircle2,
  ExternalLink,
  BookOpen,
  HelpCircle,
  Stethoscope,
  Activity,
  ArrowRight,
  Pill,
  Share2,
  Zap,
  RefreshCw
} from 'lucide-react';
import { safetyService } from '../../services/api';
import InteractionMatrix from '../../components/InteractionMatrix';
import RiskBadge from '../../components/RiskBadge';
import SafetyDisclaimer from '../../components/SafetyDisclaimer';
import ReportModal from '../../components/ReportModal';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Card, { CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { ClinicalHighlightBox } from '../../components/ui/ClinicalHighlightBox';

export const DoctorResults = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [data, setData] = useState(() => {
    if (location.state?.analysisData) return location.state.analysisData;
    try {
      const history = JSON.parse(localStorage.getItem('curenova_doctor_safety_history') || '[]');
      if (history.length > 0 && history[0].analysisData) {
        return history[0].analysisData;
      }
    } catch {
      // ignore
    }
    return null;
  });

  if (!data) {
    return (
      <div className="max-w-2xl mx-auto py-12 px-4">
        <Card className="p-8 border border-[var(--color-border-subtle)] bg-[var(--color-surface-card)] text-center space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-[var(--color-brand-surface)] border border-[var(--color-brand-border)] text-[var(--color-brand-primary)] flex items-center justify-center mx-auto">
            <Stethoscope className="w-8 h-8" />
          </div>
          <div className="space-y-2">
            <h2 className="text-xl sm:text-2xl font-extrabold text-[var(--color-text-primary)]">
              No Active Polypharmacy Dossier Selected
            </h2>
            <p className="text-xs sm:text-sm text-[var(--color-text-secondary)] max-w-md mx-auto leading-relaxed">
              To evaluate higher-order drug combinations, view pairwise interaction matrices, and inspect openFDA safety citations, enter a medication regimen in the Medication Safety Analyzer.
            </p>
          </div>

          <div className="pt-2 flex flex-col sm:flex-row justify-center gap-3">
            <Button
              variant="primary"
              onClick={() => navigate('/doctor/medication-safety')}
              className="!bg-[#0284C7] hover:!bg-[#0369A1]"
            >
              Start Medication Safety Check
            </Button>
            <Button
              variant="secondary"
              onClick={() => navigate('/doctor/dashboard')}
            >
              Doctor Clinical Dashboard
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  const drugNames = data.normalized_drugs?.map((d) => d.canonical_name) || [];
  const isHighRisk = (data.overall_risk_score ?? 0) >= 65;

  return (
    <div className="space-y-6">
      {/* Top Bar with Navigation and Report Generator */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/doctor/medication-safety"
            className="p-2 rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-card)] hover:bg-[var(--color-surface-hover)] text-[var(--color-text-secondary)] transition-colors cursor-pointer"
            title="Back to Input"
          >
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-[var(--color-text-primary)]">
              Clinical Medication Safety Dossier
            </h1>
            <p className="text-xs text-[var(--color-text-muted)] font-mono">
              Analysis ID: {data.analysis_id} · Grounded in PubMed & openFDA Pharmacovigilance
            </p>
          </div>
        </div>

        <Button
          variant="secondary"
          size="md"
          icon={FileText}
          onClick={() => setReportModalOpen(true)}
        >
          Generate Clinical Report (PDF)
        </Button>
      </div>

      <SafetyDisclaimer variant="compact" />

      {/* Overview Dossier Banner: Critical Hazard treatment if high risk */}
      <Card
        elevation={isHighRisk ? 'critical' : 'raised'}
        className={`p-6 ${isHighRisk ? 'border-l-4 border-l-[#dc2626]' : ''}`}
      >
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <RiskBadge severity={data.overall_risk_category} size="lg" />
              {data.human_review_required && (
                <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-[var(--color-status-critical-bg)] text-[var(--color-status-critical-text)] border border-[var(--color-status-critical-border)]">
                  Human Clinical Review Recommended
                </span>
              )}
            </div>
            <h2 className="text-lg sm:text-xl font-bold text-[var(--color-text-primary)] tracking-tight">
              {data.summary_headline}
            </h2>

            {/* Evaluated Drugs with RxCUI Mono Badges */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-xs text-[var(--color-text-muted)] font-medium">Evaluated Therapies:</span>
              {data.normalized_drugs?.map((d, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)] text-xs font-semibold text-[var(--color-text-primary)]"
                >
                  <Pill className="w-3.5 h-3.5 text-[var(--color-brand-primary)]" />
                  <span>{d.canonical_name}</span>
                  <span className="text-[10px] font-mono text-[var(--color-text-muted)] bg-[var(--color-surface-card)] px-1 py-0.2 rounded border border-[var(--color-border-subtle)]">
                    RxCUI: {d.rxcui}
                  </span>
                </span>
              ))}
            </div>
          </div>

          <div className="sm:text-right shrink-0 border-t sm:border-t-0 border-[var(--color-border-subtle)] pt-3 sm:pt-0">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[var(--color-text-muted)] block">
              Quantified Risk Score
            </span>
            <div className={`text-3xl font-extrabold tabular ${isHighRisk ? 'text-[#dc2626] dark:text-[#f87171]' : 'text-[var(--color-text-primary)]'}`}>
              {data.overall_risk_score}
              <span className="text-sm font-normal text-[var(--color-text-muted)]"> / 100</span>
            </div>
          </div>
        </div>
      </Card>

      {/* Main Grid: Interaction Heatmap & Overlap Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Interaction Matrix Heatmap & Citations */}
        <div className="lg:col-span-8 space-y-6">
          {/* Pairwise Interaction Matrix */}
          <Card elevation="raised" className="p-6">
            <InteractionMatrix drugs={drugNames} matrixCells={data.interaction_matrix || []} />
          </Card>

          {/* Detailed Pairwise Citations & Pharmacokinetic Mechanism Cards */}
          <Card elevation="raised" className="p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--color-border-subtle)] pb-3">
              <div>
                <CardTitle>Detailed Pharmacokinetic Evidence & Citations</CardTitle>
                <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                  Peer-reviewed mechanism breakdown, receptor kinetics, and adverse signal levels
                </p>
              </div>
              <span className="text-xs font-mono font-semibold text-[var(--color-text-muted)] tabular">
                {data.pairwise_interactions?.length || 0} Flagged Pair(s)
              </span>
            </div>

            {(!data.pairwise_interactions || data.pairwise_interactions.length === 0) ? (
              <div className="p-6 rounded-2xl bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)] text-center space-y-3">
                <div className="w-12 h-12 rounded-xl bg-[#E0F2FE] dark:bg-[#0369A1]/20 text-[#0284C7] flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <h4 className="text-sm font-bold text-[var(--color-text-primary)]">
                  No Documented Pairwise Interactions in Reference Database
                </h4>
                <p className="text-xs text-[var(--color-text-secondary)] max-w-lg mx-auto leading-relaxed">
                  The evaluated medication combination does not show recorded adverse interactions or metabolic conflict within the indexed biomedical literature and openFDA post-marketing safety dataset.
                </p>
                <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-200 text-xs font-medium text-left flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-amber-600" />
                  <span className="leading-relaxed">
                    <strong>Scientific Limitation Notice:</strong> An absence of documented interactions does not establish clinical safety. Uncharacterized pharmacokinetic interactions, renal/hepatic clearance status, and patient-specific variables must always be clinically evaluated.
                  </span>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {data.pairwise_interactions?.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-sunken)] space-y-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-[var(--color-text-primary)]">
                          {item.drug_a} ↔ {item.drug_b}
                        </span>
                        <span className="text-xs text-[var(--color-text-muted)] font-mono">
                          ({item.interaction_type})
                        </span>
                      </div>
                      <RiskBadge severity={item.severity} size="sm" />
                    </div>

                    <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed">
                      {item.mechanism}
                    </p>

                    <div className="p-3 rounded-lg bg-[var(--color-surface-card)] border border-[var(--color-brand-border)] text-xs space-y-1">
                      <span className="font-bold text-[var(--color-brand-text)] text-[11px] uppercase tracking-wider block">
                        Clinician Decision Guidance:
                      </span>
                      <p className="text-[var(--color-text-primary)] font-medium leading-relaxed">
                        {item.doctor_guidance}
                      </p>
                    </div>

                    {/* Supporting Literature / Regulatory Alerts */}
                    {item.citations?.length > 0 && (
                      <div className="pt-2 border-t border-[var(--color-border-subtle)] space-y-2">
                        <span className="text-[11px] font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider block">
                          Grounded Sources & Citations:
                        </span>
                        {item.citations.map((cite, cIdx) => (
                          <div
                            key={cIdx}
                            className="text-xs p-3 rounded-lg bg-[var(--color-surface-card)] border border-[var(--color-border-subtle)] space-y-1"
                          >
                            <div className="flex items-center justify-between font-semibold text-[var(--color-text-primary)] text-[11px]">
                              <span>{cite.source}</span>
                              {cite.pmid && (
                                <a
                                  href={`https://pubmed.ncbi.nlm.nih.gov/${cite.pmid}/`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-[var(--color-brand-primary)] hover:underline flex items-center gap-1 font-mono text-[10px] bg-[var(--color-surface-sunken)] px-1.5 py-0.5 rounded border border-[var(--color-border-subtle)]"
                                >
                                  PMID: {cite.pmid} <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                            </div>
                            <p className="text-[11px] text-[var(--color-text-secondary)] font-medium">{cite.title || cite.fda_signal}</p>
                            <p className="text-[10px] text-[var(--color-text-muted)] italic font-mono">{cite.citation}</p>
                          </div>
                        ))}
                      </div>
                    )}

                    {item.uncertainty && (
                      <div className="text-[11px] text-[var(--color-text-muted)] flex items-center gap-1.5 pt-1">
                        <HelpCircle className="w-3.5 h-3.5" />
                        <span>Uncertainty: {item.uncertainty}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right Column: Discussion Points & Adverse Event Overlap Rail */}
        <div className="lg:col-span-4 space-y-6">
          {/* Adverse Event Overlap Rail */}
          <Card elevation="raised" className="p-5 space-y-3">
            <CardTitle>Adverse Event Hazard Overlap</CardTitle>
            <p className="text-xs text-[var(--color-text-muted)]">
              Multi-drug synergism elevating specific toxicity clusters.
            </p>
            <div className="space-y-2 text-xs">
              {data.adverse_event_overlap?.map((ae, i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl border border-[var(--color-status-critical-border)] bg-[var(--color-status-critical-bg)] text-[var(--color-status-critical-text)] space-y-1"
                >
                  <div className="flex justify-between font-bold">
                    <span>{ae.adverse_event}</span>
                    <span className="font-mono text-[11px] uppercase tracking-wider">{ae.hazard_level}</span>
                  </div>
                  <div className="text-[11px] opacity-90 font-mono">
                    Contributing: {ae.contributing_pairs?.join(', ')}
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Clinician Discussion Points Highlight Box */}
          <ClinicalHighlightBox
            variant="primary"
            title="Suggested Discussion Points"
            subtitle="Evidence-based talking points for multidisciplinary clinical rounds and patient visits."
            icon={Stethoscope}
            badge={`${data.clinician_discussion_points?.length || 0} points`}
          >
            <div className="space-y-2 pt-1 text-xs">
              {data.clinician_discussion_points?.map((pt, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 p-2.5 rounded-lg bg-[var(--color-surface-card)] border border-[var(--color-border-subtle)] text-[var(--color-text-secondary)]"
                >
                  <span className="font-bold text-[#0284C7] dark:text-[#38BDF8] shrink-0 mt-0.5">•</span>
                  <span className="leading-relaxed">{pt}</span>
                </div>
              ))}
            </div>
          </ClinicalHighlightBox>

          {/* Patient Context Considerations */}
          {data.patient_context_considerations?.length > 0 && (
            <ClinicalHighlightBox
              variant="warning"
              title="Patient Context Considerations"
              subtitle="Physiological & metabolic risk factors flagged for this patient profile"
              badge={`${data.patient_context_considerations.length} alerts`}
            >
              <div className="space-y-2 text-xs">
                {data.patient_context_considerations.map((c, i) => (
                  <div
                    key={i}
                    className="p-2.5 rounded-lg bg-[var(--color-surface-card)] border border-[var(--color-status-warning-border)] text-[var(--color-status-warning-text)] text-xs leading-relaxed"
                  >
                    {c}
                  </div>
                ))}
              </div>
            </ClinicalHighlightBox>
          )}

          {/* Link to Knowledge Graph */}
          <Card elevation="flat" className="p-5 space-y-3 border-l-4 border-l-[#0284C7] dark:border-l-[#38BDF8]">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-[#0284C7] dark:text-[#38BDF8]">
              Biomedical Knowledge Graph
            </h4>
            <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed">
              Explore the graphical interaction network linking these molecules to their biological targets and adverse signals.
            </p>
            <Button
              variant="subtle"
              size="sm"
              icon={ArrowRight}
              iconPosition="right"
              onClick={() => navigate('/knowledge-graph')}
            >
              Inspect Network Graph
            </Button>
          </Card>
        </div>
      </div>

      {/* Report Modal */}
      <ReportModal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        reportType="doctor"
        data={data}
      />
    </div>
  );
};

export default DoctorResults;
