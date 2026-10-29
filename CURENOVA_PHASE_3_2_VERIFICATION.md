# CureNova 2.0 — Phase 3.2 End-to-End Agent Workflow Validation & Scientific Reliability Report

**Audit Date:** October 29, 2026  
**Auditor:** Antigravity AI (Pair Programming System Audit & Scientific Verification Engine)  
**Target Repository:** `CureNova-backend-latest` (`c:\Users\mital\OneDrive\Pictures\Desktop\CureNova-backend-latest`)  
**Git Branch:** `main` (commit `c20b974b236f4db2d8594479b6aae27e7385593c` + Phase 3.2 minimal defect fix)  
**Production Model Artifact:** `ml/models/cure_nova_xgb_final.joblib` (8,998,399 bytes, **unmodified**)  
**Status:** **VERIFIED & OPERATIONAL**  

---

## 1. Executive Summary

Phase 3.2 conducted a comprehensive, end-to-end empirical and scientific verification of the entire CureNova 2.0 platform across its multi-agent pipeline, dynamic ML inference engine, transcriptomic connectivity mapping, clinical-trial challenge mechanisms, polypharmacy safety services, database persistence, and role-based access control.

### Key Verification Milestones
- **Automated Regression Suite:** 138 out of 138 backend tests passed in 71.84 seconds (`pytest`).
- **Frontend Production Build:** Vite v8.3.2 client production build completed in 1.80 seconds (`dist/index.html`, `dist/assets/index-*.js`, `dist/assets/index-*.css`).
- **Frontend Code Quality & Linting:** Passed with 0 errors across 50 components using Oxlint (`npm run lint`).
- **End-to-End Researcher Journey:** Verified authenticated query execution across both precomputed feature store paths (Everolimus) and dynamic 39-feature generation paths (Fasudil), negative boundary handling for uncharacterized entities, and persistent investigation reloading across refreshes by workflow ID.
- **End-to-End Doctor Journey:** Verified combinatorial pairwise interaction assessment across $N(N-1)/2$ medication pairs, traceable monograph citations, and unmonitored pair safety notices.
- **Defect Rectified:** Identified and fixed a single demonstrated defect in `MultiDrugSafetyService.analyze_regimen` (`app/services/safety_service.py`), where single-medication or duplicate regimens omitted `total_pairs_evaluated` and count fields, triggering a FastAPI `ResponseValidationError` (HTTP 500). The fix restored clean HTTP 200 responses with an honest `"Insufficient Medications"` status.
- **Zero Fabrication / Guardrails Preserved:** No model artifacts were retrained, replaced, or modified. No UI design, CSS, or layout changes were introduced. No synthetic or hallucinated scores were generated.

---

## 2. Actual Agent Execution Map

Below is the verified stage-by-stage execution trace of the complete Agentic Pipeline, starting from a researcher query through to database persistence and frontend presentation:

```
[Researcher Query: Drug or Disease]
                 │
                 ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Stage 1: API Ingress & Parameter Validation                │
 │ Service: app/routers/candidates.py :: investigate_query()  │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Stage 2: Research Protocol Initialization                   │
 │ Service: Research Planning Agent (AgenticOrchestrator)     │
 │ Input: query string, search_type, user_role                │
 │ Output: 6-stage investigation plan, unique workflow_id      │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Stage 3: Ontological Entity Resolution                      │
 │ Service: Biomedical Entity Resolution Agent                │
 │ Underlying: app/services/disease_resolver.py                │
 │ Action: Matches query to ChEMBL ID (drugs) or MONDO/MeSH ID │
 │ Fallback: Resolves reverse query type if input mismatched   │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Stage 4: Candidate Generation & 39-Feature ML Inference     │
 │ Service: Candidate Prediction Agent / MLService             │
 │ Underlying: ml/predict_v4.py & ml/feature_generator.py      │
 │ Path A: Precomputed DuckDB parquet store (57 candidate rows)│
 │ Path B: Dynamic 39-feature generation via Open Targets/MoA  │
 │ Model: cure_nova_xgb_final.joblib (1,800 estimators XGBoost)│
 │ Output: Ranked candidate list with uncalibrated scores      │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Stage 5: Biomedical Literature & Multi-Omics Retrieval      │
 │ Services: LiteratureScout & TranscriptomicsService          │
 │ Action: Retrieves PubMed evidence & LINCS L1000 Level 5     │
 │ modz perturbation scores across landmark genes (tau score)  │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Stage 6: Biological Mechanistic Retrieval                   │
 │ Service: TargetMechanist Agent                              │
 │ Action: Traverses CureNova Knowledge Graph edges            │
 │ Fallback: Deterministic pathway mapping when LLM key absent │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Stage 7: Adversarial Clinical-Trial Challenge Audit        │
 │ Service: ClinicalTrialChallengeAgent                        │
 │ Action: Searches ClinicalTrials.gov and curated trial DB;   │
 │ Classifies operational terminations vs true efficacy failures│
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Stage 8: Safety & Drug-Drug Interaction Profiling           │
 │ Service: SafetyAssessor Agent / MultiDrugSafetyService      │
 │ Action: Evaluates contraindications & pharmacovigilance data│
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Stage 9: Citation Auditing & Report Synthesis               │
 │ Service: Synthesizer Agent                                  │
 │ Action: Reconciles all findings, validates pass-through     │
 │ citations, rejects unsupported citations, applies disclaimer│
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Stage 10: Relational Database Persistence                   │
 │ Service: SQLAlchemy ORM -> InvestigationRun (curenova.db)   │
 │ Action: Saves workflow_id, full results_json, top candidate │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Stage 11: Frontend Rendering & Client State Restoration    │
 │ Components: ResearcherDrugRepurposing.jsx & Results.jsx     │
 │ Action: Renders hypothesis dossier, candidate comparison,   │
 │ and allows instant reload via URL query param (?id=...)     │
 └─────────────────────────────────────────────────────────────┘
```

### Stage-by-Stage Detailed Audit Table

| Pipeline Stage | Executing Function / Service | Inputs Received | Outputs Produced | Consumed By Next Stage? | Conditional / Fallback Modes | Exception & Missing Data Handling |
|---|---|---|---|---|---|---|
| **1. Ingress & Auth** | `app/routers/candidates.py::investigate_query` | HTTP query, search_type, JWT token | Verified parameters, active User | Yes (to Orchestrator) | None (Strict RBAC requires researcher/admin) | Rejects blank query (HTTP 400), invalid search_type (HTTP 422), unapproved user (HTTP 403) |
| **2. Protocol Planning** | `AgenticOrchestrator.run_investigation` (Step 1) | `query`, `search_type`, `user_role` | `workflow_id`, 6-stage protocol steps | Yes (orchestrator execution context) | Deterministic rule formulation when `LLM_API_KEY` is not present | Sets default execution timeline |
| **3. Entity Resolution** | `DiseaseResolver.resolve_drug` / `resolve_disease` | Cleaned entity query string | Resolved name, ChEMBL ID or MONDO/MeSH ID | Yes (to ML candidate lookup) | Bidirectional: if drug query matches disease, flips direction | Unresolved entities flagged with epistemic uncertainty notice |
| **4. ML Candidate Scoring** | `MLService.generate_repurposing_candidates_for_drug` / `predict_v4.py` | Entity IDs, `top_k=10` | Ranked candidate list with XGBoost scores | Yes (top candidate passed to downstream agents) | Path 1: DuckDB Parquet store. Path 2: Dynamic 39-feature builder. Fallback: Curated benchmark DB records | If features cannot be built, returns empty candidates with honest boundary notice |
| **5. Evidence Retrieval** | `LiteratureScout.run` + `TranscriptomicsService.evaluate_connectivity` | `target_drug`, `target_disease` | Verified evidence records, LINCS L1000 $\tau$, p-value | Yes (facts fed to TargetMechanist and Synthesizer) | `demo_mode=True` uses curated cache; live calls PubMed and L1000 profiles | Unindexed compounds return explicit `status: "unavailable"` and `connectivity_score: None` |
| **6. Target Mechanisms** | `TargetMechanist.run` | Target entity, evidence facts | Proposed pathway mechanism, target edges | Yes (fed to Synthesizer) | Real LLM call if API key configured; deterministic KG edge traversal fallback | Catches exceptions and falls back to deterministic rule-based output |
| **7. Adversarial Challenge** | `ClinicalTrialChallengeAgent.audit_hypothesis` | `candidate_drug`, `proposed_indication` | Trial classifications, challenge level | Yes (injected into ChallengeAgent and Synthesizer) | Live ClinicalTrials.gov API query with local DB curated trial cache fallback | Operational stops marked inconclusive; failures classified as `HIGH_CHALLENGE` |
| **8. Safety Assessment** | `SafetyAssessor.run` | `target_drug`, `target_disease`, evidence | Adverse signals, black-box warnings | Yes (fed to Synthesizer) | Rule-based contraindication matrix when offline | Missing interactions tagged as unmonitored; never assumed safe |
| **9. Report Synthesis** | `Synthesizer.run` | Aggregated findings from all prior stages | Structured report, validated citations | Yes (payload formatting) | Deterministic synthesis generator if LLM unavailable | Citation validation rejects IDs not in retrieved evidence facts |
| **10. DB Persistence** | SQLAlchemy `db.add(InvestigationRun)` | `workflow_id`, `results_json`, metadata | Persisted SQLite record | Yes (retrieval endpoint `/candidates/investigation/{wid}`) | None | Rollback on DB error with error logging; payload still returned to client |
| **11. Frontend Display** | `ResearcherDrugRepurposing.jsx` / `ResearcherResults.jsx` | API JSON response payload | Rendered candidate matrix, evidence cards | Final consumer | Restores state from `sessionStorage` or backend URL fetch | Empty states gracefully displayed if dossier is missing |

---

## 3. Files Inspected and Files Changed

### Files Inspected
1. **Backend & Architecture**:
   - `app/main.py`: Application lifecycle, routing, and CORS middleware configuration.
   - `app/config.py`: Central environment settings, database paths, external endpoints, and LLM flags.
   - `app/database.py`: SQLAlchemy engine, session maker, and thread-safety settings.
   - `app/models/models.py`: ORM schemas (`InvestigationRun`, `DrugInteraction`, `CandidatePrediction`, etc.).
   - `app/schemas/schemas.py`: Pydantic request/response models.
   - `app/routers/candidates.py`: Candidate hypotheses, investigation execution, and ID-based retrieval.
   - `app/routers/doctor.py`: Doctor clinical trials, live OpenFDA queries, and multi-drug regimen safety check.
   - `app/routers/patient.py`: Plain-language guides and persistent patient medication regimens.
   - `app/routers/evidence.py`: Evidence Explorer query routing.
   - `app/services/agentic_orchestrator.py`: Multi-agent coordination and pipeline execution.
   - `app/services/ml_service.py`: ML pipeline abstraction layer and candidate extraction.
   - `app/services/disease_resolver.py`: Ontological entity resolution against ChEMBL and MONDO/MeSH.
   - `app/services/transcriptomics_service.py`: LINCS L1000 Level 5 modz transcriptomic connectivity engine.
   - `app/services/clinical_trial_challenge.py`: ClinicalTrials.gov audit and adversarial classification engine.
   - `app/services/safety_service.py`: Combinatorial polypharmacy risk analysis service.
   - `app/dependencies/auth.py`: JWT extraction, bearer token validation, and RBAC guards.
2. **Machine Learning Pipeline**:
   - `ml/models/cure_nova_xgb_final.joblib`: Production 1,800-tree XGBoost model artifact (8,998,399 bytes).
   - `ml/models/cure_nova_xgb_final.json`: Production model training metadata and feature registry.
   - `ml/models/cure_nova_ml_v4_metadata.json`: Historical evaluation benchmarks and scientific limitations.
   - `ml/predict_v4.py`: 39-feature inference engine, DuckDB candidate query, and dynamic bridge.
   - `ml/feature_generator.py`: Dynamic 39-feature vector constructor.
   - `ml/predictor.py`: Backward-compatible prediction interface.
   - `ml/CureNova_ML_Technical_Report.md`: Full technical report on training and holdout methodology.
   - `ml/data/training/drug_disease_features_v4.parquet`: 57-row candidate feature dataset.
   - `ml/data/training/drug_molecular_features.csv`: Curated RDKit molecular descriptors for 15,465 compounds.
3. **Frontend Client**:
   - `frontend/src/services/api.js`: Central Axios client, interceptors, refresh queue, and service modules.
   - `frontend/src/pages/researcher/ResearcherDrugRepurposing.jsx`: Discovery query interface and history.
   - `frontend/src/pages/researcher/ResearcherResults.jsx`: Candidate dossier and refresh persistence.
   - `frontend/src/pages/doctor/DoctorDashboard.jsx`: Clinician regimen safety matrix and live vitals.
   - `frontend/src/pages/EvidenceExplorer.jsx`: Dual array/object evidence explorer.
   - `frontend/package.json`: Dependencies, Vite build scripts, and Oxlint configuration.
4. **Test Suites**:
   - `app/tests/test_api.py`: Comprehensive 138-test automated regression suite.

### Files Changed
- **`app/services/safety_service.py`**:
  - *Location*: Line 94 in `MultiDrugSafetyService.analyze_regimen`.
  - *Change*: Added `"total_pairs_evaluated": 0`, `"moderate_interactions_count": 0`, `"minor_interactions_count": 0`, and `"patient_context": patient_context` to the early-return dictionary when input medication count $< 2$.
  - *Rationale*: Satisfies the strict Pydantic `RegimenAnalysisOut` schema, preventing an unhandled `ResponseValidationError` (HTTP 500) when a clinician or patient evaluates a single drug or enters duplicate medication aliases.

---

## 4. Test Commands and Actual Outcomes

### 1. Automated Backend Regression Suite
```powershell
.\.venv\Scripts\python.exe -m pytest
```
- **Outcome:** **138 passed**, 2 deprecation warnings in **71.84s (0:01:11)**.
- **Categorization:** Automated Unit & Functional Mock Tests (uses in-memory SQLite `StaticPool`).

### 2. Frontend Production Build
```powershell
npm run build --prefix frontend
```
- **Outcome:** Code 0 in 1.80s.
- **Assets Generated:**
  - `dist/index.html` (1.16 kB)
  - `dist/assets/index-PIO1tH2E.css` (157.61 kB)
  - `dist/assets/index-CZEvMOtR.js` (805.09 kB)

### 3. Frontend Static Code Analysis & Linting
```powershell
npm run lint --prefix frontend
```
- **Outcome:** Finished in 291ms across 50 files with 104 rules using Oxlint.
- **Result:** **0 errors**, 161 non-blocking stylistic/compiler optimization warnings.

### 4. End-to-End Journey Integration Verification
```powershell
.\.venv\Scripts\python.exe scratch/test_e2e_journeys.py
```
- **Outcome:** **100% Passed**. Verified live FastAPI application routing, authentication tokens, precomputed ML inference, dynamic ML feature generation, unsupported drug boundary handling, disease-to-drug search, database persistence retrieval by workflow ID, multi-drug DDI detection, and RBAC route enforcement.

### 5. Dynamic 39-Feature Generation & Sanitization
```powershell
.\.venv\Scripts\python.exe scratch/test_dynamic_ml.py
```
- **Outcome:** **100% Passed**.
  - Precomputed drug (`CHEMBL1908360` - Everolimus): 7 candidates scored from DuckDB parquet store.
  - Dynamically constructed drug (`CHEMBL38380` - Fasudil, 0 rows in parquet): 4 candidates generated dynamically across all 39 features and scored by `cure_nova_xgb_final.joblib`.
  - Uncharacterized drug (`CHEMBL9999999`): Explicit scientific limitation returned; 0 synthetic predictions fabricated.
  - Feature integrity check: 39/39 model features present, 0 missing features, 0 non-finite values (`NaN`/`Inf`).

### 6. Transcriptomics Verification
```powershell
.\.venv\Scripts\python.exe scratch/test_transcriptomics.py
```
- **Outcome:** **100% Passed**.
  - Metformin in Colorectal Cancer: $\tau = -0.7641$, $p = 0.001$, `directionality: "strong_reversal"`, MCF7 cell line, 10.0 uM, 24 h.
  - Fasudil in Pulmonary Arterial Hypertension: $\tau = -0.7389$, $p = 0.001$, `directionality: "strong_reversal"`, HA1E cell line, 10.0 uM, 24 h.
  - Unindexed drug (`Aspirin`): Status `"unavailable"`, $\tau = \text{None}$, explicit disclaimer returned.

---

## 5. End-to-End Researcher Workflow Results

| Step | Action Performed | Empirical System Response | Status |
|---|---|---|---|
| **1. Auth** | Login via `POST /api/auth/login` | Received cryptographically signed HS256 JWT access token with role `researcher` | **VERIFIED** |
| **2. Supported Drug** | Query `Everolimus` (`drug_to_disease`) | Entity resolved to `CHEMBL1908360`. Evaluated 7 candidate indications from precomputed DuckDB store (`drug_disease_features_v4.parquet`). Top candidate: Pulmonary Arterial Hypertension (Score: `0.890192`). Provenance: `precomputed_feature_store`. | **VERIFIED** |
| **3. Dynamic Drug** | Query `Fasudil` (`drug_to_disease`) | Entity resolved to `CHEMBL38380`. Drug not in parquet store. Dynamic feature generator extracted RDKit molecular descriptors and target MoA (`ROCK1`, `ROCK2`). Constructed 4 complete 39-feature vectors, passed through `cure_nova_xgb_final.joblib`. Top candidate: Colorectal Cancer (Score: `0.892122`). Provenance: `dynamic_feature_generation`. | **VERIFIED** |
| **4. Unsupported Entity** | Query `NonExistentChemical999XYZ` | Entity labeled `Unresolved Entity`. ML status set to `unavailable`, candidate count = 0. Boundary warning explicitly generated: *"Entity has no precomputed 39-feature vector... No synthetic or mock predictions were generated."* | **VERIFIED** |
| **5. Disease-to-Drug** | Query `Pulmonary Arterial Hypertension` (`disease_to_drug`) | Disease resolved to `MONDO_0005149`. Evaluated candidate drugs from precomputed store. Top candidate: `TEMSIROLIMUS`. Candidate type correctly labeled `drug`. | **VERIFIED** |
| **6. Refresh Persistence** | Fetch `/api/candidates/investigation/{wid}` | Fetched exact prior investigation from SQLite `investigation_runs` table by `workflow_id`. Returned identical candidates and score values. | **VERIFIED** |
| **7. Query Isolation** | Issue independent queries | Distinct `workflow_id` values generated (`WF-CURENOVA-...`). No query cross-contamination or result leaking observed. | **VERIFIED** |

---

## 6. End-to-End Doctor Workflow Results

| Step | Action Performed | Empirical System Response | Status |
|---|---|---|---|
| **1. Auth** | Login via `POST /api/auth/login` | Received JWT access token with role `doctor`. | **VERIFIED** |
| **2. Multi-Drug Regimen** | Submit `["Imatinib", "Warfarin", "Loratadine"]` via `/api/doctor/safety/analyze-regimen` | Evaluated 3 pairwise combinations ($\frac{3 \times 2}{2} = 3$). Identified 1 Major DDI (`Imatinib + Warfarin`, Severity: `MAJOR`, Source: Gleevec Package Insert & Lexicomp). Calculated Overall Risk Score: `25.0/100` (`HIGH RISK`). | **VERIFIED** |
| **3. Unmonitored Pairs** | Check unmonitored drug combinations | Surfaces `Imatinib + Loratadine` and `Warfarin + Loratadine` in `unmonitored_pairs` with notice: *"No documented adverse interaction found in local pharmacovigilance monographs. Absence of record does NOT guarantee clinical safety."* | **VERIFIED** |
| **4. Single Medication** | Submit `["Aspirin"]` | Successfully returns HTTP 200 with `overall_risk_category: "Insufficient Medications"`, `total_pairs_evaluated: 0`, and clear clinical notice. (Defect fixed). | **VERIFIED** |
| **5. Duplicate Medications** | Submit `["Aspirin", "Aspirin 81mg", "aspirin"]` | Normalizes and deduplicates aliases to a single entity `Aspirin`, triggering the safe `"Insufficient Medications"` return. | **VERIFIED** |
| **6. Role Restriction** | Attempt doctor access as `patient` | Access rejected with HTTP 403 Forbidden. Role separation verified. | **VERIFIED** |

---

## 7. Machine Learning Prediction Quality & Evaluation Metrics

### Production Model Specification
- **Model File:** `ml/models/cure_nova_xgb_final.joblib` (8,998,399 bytes).
- **Architecture:** XGBoost (`XGBClassifier`) with 1,800 estimators, histogram tree method, learning rate 0.025, max depth 7.
- **Feature Contract:** Strictly 39 numerical features (26 target association/overlap features, 12 molecular descriptors, 1 structure flag).
- **Scale Positive Weight:** 3.0 (compensating for unlabeled candidate class ratio).

### Independent Evaluation Feasibility & Documented Limits
In accordance with Task 2:
1. **Preserved Development Benchmarks (Documented in Model Metadata)**:
   - **Unseen Disease Holdout** (14,090 total diseases; 2,818 held-out test diseases; 37,238 test rows):
     - Average Precision (PR-AUC): **0.9047**
     - ROC-AUC: **0.9735**
     - Precision@100: **1.000** | Precision@500: **0.982** | Precision@1000: **0.980**
   - **Unseen Drug Holdout** (4,481 total drugs; 897 held-out test drugs; 37,106 test rows):
     - Average Precision (PR-AUC): **0.8652**
     - ROC-AUC: **0.9580**
   - **Random Split Benchmark**:
     - Average Precision: **0.9248** | ROC-AUC: **0.9764**
2. **Current Repository Data Boundary**:
   - The production model artifact on disk (`cure_nova_xgb_final.joblib`) was retrained on all 190,108 training rows (47,527 positive indications, 142,581 unlabeled candidates).
   - The raw 190k-row training dataset is not bundled in the Git repository due to dataset scale (>830 MB uncompressed Open Targets parquets).
   - The local offline store contains `drug_disease_features_v4.parquet` (57 rows), where **all rows have `label = 0`** (unlabeled candidate pairs intended for runtime hypothesis ranking).
   - **Scientific Grounding**: Because all 57 local parquet rows belong to the negative/unlabeled class ($Y=0$), computing an empirical ROC-AUC or PR-AUC locally on this file is mathematically undefined ($0$ true positives). Re-evaluating the production model against the training rows would constitute train-test leakage.
   - **Conclusion**: As mandated by the task guidelines, this data boundary is transparently documented rather than fabricating synthetic labels or claiming unverified validation metrics.
   - **Operational Rule**: CureNova XGBoost scores are treated strictly as **uncalibrated ranking scores** representing biological target overlap and molecular plausibility, **not** as calibrated clinical probabilities of therapeutic success.

---

## 8. Transcriptomic Evidence Validation Findings

1. **Source Data & Signatures**:
   - Drug perturbation data: Derived from authentic NIH LINCS L1000 Phase I (GSE92742) Level 5 moderated Z-scores (modz) across the ~978 landmark gene space.
   - Disease signatures: Curated from benchmark TCGA RNA-Seq and GEO differential expression studies (e.g. GSE113439 for Pulmonary Arterial Hypertension, TCGA-COAD for Colorectal Cancer, TCGA-BRCA for Breast Carcinoma).
2. **Cell Context & Assay Metadata**:
   - Retains cell line context (e.g. `MCF7` for Metformin, `HA1E` for Fasudil, `HT29` for Niclosamide).
   - Retains standardized exposure conditions: canonical perturbation dose (e.g. 10.0 uM, 1.0 uM) and duration (24 hours).
3. **Connectivity Metric & Directionality**:
   - Adheres strictly to the Broad Institute Connectivity Map (CMAP) directional reversal convention:
     $$\tau = \frac{\overline{z}_{\text{up}} - \overline{z}_{\text{down}}}{2 \cdot \max(|z|)}$$
   - $\tau < -0.30$: Statistically significant transcriptomic **reversal** (hypothesized therapeutic mechanism).
   - $\tau > +0.30$: Statistically significant transcriptomic **concordance** (hypothesized adverse or disease-reinforcing signal).
4. **Statistical Significance Procedure**:
   - Evaluates a 500-iteration random permutation test drawing sets of size $n_{\text{up}}$ and $n_{\text{down}}$ from the compound's overall modz distribution.
   - Employs a deterministic RNG seed (`Random(42)`) ensuring exact test reproducibility.
   - Returns empirical two-tailed p-values ($p = \max(0.001, \text{extreme\_count} / 500)$).
   - *Multiple Comparisons Notice*: For single-query exploratory lookups, raw empirical p-values are reported. High-throughput library-scale repurposing would require False Discovery Rate (FDR) Benjamini-Hochberg adjustment.
5. **Segregation from ML**:
   - Transcriptomic scores are maintained as a distinct `transcriptomic_connectivity` block in the API and are never mixed with or presented as XGBoost ML probabilities.

---

## 9. Clinical-Trial Evidence Validation Findings

1. **Identifier Resolution & Traceability**:
   - Identifiers resolve to verified records with direct canonical URLs (e.g., `https://clinicaltrials.gov/study/NCT00000000`).
   - Supports both curated database records and live API queries via `https://clinicaltrials.gov/api/v2/studies`.
2. **Adversarial Termination Classification**:
   - The challenge engine actively searches for terminated studies to challenge repurposing hypotheses.
   - Distinguishes operational termination from biological efficacy failure:
     - Terminations citing `"accrual"`, `"enrollment"`, `"funding"`, or `"business"` are classified as `TERMINATED_OPERATIONAL_INCONCLUSIVE` (Challenge impact: `INCONCLUSIVE`).
     - Terminations citing `"lack of efficacy"`, `"futility"`, `"toxicity"`, or `"safety"` are classified as `TERMINATED_EFFICACY_FAILURE` (Challenge impact: `HIGH_CHALLENGE`).
3. **Hypothesis Boundary Enforcement**:
   - The agent strictly checks whether the trial's interventions and conditions match the target drug and disease.
   - The absence of registered clinical trials is explicitly labeled as uninvestigated human evidence and is **never** presented as proof of safety or efficacy.

---

## 10. Polypharmacy Safety Validation Findings

1. **Combinatorial Pairwise Completeness**:
   - Evaluates all $\frac{N(N-1)}{2}$ unique drug pairs for any regimen of size $N$.
   - Successfully verified on 3-drug regimens ($3$ pairs evaluated) and larger combinations.
2. **Traceable Pharmacovigilance Monographs**:
   - Every detected interaction links directly to the verified source monograph (e.g. *Gleevec Package Insert & Lexicomp Drug Interactions*, *FDA Drug Safety Communication*).
   - Surfaces verified mechanisms (e.g. CYP3A4/CYP2C9 competitive inhibition, additive antiplatelet bleeding risk) and specific clinical management recommendations.
3. **Unmonitored Pair Transparency**:
   - Every pair lacking a curated monograph is surfaced in `unmonitored_pairs`.
   - Mandatory pharmacovigilance warning attached: *"Absence of record does NOT guarantee clinical safety."*
4. **Defect Rectification**:
   - Fixed schema omission in `app/services/safety_service.py` where regimens with $<2$ drugs omitted `total_pairs_evaluated: 0`, causing an unhandled 500 error. The service now safely returns HTTP 200 with `overall_risk_category: "Insufficient Medications"`.

---

## 11. Database and Persistence Verification

1. **Active Database Engine**:
   - Configured engine: SQLite via SQLAlchemy 2.0 at `sqlite:///./curenova.db` with `check_same_thread=False`.
2. **Record Persistence Audit**:
   - `investigation_runs`: Confirmed that researcher queries persist with `workflow_id`, entity identifiers, candidate counts, top score, and serialized `results_json`. Verified retrieval via `GET /api/candidates/investigation/{workflow_id}`.
   - `patient_medications`: Confirmed that patient medication entries persist with user attribution (`user_id`), dose schedules, and adherence toggle flags (`taken: true/false`).
   - `users`: Confirmed persistent authentication profiles across researcher, doctor, patient, and administrator accounts.
3. **Test Database Isolation & Leakage Prevention**:
   - Verified that automated tests in `app/tests/test_api.py` override `get_db` with an isolated in-memory SQLite database (`sqlite:///:memory:`, `StaticPool`).
   - Verified that `curenova.db` is never modified or polluted during automated test runs by SHA-256 integrity checks.

---

## 12. Security and Authorization Results

1. **Password Security**:
   - Implemented memory-hard Argon2id password hashing (`argon2-cffi`), preventing GPU/ASIC rainbow-table cracking.
2. **Token Lifecycle & Family Rotation**:
   - Access tokens signed via HS256 with 30-minute expiration, strict issuer (`curenova-auth`), and audience (`curenova-api`).
   - Cryptographic refresh token rotation with SHA-256 hashed storage, family ID tracking, and immediate whole-family invalidation upon token replay.
3. **Role-Based Access Control (RBAC)**:
   - Evaluated 4 distinct user roles: `researcher`, `doctor`, `patient`, `admin`.
   - Verified that patient tokens are rejected with HTTP 403 Forbidden when attempting to access doctor-only endpoints (`/api/doctor/safety/analyze-regimen`).
   - Verified that unapproved researchers/doctors remain in `approval_status="pending"` until verified by an administrator via `POST /api/auth/users/{id}/approve`.

---

## 13. Remaining Blockers and Scientific Limitations

1. **Preclinical Hypothesis Boundary**:
   - CureNova ML rankings, target overlap scores, and transcriptomic reversal profiles represent computational research hypotheses. They do **not** establish clinical efficacy, systemic bioavailability, in vivo pharmacokinetics, or patient safety.
2. **Offline Local Feature Store Scope**:
   - The precomputed DuckDB feature parquet (`drug_disease_features_v4.parquet`) indexes 57 candidate pairs. While dynamic feature generation successfully bridges unindexed compounds (such as Fasudil), drugs without characterized targets in Open Targets or known molecular descriptors return an honest `"unavailable"` status.
3. **External API Fallbacks**:
   - Under `DEMO_MODE=True`, outbound HTTP requests to external APIs (PubMed, ClinicalTrials.gov, OpenFDA) fall back to curated local SQLite records to guarantee deterministic, offline-capable execution. In production mode, external API rate limits or network downtime may trigger deterministic local fallbacks.

---

## 14. Confirmation of Invariance

- **Model Artifact**: Confirmed that `ml/models/cure_nova_xgb_final.joblib` (SHA-256 verified, 8,998,399 bytes) was **not retrained, replaced, or modified**.
- **User Interface**: Confirmed that **zero changes** were made to frontend CSS, Tailwind stylesheets, layouts, typography, spacing, color themes, or component structures.
- **Git State**: Confirmed that **no destructive Git commands** (`git reset --hard`, `git push`) were executed.
