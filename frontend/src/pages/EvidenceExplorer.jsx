import React, { useState, useEffect, useCallback } from 'react';
import {
  Search,
  Filter,
  FileText,
  ExternalLink,
  BookOpen,
  RefreshCw,
  AlertTriangle,
  Database,
  FlaskConical,
  Activity,
  Layers,
  X,
  ChevronRight,
  Tag
} from 'lucide-react';
import { evidenceService } from '../services/api';
import RiskBadge from '../components/RiskBadge';
import Button from '../components/ui/Button';
import { SkeletonCard } from '../components/ui/Skeleton';

const SOURCES = [
  { key: 'all', label: 'All Sources', color: '#0271b0', icon: Database },
  { key: 'PubMed', label: 'PubMed', color: '#38bdf8', icon: BookOpen },
  { key: 'openFDA', label: 'openFDA', color: '#fbbf24', icon: Activity },
  { key: 'ClinicalTrials.gov', label: 'ClinicalTrials', color: '#818cf8', icon: FlaskConical },
  { key: 'ChEMBL', label: 'ChEMBL', color: '#2dd4bf', icon: Layers },
];

const TYPES = [
  { key: 'all', label: 'All Types' },
  { key: 'Literature', label: 'Literature' },
  { key: 'SafetySignal', label: 'Safety Signal' },
  { key: 'ClinicalTrial', label: 'Clinical Trial' },
  { key: 'Pathway', label: 'Pathway' },
];

export const EvidenceExplorer = () => {
  const [query, setQuery] = useState('');
  const [source, setSource] = useState('all');
  const [evidenceType, setEvidenceType] = useState('all');
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedRecord, setSelectedRecord] = useState(null);

  const fetchEvidence = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await evidenceService.search({
        q: query || undefined,
        source: source !== 'all' ? source : undefined,
        evidence_type: evidenceType !== 'all' ? evidenceType : undefined,
      });
      setRecords(Array.isArray(res) ? res : (res.results || []));
    } catch {
      setError('Unable to reach evidence repository. Please retry.');
    } finally {
      setLoading(false);
    }
  }, [query, source, evidenceType]);

  useEffect(() => {
    fetchEvidence();
  }, [fetchEvidence]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchEvidence();
  };

  const clearFilters = () => {
    setQuery('');
    setSource('all');
    setEvidenceType('all');
  };

  const hasActiveFilters = source !== 'all' || evidenceType !== 'all' || query;
  const activeSource = SOURCES.find((s) => s.key === source);

  return (
    <div className="min-h-screen bg-[var(--color-surface-ground)]">

      {/* ── PAGE HEADER ── */}
      <div className="bg-gradient-to-r from-[#0b1e3d] to-[#0a2d3a] border-b border-white/10 px-6 py-6">
        <div className="max-w-[1600px] mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5 mb-1">
              <div className="w-8 h-8 rounded-lg bg-[#0271b0] flex items-center justify-center">
                <Search className="w-4 h-4 text-white" />
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold tracking-tight text-white">
                Biomedical Evidence Explorer
              </h1>
            </div>
            <p className="text-sm text-white/60 ml-10">
              Curated peer-reviewed literature, regulatory signals, and pathway data — PubMed · openFDA · ChEMBL · ClinicalTrials.gov
            </p>
          </div>
          <div className="flex items-center gap-2 ml-10 sm:ml-0">
            {SOURCES.slice(1).map((s) => (
              <span
                key={s.key}
                className="flex items-center gap-1 text-[11px] font-semibold text-white/50 px-2 py-1 rounded-lg border border-white/10 bg-white/5"
              >
                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: s.color }} />
                {s.label}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-[1600px] mx-auto flex flex-col lg:flex-row min-h-[calc(100vh-160px)]">

        {/* ── LEFT SIDEBAR: Filters ── */}
        <aside className="w-full lg:w-64 xl:w-72 flex-shrink-0 border-b lg:border-b-0 lg:border-r border-[var(--color-border-subtle)] bg-[var(--color-surface-card)] p-5 space-y-6">

          {/* Search */}
          <form onSubmit={handleSearchSubmit} className="space-y-2">
            <label className="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
              Search Evidence
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)] pointer-events-none" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Drug, disease, PMID…"
                className="w-full pl-9 pr-3 py-2 text-sm rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-sunken)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-2 focus:ring-[#0271b0] focus:border-transparent transition-all"
              />
            </div>
            <button
              type="submit"
              className="w-full py-2 rounded-xl bg-[#0271b0] text-white text-sm font-bold hover:bg-[#025f93] transition-colors"
            >
              Search
            </button>
          </form>

          {/* Source filter */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                Data Source
              </span>
              <Filter className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
            </div>
            <div className="space-y-1">
              {SOURCES.map((s) => {
                const Icon = s.icon;
                const isActive = source === s.key;
                return (
                  <button
                    key={s.key}
                    type="button"
                    onClick={() => setSource(s.key)}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-all text-left ${
                      isActive
                        ? 'text-white shadow-sm'
                        : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)]'
                    }`}
                    style={isActive ? { backgroundColor: s.color } : {}}
                  >
                    <Icon className="w-4 h-4 flex-shrink-0" />
                    <span>{s.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Evidence Type filter */}
          <div className="space-y-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
              Evidence Type
            </span>
            <div className="space-y-1">
              {TYPES.map((t) => {
                const isActive = evidenceType === t.key;
                return (
                  <button
                    key={t.key}
                    type="button"
                    onClick={() => setEvidenceType(t.key)}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-all text-left ${
                      isActive
                        ? 'bg-[var(--color-brand-surface)] text-[var(--color-brand-primary)] border border-[var(--color-brand-border)]'
                        : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)]'
                    }`}
                  >
                    <Tag className="w-3.5 h-3.5 flex-shrink-0" />
                    {t.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Clear filters */}
          {hasActiveFilters && (
            <button
              type="button"
              onClick={clearFilters}
              className="w-full flex items-center justify-center gap-2 py-2 rounded-xl border border-[var(--color-border-subtle)] text-xs font-semibold text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] transition-all"
            >
              <X className="w-3.5 h-3.5" />
              Clear All Filters
            </button>
          )}
        </aside>

        {/* ── MAIN CONTENT AREA ── */}
        <main className="flex-1 p-5 sm:p-6 space-y-4 min-w-0">

          {/* Results header bar */}
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-3">
              {!loading && !error && (
                <span className="text-sm font-bold text-[var(--color-text-primary)]">
                  {records.length} record{records.length !== 1 ? 's' : ''} found
                </span>
              )}
              {hasActiveFilters && (
                <div className="flex flex-wrap gap-1.5">
                  {source !== 'all' && (
                    <span
                      className="flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full text-white"
                      style={{ backgroundColor: activeSource?.color }}
                    >
                      {source}
                      <button onClick={() => setSource('all')} className="ml-0.5 hover:opacity-80"><X className="w-3 h-3" /></button>
                    </span>
                  )}
                  {evidenceType !== 'all' && (
                    <span className="flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-[var(--color-brand-surface)] text-[var(--color-brand-primary)] border border-[var(--color-brand-border)]">
                      {evidenceType}
                      <button onClick={() => setEvidenceType('all')} className="ml-0.5 hover:opacity-80"><X className="w-3 h-3" /></button>
                    </span>
                  )}
                  {query && (
                    <span className="flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-[var(--color-surface-sunken)] text-[var(--color-text-secondary)] border border-[var(--color-border-subtle)]">
                      "{query}"
                      <button onClick={() => setQuery('')} className="ml-0.5 hover:opacity-80"><X className="w-3 h-3" /></button>
                    </span>
                  )}
                </div>
              )}
            </div>
            <button
              type="button"
              onClick={fetchEvidence}
              className="flex items-center gap-1.5 text-xs font-semibold text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
          </div>

          {/* Results grid */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {Array.from({ length: 9 }).map((_, i) => <SkeletonCard key={i} />)}
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-24 space-y-4 text-center">
              <div className="w-14 h-14 rounded-2xl bg-[var(--color-status-critical-bg)] border border-[var(--color-status-critical-border)] flex items-center justify-center">
                <AlertTriangle className="w-7 h-7 text-[#dc2626]" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-[var(--color-text-primary)]">Evidence Retrieval Error</h3>
                <p className="text-xs text-[var(--color-text-muted)] mt-1 max-w-xs">{error}</p>
              </div>
              <Button variant="secondary" size="sm" icon={RefreshCw} onClick={fetchEvidence}>Retry</Button>
            </div>
          ) : records.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 space-y-4 text-center">
              <div className="w-14 h-14 rounded-2xl bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)] flex items-center justify-center">
                <BookOpen className="w-7 h-7 text-[var(--color-text-muted)]" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-[var(--color-text-primary)]">No Records Found</h3>
                <p className="text-xs text-[var(--color-text-muted)] mt-1 max-w-xs">
                  Try broadening your query or clearing the active filters.
                </p>
              </div>
              <Button variant="subtle" size="sm" onClick={clearFilters}>Clear Filters</Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {records.map((rec) => {
                const srcColor = SOURCES.find((s) => s.key === rec.source)?.color || '#64748b';
                return (
                  <div
                    key={rec.id}
                    onClick={() => setSelectedRecord(selectedRecord?.id === rec.id ? null : rec)}
                    className={`group bg-[var(--color-surface-card)] border rounded-2xl p-5 flex flex-col justify-between space-y-3 cursor-pointer transition-all hover:shadow-md ${
                      selectedRecord?.id === rec.id
                        ? 'border-[#0271b0] ring-2 ring-[#0271b0]/20 shadow-md'
                        : 'border-[var(--color-border-subtle)] hover:border-[var(--color-border-strong)]'
                    }`}
                  >
                    <div className="space-y-2.5">
                      {/* Source dot + type */}
                      <div className="flex items-center justify-between gap-2">
                        <span
                          className="flex items-center gap-1.5 text-[11px] font-bold px-2.5 py-1 rounded-full text-white"
                          style={{ backgroundColor: srcColor }}
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-white/60" />
                          {rec.source}
                        </span>
                        {rec.evidence_level && <RiskBadge severity={rec.evidence_level} size="sm" />}
                      </div>

                      <h3 className="text-sm font-bold text-[var(--color-text-primary)] leading-snug line-clamp-2 group-hover:text-[#0271b0] transition-colors">
                        {rec.title}
                      </h3>

                      <p className="text-xs text-[var(--color-text-secondary)] line-clamp-3 leading-relaxed">
                        {rec.summary || rec.findings}
                      </p>
                    </div>

                    <div className="pt-3 border-t border-[var(--color-border-subtle)] flex items-center justify-between">
                      <span className="text-[10px] font-mono text-[var(--color-text-muted)] tabular">
                        {rec.pmid ? `PMID ${rec.pmid}` : rec.nct_id ? rec.nct_id : 'openFDA FAERS'}
                      </span>
                      {rec.url ? (
                        <a
                          href={rec.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="flex items-center gap-1 text-[11px] font-semibold text-[#0271b0] hover:underline"
                        >
                          View <ExternalLink className="w-3 h-3" />
                        </a>
                      ) : (
                        <span className="flex items-center gap-1 text-[11px] font-semibold text-[var(--color-text-muted)]">
                          Details <ChevronRight className="w-3 h-3" />
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </main>

        {/* ── DETAIL PANEL (slides in on click) ── */}
        {selectedRecord && (
          <aside className="hidden xl:flex w-80 flex-shrink-0 border-l border-[var(--color-border-subtle)] bg-[var(--color-surface-card)] p-5 flex-col space-y-4 overflow-y-auto">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Record Detail</span>
              <button
                type="button"
                onClick={() => setSelectedRecord(null)}
                className="p-1 rounded-lg hover:bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                {selectedRecord.source && (
                  <span
                    className="text-[11px] font-bold px-2 py-0.5 rounded-full text-white inline-block mb-2"
                    style={{ backgroundColor: SOURCES.find((s) => s.key === selectedRecord.source)?.color || '#64748b' }}
                  >
                    {selectedRecord.source}
                  </span>
                )}
                <h3 className="text-sm font-bold text-[var(--color-text-primary)] leading-snug">
                  {selectedRecord.title}
                </h3>
              </div>

              {selectedRecord.evidence_level && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-[var(--color-text-muted)]">Risk Level:</span>
                  <RiskBadge severity={selectedRecord.evidence_level} size="sm" />
                </div>
              )}

              {(selectedRecord.pmid || selectedRecord.nct_id) && (
                <div className="flex items-center gap-2 text-[11px] font-mono text-[var(--color-text-muted)]">
                  <FileText className="w-3.5 h-3.5" />
                  {selectedRecord.pmid ? `PMID: ${selectedRecord.pmid}` : selectedRecord.nct_id}
                </div>
              )}

              <div className="p-3 rounded-xl bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)]">
                <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed">
                  {selectedRecord.summary || selectedRecord.findings || 'No summary available.'}
                </p>
              </div>

              {selectedRecord.url && (
                <a
                  href={selectedRecord.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-[#0271b0] text-white text-sm font-bold hover:bg-[#025f93] transition-colors"
                >
                  View Full Record <ExternalLink className="w-4 h-4" />
                </a>
              )}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
};

export default EvidenceExplorer;
