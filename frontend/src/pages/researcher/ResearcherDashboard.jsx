import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Microscope,
  Search,
  Share2,
  Plus,
  ArrowRight,
  FileText,
  Clock,
  Sparkles,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  BookOpen
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { repurposingService } from '../../services/api';
import { ClinicalHighlightBox } from '../../components/ui/ClinicalHighlightBox';

export const ResearcherDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const DRUG_BENCHMARK_EXAMPLES = [
    "Metformin",
    "Fasudil",
    "Everolimus",
    "Niclosamide",
    "Imatinib"
  ];

  // Load real diseases and examples from backend API
  const [diseases, setDiseases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDisease, setSelectedDisease] = useState(null);
  const [expandedInfo, setExpandedInfo] = useState(false);
  const [exampleQueries, setExampleQueries] = useState(DRUG_BENCHMARK_EXAMPLES);
  const [quickQuery, setQuickQuery] = useState('');

  // Real stored user research runs from localStorage
  const [savedRuns, setSavedRuns] = useState([]);

  useEffect(() => {
    repurposingService
      .getDiseases()
      .then((res) => {
        const loadedDiseases = res.diseases || [];
        setDiseases(loadedDiseases);
        if (res.example_queries && res.example_queries.length > 0) {
          setExampleQueries(res.example_queries);
        }
        if (loadedDiseases.length > 0) {
          setSelectedDisease(loadedDiseases[0]);
        }
      })
      .catch((err) => console.error('Failed to load supported diseases', err))
      .finally(() => setLoading(false));

    try {
      const stored = localStorage.getItem('curenova_research_history');
      if (stored) {
        setSavedRuns(JSON.parse(stored));
      }
    } catch {
      // ignore
    }
  }, []);

  const handleQuickSubmit = (e) => {
    e.preventDefault();
    if (quickQuery.trim()) {
      navigate('/researcher/drug-repurposing', {
        state: { prefilledQuery: quickQuery.trim(), prefilledMode: 'drug-to-disease' }
      });
    }
  };

  const completedCount = savedRuns.filter((r) => r.status !== 'failed').length;

  return (
    <div className="space-y-8 w-full text-left">
      {/* ── Demo-Style Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Research Overview</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Explore drug repurposing candidates and investigate biological evidence
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => navigate('/researcher/drug-repurposing')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-medium text-sm shadow-sm transition-colors cursor-pointer"
          >
            <Plus className="h-4 w-4" />
            <span>New Research</span>
          </button>
        </div>
      </div>

      {/* ── Demo-Style 4 Stats Grid ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Research Runs */}
        <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-teal-50 dark:bg-teal-900/20 rounded-lg">
              <Microscope className="h-5 w-5 text-teal-600 dark:text-teal-400" />
            </div>
            <span className="text-xs text-teal-600 dark:text-teal-400 font-medium">Inquiries</span>
          </div>
          <h3 className="font-medium text-gray-600 dark:text-gray-400 mb-1">Research Runs</h3>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{savedRuns.length}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Saved user inquiries</p>
        </div>

        {/* Completed Analyses */}
        <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <FileText className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <span className="text-xs text-blue-600 dark:text-blue-400 font-medium">Verified</span>
          </div>
          <h3 className="font-medium text-gray-600 dark:text-gray-400 mb-1">Completed Analyses</h3>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{completedCount}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Evidence dossiers evaluated</p>
        </div>

        {/* Disease Models */}
        <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <Sparkles className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            <span className="text-xs text-purple-600 dark:text-purple-400 font-medium">Profiles</span>
          </div>
          <h3 className="font-medium text-gray-600 dark:text-gray-400 mb-1">Target Models</h3>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{diseases.length}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Curated reference models</p>
        </div>

        {/* Small Molecule Candidates */}
        <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
              <Share2 className="h-5 w-5 text-orange-600 dark:text-orange-400" />
            </div>
            <span className="text-xs text-orange-600 dark:text-orange-400 font-medium">Screened</span>
          </div>
          <h3 className="font-medium text-gray-600 dark:text-gray-400 mb-1">Drug Candidates</h3>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {diseases.reduce((acc, d) => acc + (d.candidate_count || 3), 0)}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Potential indications</p>
        </div>
      </div>

      {/* ── Main Content Grid (2-to-1 demo split) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* Left Column (2 cols): Search & Target Profiles */}
        <div className="lg:col-span-2 space-y-6">
          {/* Quick Investigation Box */}
          <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-4">
            <div>
              <h2 className="text-base font-bold text-gray-900 dark:text-gray-100">
                Investigate Drug Repurposing Hypotheses
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Enter an approved or investigational small-molecule drug to discover candidate indications.
              </p>
            </div>
            <form onSubmit={handleQuickSubmit} className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                <input
                  type="text"
                  value={quickQuery}
                  onChange={(e) => setQuickQuery(e.target.value)}
                  placeholder="e.g. Metformin, Fasudil, Everolimus..."
                  className="w-full pl-10 pr-3.5 py-2.5 text-xs sm:text-sm rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>
              <button
                type="submit"
                disabled={!quickQuery.trim()}
                className="px-4 py-2.5 rounded-xl font-medium text-xs sm:text-sm text-white bg-teal-600 hover:bg-teal-700 disabled:opacity-50 transition-colors cursor-pointer shrink-0 shadow-sm flex items-center gap-1.5"
              >
                <Sparkles className="w-4 h-4" />
                <span>Search</span>
              </button>
            </form>
            {exampleQueries.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                <span className="text-[11px] font-medium text-gray-400">Suggestions:</span>
                {exampleQueries.map((ex) => (
                  <button
                    key={ex}
                    type="button"
                    onClick={() => navigate('/researcher/drug-repurposing', { state: { prefilledQuery: ex, prefilledMode: 'drug-to-disease' } })}
                    className="px-2.5 py-1 text-xs rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-teal-50 dark:hover:bg-teal-900/30 text-gray-600 dark:text-gray-300 hover:text-teal-700 dark:hover:text-teal-300 border border-gray-200 dark:border-gray-700 transition-colors cursor-pointer"
                  >
                    + {ex}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Curated Target Profiles */}
          <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-gray-900 dark:text-gray-100">
                  Curated Target Profiles
                </h2>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  Select a disease model to inspect biological targets and small molecule candidates.
                </p>
              </div>
              <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-teal-50 text-teal-700 border border-teal-200 dark:bg-teal-950/40 dark:text-teal-300 dark:border-teal-800">
                {diseases.length} Available
              </span>
            </div>

            {loading ? (
              <div className="py-8 text-center text-xs text-[var(--color-text-muted)]">
                Loading supported disease profiles...
              </div>
            ) : diseases.length === 0 ? (
              <div className="py-8 text-center text-xs text-[var(--color-text-muted)] italic">
                No disease profiles loaded in database.
              </div>
            ) : (
              <div className="space-y-2.5">
                {diseases.map((dm) => {
                  const isSelected = selectedDisease?.id === dm.id;
                  return (
                    <div
                      key={dm.id}
                      onClick={() => {
                        setSelectedDisease(dm);
                        setExpandedInfo(false);
                      }}
                      className={`p-3.5 sm:p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between card-3d-hover ${
                        isSelected
                          ? 'bg-[#EFF6FF] dark:bg-[#0C243B]/40 border-[#0284C7] ring-1 ring-[#0284C7]'
                          : 'bg-[var(--color-surface-sunken)] border-[var(--color-border-subtle)] hover:border-[var(--color-border-strong)]'
                      }`}
                    >
                      <div className="space-y-1 min-w-0 pr-3">
                        <div className="flex items-center gap-2">
                          <span className="text-xs sm:text-sm font-bold text-[var(--color-text-primary)]">
                            {dm.name}
                          </span>
                          {dm.mesh_id && (
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--color-surface-card)] text-[var(--color-text-secondary)] border border-[var(--color-border-subtle)]">
                              MeSH: {dm.mesh_id}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-[var(--color-text-secondary)] line-clamp-1">
                          {dm.summary || 'Complex pathology with small-molecule candidate screening.'}
                        </p>
                      </div>

                      <div className="text-right shrink-0">
                        <span className="text-xs font-bold text-[#0284C7] dark:text-[#38BDF8] block">
                          {dm.candidate_count || 3} Candidates
                        </span>
                        <span className="text-[10px] text-[var(--color-text-muted)]">
                          Click to select
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Target Profile Inspector (Clean, Progressive Disclosure) */}
            {selectedDisease && (
              <div className="p-4 rounded-xl bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)] space-y-3 pt-3">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#0284C7] dark:text-[#38BDF8] block">
                      Selected Target
                    </span>
                    <h3 className="text-sm font-bold text-[var(--color-text-primary)]">
                      {selectedDisease.name}
                    </h3>
                  </div>
                  <button
                    type="button"
                    onClick={() => setExpandedInfo(!expandedInfo)}
                    className="text-xs text-[var(--color-text-secondary)] hover:text-[#0284C7] flex items-center gap-1 cursor-pointer"
                  >
                    <span>{expandedInfo ? 'Less info' : 'More information'}</span>
                    {expandedInfo ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>
                </div>

                {expandedInfo && (
                  <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed pt-1 border-t border-[var(--color-border-subtle)]">
                    {selectedDisease.summary || 'Pathology model mapped with multi-relational evidence from PubMed citations, ChEMBL bioactive binding assays, and Reactome cascades.'}
                  </p>
                )}

                <button
                  type="button"
                  onClick={() => navigate('/researcher/drug-repurposing', { state: { prefilledQuery: selectedDisease.name } })}
                  className="w-full py-2.5 px-4 rounded-xl text-xs sm:text-sm font-bold text-white bg-[#0284C7] hover:bg-[#0369A1] transition-all shadow-xs flex items-center justify-center gap-2 cursor-pointer"
                >
                  <span>Investigate {selectedDisease.name}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Recent Research & Tools */}
        <div className="space-y-6">
          {/* Recent Research Runs Card */}
          <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                <h3 className="text-base font-bold text-gray-900 dark:text-gray-100">
                  Recent Research
                </h3>
              </div>
              {savedRuns.length > 0 && (
                <span className="text-xs text-gray-400">
                  {savedRuns.length} run{savedRuns.length !== 1 ? 's' : ''}
                </span>
              )}
            </div>

            {savedRuns.length > 0 ? (
              <div className="divide-y divide-gray-100 dark:divide-gray-800">
                {savedRuns.slice(0, 5).map((item) => (
                  <div key={item.id} className="py-3 flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <span className="text-xs font-bold text-gray-900 dark:text-gray-100 truncate block">
                        {item.query}
                      </span>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[11px] text-gray-500">
                          {item.top_candidate ? `Top: ${item.top_candidate}` : 'Evaluated'}
                        </span>
                        <span className="text-[10px] text-gray-400">·</span>
                        <span className="text-[11px] text-gray-400">
                          {new Date(item.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                        </span>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => navigate('/researcher/drug-repurposing', { state: { prefilledQuery: item.query } })}
                      className="text-xs font-medium text-teal-600 dark:text-teal-400 hover:underline shrink-0 cursor-pointer"
                    >
                      Re-open
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              /* Clean Honest Empty State */
              <div className="py-8 text-center space-y-3">
                <div className="w-10 h-10 rounded-xl bg-gray-50 dark:bg-gray-800 text-gray-400 flex items-center justify-center mx-auto">
                  <Microscope className="w-5 h-5" />
                </div>
                <div className="space-y-1">
                  <h4 className="text-xs font-bold text-gray-900 dark:text-gray-100">
                    No research yet
                  </h4>
                  <p className="text-xs text-gray-500 max-w-xs mx-auto">
                    Start your first query to see results here.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => navigate('/researcher/drug-repurposing')}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium text-white bg-teal-600 hover:bg-teal-700 transition-colors cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Start Research</span>
                </button>
              </div>
            )}
          </div>

          {/* Supporting Evidence Exploration Tools */}
          <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-3">
            <h3 className="text-sm font-bold text-gray-900 dark:text-gray-100">
              Biomedical Intelligence Tools
            </h3>
            <p className="text-xs text-gray-500 leading-relaxed">
              Explore evidence references and network relationships across biological pathways.
            </p>
            <div className="grid grid-cols-2 gap-2 pt-1">
              <Link
                to="/evidence"
                className="p-3 rounded-xl bg-gray-50 dark:bg-gray-800 hover:bg-teal-50 dark:hover:bg-teal-900/20 hover:text-teal-700 dark:hover:text-teal-300 border border-gray-200 dark:border-gray-700 transition-all text-xs font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2"
              >
                <BookOpen className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                <span>Evidence</span>
              </Link>
              <Link
                to="/knowledge-graph"
                className="p-3 rounded-xl bg-gray-50 dark:bg-gray-800 hover:bg-teal-50 dark:hover:bg-teal-900/20 hover:text-teal-700 dark:hover:text-teal-300 border border-gray-200 dark:border-gray-700 transition-all text-xs font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2"
              >
                <Share2 className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                <span>Graph Network</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResearcherDashboard;
