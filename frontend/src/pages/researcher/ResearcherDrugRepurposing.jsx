import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import {
  Microscope,
  Search,
  Sparkles,
  ArrowRight,
  ExternalLink,
  BookOpen,
  Share2,
  FileText,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Activity,
  Layers,
  BarChart2,
  GitFork,
  Dna,
  Clock,
  RotateCcw,
  Sliders,
  Filter,
  ShieldCheck,
  ChevronRight,
  Download
} from 'lucide-react';
import { repurposingService } from '../../services/api';
import AnalysisProgress from '../../components/AnalysisProgress';
import SafetyDisclaimer from '../../components/SafetyDisclaimer';
import RiskBadge from '../../components/RiskBadge';
import ReportModal from '../../components/ReportModal';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Card, { CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { ClinicalHighlightBox } from '../../components/ui/ClinicalHighlightBox';

export const ResearcherDrugRepurposing = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // Persistent Research History
  const [history, setHistory] = useState(() => {
    try {
      const stored = localStorage.getItem('curenova_research_history');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  // Persistent Active Investigation state across browser refresh
  const [result, setResult] = useState(() => {
    try {
      const active = sessionStorage.getItem('curenova_active_investigation');
      if (active) return JSON.parse(active);
      const stored = localStorage.getItem('curenova_research_history');
      const hist = stored ? JSON.parse(stored) : [];
      if (hist.length > 0 && hist[0].result) return hist[0].result;
    } catch {
      // ignore
    }
    return null;
  });

  const [query, setQuery] = useState(() => {
    if (location.state?.prefilledQuery) return location.state.prefilledQuery;
    try {
      const active = sessionStorage.getItem('curenova_active_investigation');
      if (active) {
        const parsed = JSON.parse(active);
        return parsed.query_entity || parsed.disease_detected || '';
      }
      const stored = localStorage.getItem('curenova_research_history');
      const hist = stored ? JSON.parse(stored) : [];
      if (hist.length > 0) return hist[0].query || '';
    } catch {
      // ignore
    }
    return '';
  });

  const [minEvidence, setMinEvidence] = useState('all');
  const [searchMode, setSearchMode] = useState(location.state?.prefilledMode || 'drug-to-disease'); // 'drug-to-disease' | 'disease-to-drug'
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState('');
  const [selectedCandidate, setSelectedCandidate] = useState(() => {
    try {
      const active = sessionStorage.getItem('curenova_active_investigation');
      if (active) {
        const parsed = JSON.parse(active);
        return parsed.candidates?.[0] || null;
      }
      const stored = localStorage.getItem('curenova_research_history');
      const hist = stored ? JSON.parse(stored) : [];
      if (hist.length > 0 && hist[0].result?.candidates?.length > 0) {
        return hist[0].result.candidates[0];
      }
    } catch {
      // ignore
    }
    return null;
  });
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState('table'); // 'table' | 'cards'
  const [activeTab, setActiveTab] = useState('workspace'); // 'workspace' | 'history'

  const exampleQueries = [
    "Metformin",
    "Fasudil",
    "Everolimus",
    "Niclosamide",
    "Imatinib"
  ];

  const handleRunAnalysis = async (searchQuery = query, mode = searchMode) => {
    const cleanQuery = searchQuery.trim();
    if (!cleanQuery) {
      setError(mode === 'drug-to-disease'
        ? 'Please provide an existing small-molecule drug name (e.g. Metformin, Everolimus).'
        : 'Please provide a research indication, target, or disease query.');
      return;
    }
    setError('');
    setExecuting(true);
    setResult(null);

    try {
      // Direct real API call to backend - NO FAKE TIMERS
      const backendSearchType = mode === 'drug-to-disease' ? 'drug_to_disease' : 'disease_to_drug';
      const response = await repurposingService.analyze(cleanQuery, minEvidence, backendSearchType);
      setExecuting(false);
      setResult(response);
      try {
        sessionStorage.setItem('curenova_active_investigation', JSON.stringify(response));
      } catch {
        // ignore
      }

      if (response.candidates?.length > 0) {
        setSelectedCandidate(response.candidates[0]);
      }

      // Persist in history
      const historyItem = {
        id: response.analysis_id || `rep-${Date.now()}`,
        query: cleanQuery,
        search_type: backendSearchType,
        disease_detected: response.disease_detected || cleanQuery,
        candidate_count: response.candidates?.length || 0,
        top_candidate: response.candidates?.[0]?.candidate_name || response.candidates?.[0]?.drug_name || 'N/A',
        timestamp: new Date().toISOString(),
        result: response,
      };

      const updatedHistory = [historyItem, ...history.filter(h => h.query.toLowerCase() !== cleanQuery.toLowerCase())].slice(0, 15);
      setHistory(updatedHistory);
      try {
        localStorage.setItem('curenova_research_history', JSON.stringify(updatedHistory));
      } catch {
        // ignore storage errors
      }
    } catch (err) {
      setExecuting(false);
      setError(err.message || 'Repurposing discovery analysis failed. Check backend connection.');
    }
  };

  const handleLoadFromHistory = (item) => {
    setQuery(item.query);
    setResult(item.result);
    try {
      sessionStorage.setItem('curenova_active_investigation', JSON.stringify(item.result));
    } catch {
      // ignore
    }
    if (item.result?.candidates?.length > 0) {
      setSelectedCandidate(item.result.candidates[0]);
    }
    setActiveTab('workspace');
  };

  const handleClearHistory = () => {
    setHistory([]);
    try {
      localStorage.removeItem('curenova_research_history');
      sessionStorage.removeItem('curenova_active_investigation');
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    if (location.state?.prefilledQuery) {
      handleRunAnalysis(location.state.prefilledQuery);
    } else {
      const params = new URLSearchParams(window.location.search);
      const wid = params.get('workflow_id') || params.get('id');
      if (wid && !result) {
        repurposingService
          .getInvestigation(wid)
          .then((res) => {
            if (res) {
              setResult(res);
              setQuery(res.query_entity || res.disease_detected || '');
              if (res.candidates?.length > 0) setSelectedCandidate(res.candidates[0]);
              try {
                sessionStorage.setItem('curenova_active_investigation', JSON.stringify(res));
              } catch {
                // ignore
              }
            }
          })
          .catch((err) => {
            console.warn('Failed to load investigation run from URL param:', err);
          });
      }
    }
  }, [location.state?.prefilledQuery]);

  return (
    <div className="space-y-6 text-left">
      {/* ── Top Header Bar ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-[var(--color-border-subtle)]">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-[#E0F2FE] text-[#0369A1] border border-[#BAE6FD] dark:bg-[#0369A1]/20 dark:text-[#38BDF8] dark:border-[#0284C7]/40">
              <Microscope className="w-5 h-5" />
            </span>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#0A2540] dark:text-[#F1F5F9]">
                Drug Repurposing Discovery Engine
              </h1>
              <p className="text-xs sm:text-sm text-[var(--color-text-secondary)] mt-0.5">
                Evaluate small-molecule candidates against disease target profiles with multi-source evidence grounding
              </p>
            </div>
          </div>
        </div>

        {/* Tab switch between workspace and history */}
        <div className="flex items-center gap-2">
          <div className="p-1 rounded-xl bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)] flex text-xs font-semibold">
            <button
              type="button"
              onClick={() => setActiveTab('workspace')}
              className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
                activeTab === 'workspace'
                  ? 'bg-[var(--color-surface-card)] text-[#0284C7] dark:text-[#38BDF8] shadow-xs font-bold'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'
              }`}
            >
              Active Workspace
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('history')}
              className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'history'
                  ? 'bg-[var(--color-surface-card)] text-[#0284C7] dark:text-[#38BDF8] shadow-xs font-bold'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              <span>Saved Runs ({history.length})</span>
            </button>
          </div>
          <SafetyDisclaimer variant="compact" />
        </div>
      </div>

      {/* ── Tab: History View ── */}
      {activeTab === 'history' && (
        <Card elevation="raised" className="p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-[var(--color-border-subtle)] pb-4">
            <div>
              <h2 className="text-base font-bold text-[var(--color-text-primary)]">Previous Research Runs</h2>
              <p className="text-xs text-[var(--color-text-muted)]">Reopen completed discovery dossiers or re-execute searches</p>
            </div>
            {history.length > 0 && (
              <Button variant="ghost" size="sm" onClick={handleClearHistory} className="text-rose-600 hover:text-rose-700">
                Clear History
              </Button>
            )}
          </div>

          {history.length === 0 ? (
            <div className="py-12 text-center text-xs text-[var(--color-text-muted)] italic space-y-2">
              <Microscope className="w-8 h-8 text-[var(--color-text-muted)] mx-auto opacity-50" />
              <p>No previous research runs recorded yet.</p>
              <Button variant="secondary" size="sm" onClick={() => setActiveTab('workspace')}>
                Start a New Discovery Run
              </Button>
            </div>
          ) : (
            <div className="divide-y divide-[var(--color-border-subtle)]">
              {history.map((item) => (
                <div key={item.id} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[var(--color-surface-hover)] p-2 rounded-xl transition-colors">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-[var(--color-text-primary)]">{item.query}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#0284C7]/10 text-[#0284C7] border border-[#0284C7]/20 dark:bg-[#0284C7]/20 dark:text-[#38BDF8] dark:border-[#0284C7]/40">
                        {item.candidate_count} Candidates
                      </span>
                    </div>
                    <p className="text-xs text-[var(--color-text-muted)]">
                      Top Hit: <strong className="text-[var(--color-text-primary)]">{item.top_candidate}</strong> · Run date: {new Date(item.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => handleLoadFromHistory(item)}
                      className="!bg-[#0284C7] hover:!bg-[#0369A1]"
                    >
                      Open Results
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        setQuery(item.query);
                        handleRunAnalysis(item.query);
                        setActiveTab('workspace');
                      }}
                    >
                      Re-run
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* ── Tab: Active Workspace ── */}
      {activeTab === 'workspace' && (
        <div className="space-y-6">
          {/* Query Formulation Input Card */}
          <Card elevation="raised" className="p-6 space-y-4">
            {/* Search Mode Toggle */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--color-border-subtle)] pb-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-[var(--color-text-secondary)]">Search Mode:</span>
                <div className="flex gap-1.5 p-1 rounded-lg bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)] text-[11px] font-semibold">
                  <button
                    type="button"
                    onClick={() => setSearchMode('disease-to-drug')}
                    className={`px-2.5 py-1 rounded transition-colors cursor-pointer ${
                      searchMode === 'disease-to-drug'
                        ? 'bg-[var(--color-surface-card)] text-[#0284C7] dark:text-[#38BDF8] font-bold shadow-xs'
                        : 'text-[var(--color-text-muted)]'
                    }`}
                  >
                    Disease to Drug Candidates
                  </button>
                  <button
                    type="button"
                    onClick={() => setSearchMode('drug-to-disease')}
                    className={`px-2.5 py-1 rounded transition-colors cursor-pointer ${
                      searchMode === 'drug-to-disease'
                        ? 'bg-[var(--color-surface-card)] text-[#0284C7] dark:text-[#38BDF8] font-bold shadow-xs'
                        : 'text-[var(--color-text-muted)]'
                    }`}
                  >
                    Drug to Alternative Indications
                  </button>
                </div>
              </div>
              <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
                Database: PubMed · ChEMBL 34 · Reactome
              </span>
            </div>

            {/* Input Row */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)] pointer-events-none" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleRunAnalysis(query)}
                  placeholder={
                    searchMode === 'disease-to-drug'
                      ? "Enter disease or phenotype (e.g. Alzheimer's disease, Glioblastoma Multiforme)..."
                      : "Enter small molecule drug (e.g. Metformin, Fasudil, Disulfiram)..."
                  }
                  className="w-full pl-10 pr-4 py-3 text-xs sm:text-sm rounded-xl border border-[var(--color-border-strong)] bg-[var(--color-surface-card)] text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:ring-2 focus:ring-[#0284C7] transition-all"
                />
              </div>

              <div className="flex gap-2">
                <select
                  value={minEvidence}
                  onChange={(e) => setMinEvidence(e.target.value)}
                  className="px-3 py-2 text-xs rounded-xl border border-[var(--color-border-strong)] bg-[var(--color-surface-card)] text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[#0284C7] cursor-pointer"
                >
                  <option value="all">Evidence: All Levels</option>
                  <option value="high">High Confidence Only</option>
                  <option value="trials">Phase II / III Trials</option>
                </select>

                <Button
                  variant="primary"
                  size="md"
                  icon={Sparkles}
                  loading={executing}
                  onClick={() => handleRunAnalysis(query)}
                  className="shrink-0 !bg-[#0284C7] hover:!bg-[#0369A1] text-white"
                >
                  Discover Candidates
                </Button>
              </div>
            </div>

            {/* Example Queries */}
            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
              <span className="text-[var(--color-text-muted)] font-medium">Curated Benchmark Queries:</span>
              {exampleQueries.map((ex, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => {
                    setQuery(ex);
                    handleRunAnalysis(ex);
                  }}
                  className="px-2.5 py-1 rounded-lg text-[11px] font-mono bg-[var(--color-surface-sunken)] hover:bg-[var(--color-surface-hover)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] border border-[var(--color-border-subtle)] transition-colors cursor-pointer"
                >
                  {ex}
                </button>
              ))}
            </div>

            {error && (
              <div className="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2 font-medium">
                <AlertTriangle className="w-4 h-4 shrink-0 text-[#B91C1C]" />
                <span>{error}</span>
              </div>
            )}
          </Card>

          {/* Execution Progress */}
          {executing && (
            <div className="py-8">
              <AnalysisProgress
                title="Executing Drug Repurposing Pipeline"
                subtitle="Retrieving ChEMBL bioassays, ranking molecular targets, and challenging conflicting evidence"
              />
            </div>
          )}

          {/* Results Workspace */}
          {!executing && result && (
            <div className="space-y-6">
              
              {/* Result Overview Banner */}
              <Card elevation="raised" className="p-6 border-l-4 border-l-[#0284C7]">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold font-mono bg-[#E0F2FE] text-[#0369A1] border border-[#BAE6FD] dark:bg-[#0369A1]/20 dark:text-[#38BDF8]">
                        Target Entity: {result.disease_detected || result.query}
                      </span>
                      <span className="text-xs text-[var(--color-text-muted)] font-mono">
                        Run ID: {result.analysis_id}
                      </span>
                    </div>
                    <h2 className="text-xl sm:text-2xl font-extrabold text-[var(--color-text-primary)]">
                      {result.disease_detected || result.query} Discovery Dossier
                    </h2>
                    <p className="text-xs sm:text-sm text-[var(--color-text-secondary)] max-w-3xl leading-relaxed">
                      {result.summary}
                    </p>
                  </div>

                  <div className="flex items-center gap-2.5 shrink-0">
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={FileText}
                      onClick={() => setReportModalOpen(true)}
                    >
                      Export Dossier
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      icon={Share2}
                      onClick={() => navigate('/knowledge-graph')}
                      className="!bg-[#0284C7] hover:!bg-[#0369A1] text-white"
                    >
                      Inspect Graph
                    </Button>
                  </div>
                </div>
              </Card>

              {/* View Mode Toggle & Metrics */}
              <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-[var(--color-text-primary)] text-sm">
                    Ranked Candidates ({result.candidates?.length || 0})
                  </span>
                  <span className="text-[var(--color-text-muted)]">• Ordered by CureNova Congruence Ranking</span>
                </div>

                <div className="flex items-center gap-2">
                  <div className="p-1 rounded-lg bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)] flex">
                    <button
                      type="button"
                      onClick={() => setViewMode('table')}
                      className={`px-2.5 py-1 rounded text-xs font-semibold cursor-pointer ${
                        viewMode === 'table' ? 'bg-[var(--color-surface-card)] text-[#0284C7] dark:text-[#38BDF8] shadow-xs' : 'text-[var(--color-text-muted)]'
                      }`}
                    >
                      Table View
                    </button>
                    <button
                      type="button"
                      onClick={() => setViewMode('cards')}
                      className={`px-2.5 py-1 rounded text-xs font-semibold cursor-pointer ${
                        viewMode === 'cards' ? 'bg-[var(--color-surface-card)] text-[#0284C7] dark:text-[#38BDF8] shadow-xs' : 'text-[var(--color-text-muted)]'
                      }`}
                    >
                      Card Grid
                    </button>
                  </div>
                </div>
              </div>

              {/* Main Content Layout: Candidate List + Candidate Inspector Panel */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                
                {/* Left: Candidates Presentation (Table or Cards) */}
                <div className="lg:col-span-7 space-y-4">
                  {viewMode === 'table' ? (
                    <Card elevation="raised" className="overflow-hidden">
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-[var(--color-surface-sunken)] text-[var(--color-text-muted)] border-b border-[var(--color-border-subtle)] uppercase text-[10px] font-mono tracking-wider">
                            <tr>
                              <th className="py-3 px-4">Rank</th>
                              <th className="py-3 px-4">
                                {searchMode === 'drug-to-disease' ? 'Proposed Indication' : 'Candidate Drug'}
                              </th>
                              <th className="py-3 px-4">Score</th>
                              <th className="py-3 px-4">Evidence Level</th>
                              <th className="py-3 px-4 text-right">Action</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-[var(--color-border-subtle)]">
                            {result.candidates?.map((cand, idx) => {
                              const isSelected = selectedCandidate?.id === cand.id;
                              const displayName = cand.candidate_name || (searchMode === 'drug-to-disease' ? cand.disease_name : cand.drug_name);
                              const subtitle = searchMode === 'drug-to-disease'
                                ? `Investigated Drug: ${cand.drug_name || result.query_entity}`
                                : cand.original_indication;

                              return (
                                <tr
                                  key={cand.id}
                                  onClick={() => setSelectedCandidate(cand)}
                                  className={`cursor-pointer transition-colors ${
                                    isSelected
                                      ? 'bg-[#EFF6FF] dark:bg-[#0C243B]/40 font-semibold'
                                      : 'hover:bg-[var(--color-surface-hover)]'
                                  }`}
                                >
                                  <td className="py-3 px-4 font-mono font-bold text-[#0A2540] dark:text-[#38BDF8]">
                                    #{idx + 1}
                                  </td>
                                  <td className="py-3 px-4">
                                    <div className="font-bold text-[var(--color-text-primary)]">{displayName}</div>
                                    <div className="text-[10px] text-[var(--color-text-muted)] font-mono">{subtitle}</div>
                                  </td>
                                  <td className="py-3 px-4 font-mono font-bold text-[#0284C7] dark:text-[#38BDF8]">
                                    {cand.ml_score_available && cand.curenova_ranking != null ? (
                                      <>
                                        {cand.curenova_ranking}
                                        <span className="text-[10px] text-[var(--color-text-muted)] font-normal"> / 100</span>
                                      </>
                                    ) : (
                                      <span className="text-[10px] font-sans font-semibold text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded border border-amber-200 dark:border-amber-800">
                                        Evidence Benchmark
                                      </span>
                                    )}
                                  </td>
                                  <td className="py-3 px-4">
                                    <RiskBadge severity={cand.evidence_strength} size="sm" />
                                  </td>
                                  <td className="py-3 px-4 text-right">
                                    <button
                                      type="button"
                                      className="text-xs font-bold text-[#0284C7] dark:text-[#38BDF8] hover:underline cursor-pointer"
                                    >
                                      Inspect &rarr;
                                    </button>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </Card>
                  ) : (
                    <div className="space-y-4">
                      {result.candidates?.map((cand, idx) => {
                        const isSelected = selectedCandidate?.id === cand.id;
                        const displayName = cand.candidate_name || (searchMode === 'drug-to-disease' ? cand.disease_name : cand.drug_name);
                        const subtitle = searchMode === 'drug-to-disease'
                          ? `Drug: ${cand.drug_name || result.query_entity}`
                          : cand.original_indication;

                        return (
                          <Card
                            key={cand.id}
                            elevation={isSelected ? 'raised' : 'flat'}
                            interactive={true}
                            onClick={() => setSelectedCandidate(cand)}
                            className={`p-5 space-y-3.5 transition-all ${
                              isSelected
                                ? 'border-[#0284C7] ring-2 ring-[#0284C7]/20 bg-[var(--color-surface-card)]'
                                : 'border-[var(--color-border-subtle)] bg-[var(--color-surface-card)]'
                            }`}
                          >
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="flex items-center gap-2">
                                <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-[#0A2540] text-white">
                                  #{idx + 1}
                                </span>
                                <h3 className="text-base font-bold text-[var(--color-text-primary)]">{displayName}</h3>
                                <span className="text-xs text-[var(--color-text-muted)] font-mono">({subtitle})</span>
                              </div>
                              <div className="flex items-center gap-2">
                                {cand.ml_score_available && cand.curenova_ranking != null ? (
                                  <span className="font-mono font-bold text-sm text-[#0284C7] dark:text-[#38BDF8]">
                                    {cand.curenova_ranking} / 100
                                  </span>
                                ) : (
                                  <span className="text-[11px] font-sans font-semibold text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded border border-amber-200 dark:border-amber-800">
                                    Evidence Benchmark
                                  </span>
                                )}
                                <RiskBadge severity={cand.evidence_strength} size="sm" />
                              </div>
                            </div>

                            <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed">{cand.mechanism_summary || cand.mechanism}</p>

                            <div className="flex flex-wrap items-center gap-1.5 text-[11px] pt-1">
                              <span className="text-[var(--color-text-muted)] font-semibold mr-1">Biological Targets:</span>
                              {cand.targets?.map((t, tidx) => (
                                <span
                                  key={tidx}
                                  className="px-2 py-0.5 rounded-md bg-[var(--color-surface-sunken)] text-[var(--color-text-primary)] border border-[var(--color-border-subtle)] font-mono font-medium"
                                >
                                  {t}
                                </span>
                              ))}
                            </div>
                          </Card>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Right: Candidate Deep Dive Inspector Panel */}
                <div className="lg:col-span-5">
                  <div className="sticky top-20">
                    <Card elevation="raised" className="p-6 space-y-5 border-l-4 border-l-[#0284C7]">
                      {selectedCandidate ? (
                        <div className="space-y-5">
                          
                          {/* Candidate Identity Header */}
                          <div className="flex items-center justify-between border-b border-[var(--color-border-subtle)] pb-3">
                            <div>
                              <span className="text-[10px] font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider block">
                                {selectedCandidate.candidate_label || (searchMode === 'drug-to-disease' ? 'Proposed Indication' : 'Candidate Drug')}
                              </span>
                              <h3 className="text-lg font-bold text-[var(--color-text-primary)]">
                                {selectedCandidate.candidate_name || (searchMode === 'drug-to-disease' ? selectedCandidate.disease_name : selectedCandidate.drug_name)}
                              </h3>
                              <span className="text-xs text-[var(--color-text-muted)] font-mono">
                                {searchMode === 'drug-to-disease'
                                  ? `Investigated Drug: ${selectedCandidate.drug_name || result.query_entity}`
                                  : `Approved Indication: ${selectedCandidate.original_indication}`}
                              </span>
                            </div>
                            <div className="text-right">
                              <span className="text-[10px] font-mono text-[var(--color-text-muted)] block uppercase font-bold">
                                {selectedCandidate.ml_score_available ? 'Congruence' : 'Evidence Prior'}
                              </span>
                              <span className="text-xl font-black font-mono text-[#0284C7] dark:text-[#38BDF8]">
                                {selectedCandidate.ml_score_available && selectedCandidate.curenova_ranking != null ? selectedCandidate.curenova_ranking : 'Benchmark'}
                              </span>
                            </div>
                          </div>

                          {/* Proposed Mechanism */}
                          <div className="space-y-1">
                            <span className="text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider block">
                              Biological Mechanism
                            </span>
                            <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed">
                              {selectedCandidate.mechanism_summary || selectedCandidate.mechanism}
                            </p>
                          </div>

                          {/* Primary Targets & Pathways */}
                          <div className="space-y-2">
                            <span className="text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider block">
                              Targets & Reactome Pathways
                            </span>
                            <div className="flex flex-wrap gap-1.5">
                              {selectedCandidate.targets?.map((t, idx) => (
                                <span
                                  key={idx}
                                  className="px-2 py-0.5 rounded-md bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)] text-xs font-mono font-semibold"
                                >
                                  {t}
                                </span>
                              ))}
                            </div>
                            <div className="space-y-1 pt-1">
                              {selectedCandidate.pathways?.map((pw, idx) => (
                                <div
                                  key={idx}
                                  className="p-2 rounded-lg bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)] text-[11px] text-[var(--color-text-primary)] flex items-center gap-2"
                                >
                                  <GitFork className="w-3.5 h-3.5 text-[#0284C7] dark:text-[#38BDF8] shrink-0" />
                                  <span className="truncate">{pw}</span>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Supporting Evidence with real PubMed links */}
                          <div className="space-y-2 pt-2 border-t border-[var(--color-border-subtle)]">
                            <span className="text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider block">
                              Supporting Peer-Reviewed Literature
                            </span>
                            {selectedCandidate.supporting_papers?.length > 0 ? (
                              <div className="space-y-2">
                                {selectedCandidate.supporting_papers.map((p, idx) => (
                                  <div
                                    key={idx}
                                    className="p-3 rounded-xl bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)] space-y-1 text-xs"
                                  >
                                    <div className="flex items-center justify-between text-[11px] font-semibold">
                                      <span className="text-[var(--color-text-primary)] truncate max-w-[200px]">{p.journal} ({p.year})</span>
                                      {p.pmid && (
                                        <a
                                          href={`https://pubmed.ncbi.nlm.nih.gov/${p.pmid}/`}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="text-[#0284C7] dark:text-[#38BDF8] hover:underline flex items-center gap-1 font-mono text-[10px]"
                                        >
                                          PMID: {p.pmid} <ExternalLink className="w-3 h-3" />
                                        </a>
                                      )}
                                    </div>
                                    <p className="text-[11px] text-[var(--color-text-secondary)] font-medium leading-snug">
                                      {p.title}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="p-3 rounded-lg bg-[var(--color-surface-sunken)] text-xs text-[var(--color-text-muted)] italic">
                                Insufficient direct literature evidence retrieved for this target pair.
                              </div>
                            )}
                          </div>

                          {/* Clinical Trials Table */}
                          {selectedCandidate.clinical_trials?.length > 0 && (
                            <div className="space-y-2 pt-2 border-t border-[var(--color-border-subtle)]">
                              <span className="text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider block">
                                Documented Clinical Trials
                              </span>
                              <div className="space-y-2">
                                {selectedCandidate.clinical_trials.map((trial, idx) => (
                                  <div
                                    key={idx}
                                    className="p-2.5 rounded-xl bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)] flex items-center justify-between text-xs"
                                  >
                                    <div>
                                      <a
                                        href={`https://clinicaltrials.gov/study/${trial.nct_id}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="font-mono font-bold text-[#0284C7] dark:text-[#38BDF8] hover:underline flex items-center gap-1"
                                      >
                                        {trial.nct_id} <ExternalLink className="w-3 h-3" />
                                      </a>
                                      <div className="text-[11px] text-[var(--color-text-secondary)] line-clamp-1">{trial.title}</div>
                                    </div>
                                    <div className="text-right shrink-0">
                                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--color-surface-card)] border border-[var(--color-border-subtle)] block">
                                        {trial.phase}
                                      </span>
                                      <span className="text-[9px] text-[var(--color-text-muted)]">{trial.status}</span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Limitations & Missing Evidence */}
                          <div className="space-y-1.5 pt-2 border-t border-[var(--color-border-subtle)] text-xs">
                            <span className="font-mono font-bold text-[#B45309] dark:text-[#FBBF24] uppercase tracking-wider text-[10px] flex items-center gap-1">
                              <AlertTriangle className="w-3.5 h-3.5" />
                              Limitations & Evidence Gaps
                            </span>
                            <ul className="space-y-1 text-[11px] text-[var(--color-text-secondary)]">
                              {selectedCandidate.limitations?.map((lim, idx) => (
                                <li key={idx} className="flex items-start gap-1.5">
                                  <span className="text-[#B45309] dark:text-[#FBBF24] font-bold">•</span>
                                  <span>{lim}</span>
                                </li>
                              )) || (
                                <li>Investigational candidate; requires prospective translational validation.</li>
                              )}
                            </ul>
                          </div>

                          {/* Actions */}
                          <div className="pt-2 flex gap-2">
                            <Button
                              variant="secondary"
                              size="sm"
                              className="flex-1"
                              icon={FileText}
                              onClick={() => setReportModalOpen(true)}
                            >
                              Generate Dossier
                            </Button>
                            <Button
                              variant="primary"
                              size="sm"
                              className="flex-1 !bg-[#0284C7] hover:!bg-[#0369A1]"
                              icon={Share2}
                              onClick={() => navigate('/knowledge-graph')}
                            >
                              Inspect Network
                            </Button>
                          </div>

                        </div>
                      ) : (
                        <div className="py-12 text-center text-xs text-[var(--color-text-muted)] italic">
                          Select a candidate from the table to view the full biological and evidence profile.
                        </div>
                      )}
                    </Card>
                  </div>
                </div>

              </div>
            </div>
          )}
        </div>
      )}

      {/* Report Modal */}
      <ReportModal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        reportType="researcher"
        data={result}
      />
    </div>
  );
};

export default ResearcherDrugRepurposing;
