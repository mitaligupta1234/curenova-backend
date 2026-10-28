import React, { useState } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import {
  Microscope,
  FileText,
  ChevronLeft,
  Share2,
  ExternalLink,
  BookOpen,
  ArrowRight,
  GitFork,
  Dna,
  ShieldAlert,
  HelpCircle,
  Activity,
  Zap
} from 'lucide-react';
import SafetyDisclaimer from '../../components/SafetyDisclaimer';
import RiskBadge from '../../components/RiskBadge';
import ReportModal from '../../components/ReportModal';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Card, { CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { ClinicalHighlightBox } from '../../components/ui/ClinicalHighlightBox';

export const ResearcherResults = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [data, setData] = useState(() => {
    if (location.state?.candidateData) {
      try {
        sessionStorage.setItem('curenova_active_candidate', JSON.stringify(location.state.candidateData));
      } catch {
        // ignore
      }
      return location.state.candidateData;
    }
    try {
      const activeCand = sessionStorage.getItem('curenova_active_candidate');
      if (activeCand) return JSON.parse(activeCand);

      const activeInv = sessionStorage.getItem('curenova_active_investigation');
      if (activeInv) {
        const parsedInv = JSON.parse(activeInv);
        if (parsedInv.candidates?.length > 0) {
          const topCand = parsedInv.candidates[0];
          return {
            id: topCand.id,
            drug_name: topCand.drug_name || topCand.candidate_name,
            disease: parsedInv.disease_detected || parsedInv.query_entity || 'Target Indication',
            original_indication: topCand.original_indication || 'Preclinical Repurposing Hypothesis',
            curenova_ranking: topCand.curenova_ranking ?? Math.round((topCand.prediction_score || 0.85) * 100),
            evidence_strength: topCand.evidence_strength || 'moderate',
            status_label: 'Candidate Hypothesis',
            mechanism_summary: topCand.mechanism_summary || 'Target pathway modulation',
            evidence_passages: topCand.evidence_passages || [],
            safety_signals: topCand.safety_signals || [],
            missing_data: topCand.missing_data || [],
          };
        }
      }

      const history = JSON.parse(localStorage.getItem('curenova_research_history') || '[]');
      if (history.length > 0 && history[0].result?.candidates?.length > 0) {
        const topCand = history[0].result.candidates[0];
        return {
          id: topCand.id,
          drug_name: topCand.drug_name,
          disease: history[0].disease_detected || history[0].query,
          original_indication: topCand.original_indication || 'Preclinical Repurposing Hypothesis',
          curenova_ranking: topCand.curenova_ranking ?? Math.round((topCand.prediction_score || 0.85) * 100),
          evidence_strength: topCand.evidence_strength || 'moderate',
          status_label: 'Candidate Hypothesis',
          mechanism_summary: topCand.mechanism_summary || 'Target pathway modulation',
          evidence_passages: topCand.evidence_passages || [],
          safety_signals: topCand.safety_signals || [],
          missing_data: topCand.missing_data || [],
        };
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
          <div className="w-16 h-16 rounded-2xl bg-[#0284C7]/10 border border-[#0284C7]/20 text-[#0284C7] flex items-center justify-center mx-auto">
            <Microscope className="w-8 h-8" />
          </div>
          <div className="space-y-2">
            <h2 className="text-xl sm:text-2xl font-extrabold text-[var(--color-text-primary)]">
              No Repurposing Candidate Selected
            </h2>
            <p className="text-xs sm:text-sm text-[var(--color-text-secondary)] max-w-md mx-auto leading-relaxed">
              Launch a discovery query in the Drug Repurposing Pipeline to evaluate FDA-approved candidates against curated disease target profiles with real biomedical evidence.
            </p>
          </div>

          <div className="pt-2 flex flex-col sm:flex-row justify-center gap-3">
            <Button
              variant="primary"
              onClick={() => navigate('/researcher/drug-repurposing')}
              className="!bg-[#0284C7] hover:!bg-[#0369A1]"
            >
              Open Drug Repurposing Pipeline
            </Button>
            <Button
              variant="secondary"
              onClick={() => navigate('/researcher/dashboard')}
            >
              Researcher Dashboard
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/researcher/drug-repurposing"
            className="p-2 rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-card)] hover:bg-[var(--color-surface-hover)] text-[var(--color-text-secondary)] transition-colors cursor-pointer"
            title="Back to Discovery"
          >
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-[var(--color-text-primary)]">
              Repurposing Dossier: {data.candidate_name || data.disease_name || data.drug_name}
            </h1>
            <p className="text-xs text-[var(--color-text-muted)] font-mono">
              {data.candidate_label === 'Proposed Indication'
                ? `Investigated Drug: ${data.drug_name} · Proposed Indication: ${data.disease_name || data.candidate_name}`
                : `Target Condition: ${data.disease || data.disease_name} · Candidate Drug: ${data.drug_name}`}
              {' '}· Evaluated by CureNova Repurposing Engine
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="md"
            icon={FileText}
            onClick={() => setReportModalOpen(true)}
          >
            Export Dossier (PDF)
          </Button>
          <Button
            variant="primary"
            size="md"
            icon={Share2}
            onClick={() => navigate('/knowledge-graph')}
            className="!bg-[#0284C7] hover:!bg-[#0369A1] text-white"
          >
            Inspect Network
          </Button>
        </div>
      </div>

      <SafetyDisclaimer variant="compact" />

      {/* Hero Dossier Card */}
      <Card elevation="raised" className="p-6 border-l-4 border-l-[#0284C7]">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="info" size="md">
                {data.status_label || (data.candidate_label === 'Proposed Indication' ? 'Repurposing Candidate' : 'FDA Approved')}
              </Badge>
              <RiskBadge severity={data.evidence_strength} size="sm" />
            </div>
            <h2 className="text-xl font-bold text-[var(--color-text-primary)]">
              {data.candidate_label === 'Proposed Indication'
                ? `${data.drug_name} for ${data.disease_name || data.candidate_name || data.disease}`
                : `${data.drug_name} in ${data.disease}`}
            </h2>
            <div className="text-xs text-[var(--color-text-secondary)] flex flex-wrap gap-2">
              <span className="text-[var(--color-text-muted)]">
                {data.candidate_label === 'Proposed Indication' ? 'Clinical Status / Prior:' : 'Approved Indication:'}
              </span>
              <span className="font-semibold text-[var(--color-text-primary)]">{data.original_indication}</span>
            </div>
          </div>

          <div className="sm:text-right shrink-0">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[var(--color-text-muted)] block">
              {data.ml_score_available !== false ? 'CureNova Congruence Ranking' : 'Biomedical Evidence Benchmark'}
            </span>
            <div className="text-3xl font-extrabold tabular text-[#0284C7]">
              {data.ml_score_available !== false && data.curenova_ranking != null ? (
                <>
                  {data.curenova_ranking}
                  <span className="text-sm font-normal text-[var(--color-text-muted)]"> / 100</span>
                </>
              ) : (
                <span className="text-sm font-semibold text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2 py-1 rounded border border-amber-200 dark:border-amber-800">
                  Evidence Benchmark
                </span>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Main Dossier Content */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Biological Mechanism & Literature */}
        <div className="lg:col-span-8 space-y-6">
          {/* Pharmacological Rationale */}
          <Card elevation="raised" className="p-6 space-y-4">
            <CardTitle>Biological Mechanism & Target Concordance</CardTitle>
            <p className="text-xs sm:text-sm text-[var(--color-text-secondary)] leading-relaxed">
              {data.mechanism}
            </p>

            <div className="space-y-3 pt-2">
              <div>
                <span className="text-[10px] font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider block mb-1">
                  Validated Biological Targets (ChEMBL / UniProt)
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {data.targets?.map((t, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-md bg-[var(--color-surface-sunken)] text-[var(--color-text-primary)] border border-[var(--color-border-subtle)] font-mono text-xs font-semibold"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <span className="text-[10px] font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider block mb-1">
                  Reactome Pathway Cascades
                </span>
                <div className="space-y-1 text-xs">
                  {data.pathways?.map((p, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-lg bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)] text-[var(--color-text-primary)] flex items-center gap-2"
                    >
                      <GitFork className="w-3.5 h-3.5 text-[#0d9488] shrink-0" />
                      <span>{p}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Card>

          {/* Supporting Publications */}
          <Card elevation="raised" className="p-6 space-y-4">
            <CardTitle>Supporting Peer-Reviewed Literature (PubMed)</CardTitle>
            <div className="space-y-3">
              {data.supporting_papers?.map((paper, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-sunken)] space-y-1.5 text-xs"
                >
                  <div className="flex items-center justify-between font-semibold text-[var(--color-text-primary)]">
                    <span className="font-bold">{paper.journal} ({paper.year})</span>
                    <a
                      href={`https://pubmed.ncbi.nlm.nih.gov/${paper.pmid}/`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#0d9488] hover:underline flex items-center gap-1 font-mono text-[10px] bg-[var(--color-surface-card)] px-1.5 py-0.5 rounded border border-[var(--color-border-subtle)]"
                    >
                      PMID: {paper.pmid} <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <p className="text-[var(--color-text-secondary)] font-medium leading-relaxed">{paper.title}</p>
                  <p className="text-[10px] text-[var(--color-text-muted)] italic font-mono">{paper.citation}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Right Column: Clinical Trials & Safety Rails */}
        <div className="lg:col-span-4 space-y-6">
          {/* Clinical Trials Status */}
          <Card elevation="raised" className="p-5 space-y-3">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#0d9488]" />
              <CardTitle>Clinical Trials Pipeline</CardTitle>
            </div>
            <div className="space-y-3 text-xs">
              {data.clinical_trials?.map((trial, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-sunken)] space-y-1.5"
                >
                  <div className="flex items-center justify-between font-bold text-[var(--color-text-primary)]">
                    <span className="font-mono text-[#0d9488]">{trial.nct_id}</span>
                    <Badge variant="info" size="sm">{trial.phase}</Badge>
                  </div>
                  <p className="text-[var(--color-text-secondary)] font-medium">{trial.title}</p>
                  <div className="text-[10px] text-[var(--color-text-muted)] flex justify-between pt-1 border-t border-[var(--color-border-subtle)]">
                    <span>Status: {trial.status}</span>
                    <span className="font-mono tabular">N={trial.enrollment}</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Safety Signals & Contraindications */}
          <ClinicalHighlightBox
            variant="warning"
            title="Known Safety Signals"
            subtitle="Adverse drug events and black-box warnings flagged for this molecule"
            icon={ShieldAlert}
            badge={`${data.safety_signals?.length || 0} signals`}
          >
            <div className="space-y-2 text-xs pt-1">
              {data.safety_signals?.map((sig, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-lg bg-[var(--color-surface-card)] border border-[var(--color-status-warning-border)] text-[var(--color-status-warning-text)] leading-relaxed"
                >
                  {sig}
                </div>
              ))}
            </div>
          </ClinicalHighlightBox>

          {/* Translational Limitations */}
          <Card elevation="raised" className="p-5 space-y-3">
            <div className="flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-[var(--color-text-muted)] text-xs" />
              <CardTitle>Evidence Limitations</CardTitle>
            </div>
            <div className="space-y-2 text-xs">
              {data.limitations?.map((lim, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-lg bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)] text-[var(--color-text-secondary)] leading-relaxed"
                >
                  {lim}
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      <ReportModal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        reportType="researcher"
        data={{ candidates: [data], query: data.disease }}
      />
    </div>
  );
};

export default ResearcherResults;
