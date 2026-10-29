import axios from 'axios';

// Resolve central backend API base URL
const rawUrl = (
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  'http://127.0.0.1:8000'
).trim().replace(/\/+$/, '');

const API_BASE_URL = rawUrl === '' || rawUrl === '/api'
  ? '/api'
  : (rawUrl.endsWith('/api') ? rawUrl : `${rawUrl}/api`);

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 35000,
});

// Intercept requests to attach JWT access token if present
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('curenova_token');
    if (token && token.trim()) {
      const cleanToken = token.trim();
      if (config.headers && typeof config.headers.set === 'function') {
        config.headers.set('Authorization', `Bearer ${cleanToken}`);
      } else {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${cleanToken}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Intercept responses for consistent error formatting and automatic session renewal
api.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const originalRequest = error.config;
    const status = error.response?.status;
    const detail = error.response?.data?.detail;
    const message =
      (typeof detail === 'string' ? detail : null) ||
      error.response?.data?.message ||
      error.message ||
      'Biomedical intelligence service temporarily unavailable.';

    // Check if error is 401 and request can be refreshed
    const url = originalRequest?.url || '';
    const isAuthRequest = url.includes('/auth/login') || url.includes('/auth/refresh') || url.includes('/auth/logout');

    if (status === 401 && originalRequest && !originalRequest._retry && !isAuthRequest) {
      const storedRefresh = localStorage.getItem('curenova_refresh_token');

      if (storedRefresh) {
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          })
            .then((newToken) => {
              if (originalRequest.headers && typeof originalRequest.headers.set === 'function') {
                originalRequest.headers.set('Authorization', `Bearer ${newToken}`);
              } else {
                originalRequest.headers = originalRequest.headers || {};
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
              }
              return api(originalRequest);
            })
            .catch((err) => Promise.reject(err));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
          // Direct axios call to avoid interceptor recursion
          const refreshRes = await axios.post(
            `${API_BASE_URL}/auth/refresh`,
            { refresh_token: storedRefresh },
            { headers: { 'Content-Type': 'application/json' } }
          );

          const { access_token, refresh_token: newRefreshToken } = refreshRes.data;
          if (access_token) {
            localStorage.setItem('curenova_token', access_token);
            if (newRefreshToken) {
              localStorage.setItem('curenova_refresh_token', newRefreshToken);
            }
            if (originalRequest.headers && typeof originalRequest.headers.set === 'function') {
              originalRequest.headers.set('Authorization', `Bearer ${access_token}`);
            } else {
              originalRequest.headers = originalRequest.headers || {};
              originalRequest.headers.Authorization = `Bearer ${access_token}`;
            }
            processQueue(null, access_token);
            return api(originalRequest);
          }
        } catch (refreshErr) {
          processQueue(refreshErr, null);
          localStorage.removeItem('curenova_token');
          localStorage.removeItem('curenova_refresh_token');
          localStorage.removeItem('curenova_user');
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('curenova:session-expired'));
          }
          return Promise.reject(new Error('Session expired. Please log in again to continue your research.'));
        } finally {
          isRefreshing = false;
        }
      } else {
        // No refresh token available; clear stale credentials
        localStorage.removeItem('curenova_token');
        localStorage.removeItem('curenova_refresh_token');
        localStorage.removeItem('curenova_user');
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('curenova:session-expired'));
        }
      }
    }

    return Promise.reject(new Error(message));
  }
);

export const authService = {
  login: async (email, password) => {
    return api.post('/auth/login', {
      email: email.trim().toLowerCase(),
      password,
    });
  },
  register: async (userData) => {
    const payload = {
      email: userData.email.trim().toLowerCase(),
      password: userData.password,
      full_name: (userData.full_name || userData.name || '').trim(),
      role: (userData.role || 'patient').trim().toLowerCase(),
    };
    return api.post('/auth/signup', payload);
  },
  getMe: () => api.get('/auth/me'),
  refreshToken: (refreshToken) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
  logout: (refreshToken) =>
    api.post('/auth/logout', refreshToken ? { refresh_token: refreshToken } : {}),
  getUsers: () => api.get('/auth/users'),
  approveUser: (userId, approvalStatus) =>
    api.post(`/auth/users/${userId}/approve`, { approval_status: approvalStatus }),
};

export const adminService = {
  getUsers: () => api.get('/auth/users'),
  approveUser: (userId, approvalStatus) =>
    api.post(`/auth/users/${userId}/approve`, { approval_status: approvalStatus }),
};

const formatInvestigationResponse = (raw, query = '', searchType = 'drug_to_disease') => {
  if (!raw) return null;
  const synthesis = raw.structured_synthesis || {};
  const effectiveSearchType = raw.search_type || searchType;
  const isDrugFirst = effectiveSearchType === 'drug_to_disease' || raw.query_type === 'drug';
  const rawCandidates = raw.candidate_hypotheses || raw.candidates || [];

  return {
    analysis_id: raw.workflow_id,
    workflow_id: raw.workflow_id,
    query: query || raw.query_entity || raw.workflow_id,
    search_type: effectiveSearchType,
    query_type: raw.query_type || (isDrugFirst ? 'drug' : 'disease'),
    status: raw.status || 'completed',
    execution_duration_ms: raw.execution_duration_ms,
    disease_detected: isDrugFirst ? (rawCandidates[0]?.disease_name || 'Multiple Indications') : raw.query_entity,
    query_entity: raw.query_entity,
    queried_entity: raw.queried_entity || { name: raw.query_entity, type: raw.entity_type, query_type: raw.query_type },
    entity_type: raw.entity_type,
    ml_prediction_metadata: raw.ml_prediction_metadata || {},
    candidates: rawCandidates.map((c, idx) => {
      const candidateDisplayName = isDrugFirst ? (c.disease_name || c.candidate_name) : (c.drug_name || c.candidate_name);
      const subtitle = isDrugFirst
        ? `Investigated Drug: ${c.drug_name || raw.query_entity}`
        : (c.approval_status || 'Preclinical Repurposing Hypothesis');

      return {
        id: c.id,
        candidate_name: candidateDisplayName,
        candidate_label: isDrugFirst ? 'Proposed Indication' : 'Candidate Drug',
        drug_name: c.drug_name,
        disease_name: c.disease_name,
        original_indication: isDrugFirst ? (c.approval_status || 'Proposed Indication') : (c.approval_status || 'Preclinical Repurposing Hypothesis'),
        display_title: candidateDisplayName,
        display_subtitle: subtitle,
        curenova_ranking: c.curenova_ranking != null ? c.curenova_ranking : (c.prediction_score != null ? Math.round(c.prediction_score * 100) : null),
        prediction_score: c.prediction_score,
        score_type: c.score_type,
        ml_score_available: c.ml_score_available !== false && c.score_type !== 'curated_evidence_benchmark',
        confidence_interval: c.confidence_interval_low != null && c.confidence_interval_high != null
          ? `[${c.confidence_interval_low.toFixed(2)}, ${c.confidence_interval_high.toFixed(2)}]`
          : 'N/A',
        confidence_interval_low: c.confidence_interval_low,
        confidence_interval_high: c.confidence_interval_high,
        evidence_strength: c.evidence_strength || (c.evidence_count >= 3 ? 'high' : c.evidence_count >= 1 ? 'moderate' : 'low'),
        evidence_count: c.evidence_count,
        mechanism_summary: c.rationale || c.biological_mechanism || synthesis.proposed_mechanism || 'Target kinase signaling modulation',
        biological_mechanism: c.biological_mechanism,
        evidence_passages: synthesis.validated_citations || [],
        safety_signals: synthesis.safety_concerns || [],
        missing_data: synthesis.missing_information || [],
        epistemic_uncertainty: c.epistemic_uncertainty,
        aleatoric_uncertainty: c.aleatoric_uncertainty,
        calibration_status: c.calibration_status,
        is_bookmarked: c.is_bookmarked,
        rank: c.rank || idx + 1,
        status: c.status,
        molecular_features: c.molecular_features || null,
      };
    }),
    synthesis_report: raw.synthesis_report,
    completed_steps: raw.completed_steps || [],
    provenance_mode: raw.provenance_mode,
    llm_provider: raw.llm_provider,
    limitations_and_boundary_warning: raw.limitations_and_boundary_warning,
    structured_synthesis: synthesis,
    transcriptomic_connectivity: raw.transcriptomic_connectivity || null,
    clinical_trial_challenge: raw.clinical_trial_challenge || null,
  };
};

export const repurposingService = {
  getDiseases: () => api.get('/candidates'),
  analyze: async (query, minEvidence = 'all', searchType = 'drug_to_disease') => {
    const cleanQuery = encodeURIComponent(query.trim());
    const cleanSearchType = encodeURIComponent(searchType || 'drug_to_disease');
    const raw = await api.post(`/candidates/investigate?query=${cleanQuery}&search_type=${cleanSearchType}`, {});
    return formatInvestigationResponse(raw, query, searchType);
  },
  getResult: (id) => api.get(`/candidates/${id}`),
  getInvestigation: async (workflowId) => {
    const raw = await api.get(`/candidates/investigation/${workflowId}`);
    return formatInvestigationResponse(raw, raw.query_entity || raw.workflow_id, raw.search_type);
  },
  listInvestigations: (limit = 20) => api.get('/candidates/investigations', { params: { limit } }),
  downloadCandidateReport: (candidateId) =>
    api.get(`/reports/candidate/${candidateId}/markdown`, { responseType: 'blob' }),
  downloadInvestigationReport: (workflowId) =>
    api.get(`/reports/investigation/${workflowId}/markdown`, { responseType: 'blob' }),
  toggleBookmark: (id) => api.post(`/candidates/${id}/bookmark`),
  addNote: (candidateId, content) => api.post(`/candidates/${candidateId}/notes`, { content }),
  deleteNote: (noteId) => api.delete(`/candidates/notes/${noteId}`),
};

export const safetyService = {
  getCatalog: () => api.get('/patient/medicines'),
  analyze: async (medications, patientContext = null, roleView = 'doctor') => {
    const medList = Array.isArray(medications) ? medications : [medications];
    const medNames = medList
      .map((m) => (typeof m === 'string' ? m : m.name || m.drug_name || ''))
      .filter(Boolean);

    try {
      const endpoint = roleView === 'patient' ? '/patient/regimen/safety-check' : '/doctor/safety/analyze-regimen';
      const res = await api.post(endpoint, {
        medications: medNames,
        patient_context: patientContext,
      });
      return {
        ...res,
        medications: medList,
        patient_context: patientContext,
        role_view: roleView,
      };
    } catch (err) {
      // Fallback query to /doctor/interactions if analyze-regimen is unavailable
      const names = medNames.join(',');
      const ddis = await api.get('/doctor/interactions', {
        params: names ? { drug_names: names } : {},
      });

      const ddiArray = Array.isArray(ddis) ? ddis : [];
      const hasMajor = ddiArray.some(
        (d) => d.severity?.toLowerCase() === 'contraindicated' || d.severity?.toLowerCase() === 'major'
      );

      return {
        analysis_id: `safe-${Date.now()}`,
        overall_risk_category: hasMajor ? 'High Risk' : (ddiArray.length > 0 ? 'Moderate Risk' : 'Low Risk'),
        overall_risk_score: hasMajor ? 75.0 : (ddiArray.length > 0 ? 35.0 : 0.0),
        summary_headline: ddiArray.length > 0
          ? `Identified ${ddiArray.length} potential interaction signal(s) among evaluated medications.`
          : 'No critical drug-drug interactions detected in curated pharmacovigilance database.',
        pairwise_interactions: ddiArray.map((d) => ({
          drug_a: d.drug_a,
          drug_b: d.drug_b,
          severity: d.severity,
          mechanism: d.mechanism,
          clinical_recommendation: d.recommendation,
          source: d.verified_source,
          url: d.source_url,
        })),
        unmonitored_pairs: [],
        medications: medList,
        patient_context: patientContext,
        role_view: roleView,
      };
    }
  },
  getResult: (id) => api.get('/doctor/overview'),
  getTrials: (params) => api.get('/doctor/clinical-trials', { params }),
  getLiveTrials: (params) => api.get('/doctor/clinical-trials/live', { params }),
  getAdverseEvents: (drug, limit = 5) => api.get('/doctor/adverse-events', { params: { drug, limit } }),
  simulateTwin: async (baselineMedications, addedDrugs = [], removedDrugs = [], patientContext = null) => {
    const combined = [
      ...baselineMedications.filter((m) => !removedDrugs.includes(m)),
      ...addedDrugs,
    ];
    return safetyService.analyze(combined, patientContext, 'doctor');
  },
};

export const patientService = {
  getMedicines: (search) => api.get('/patient/medicines', { params: search ? { search } : {} }),
  getMedicineGuide: (name) => api.get(`/patient/medicines/${encodeURIComponent(name)}`),
  getRegimen: () => api.get('/patient/regimen'),
  addMedication: (data) => api.post('/patient/regimen', data),
  removeMedication: (id) => api.delete(`/patient/regimen/${id}`),
  toggleDose: (id) => api.post(`/patient/regimen/${id}/toggle`),
  explainResearch: (data) => api.post('/patient/explain-research', data),
  getOverview: () => api.get('/patient/overview'),
};

export const evidenceService = {
  search: (params) => api.get('/evidence', { params }),
  synthesize: (evidenceIds) => api.post('/evidence/synthesize', evidenceIds),
  searchLivePubmed: (query, maxResults = 5) =>
    api.get('/evidence/pubmed-live', { params: { query, max_results: maxResults } }),
};

export const graphService = {
  getOverview: (entityType = null, maxNodes = 60) =>
    api.get('/graph', { params: { node_type: entityType } }),
  getNodeSubgraph: (entityId) => api.get(`/graph/neighbors/${entityId}`),
};

export const feedbackService = {
  submit: (feedbackData) => api.post('/feedback', feedbackData),
  list: (params) => api.get('/feedback', { params }),
  evaluate: (params) => api.post('/feedback/evaluate', null, { params }),
};

export const metaService = {
  getHealth: () => api.get('/system/health'),
  getReady: () => api.get('/system/ready'),
  getSystemStatus: () => api.get('/system/status'),
  getDrug: (id) => api.get(`/candidates/${id}`),
  searchDrugs: (q) => api.get('/candidates', { params: { drug: q } }),
};

export default api;
