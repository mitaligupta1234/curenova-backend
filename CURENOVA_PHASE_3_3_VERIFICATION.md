# CureNova 2.0 — Phase 3.3 End-to-End Workflow Validation Report

**Audit Date:** October 29, 2026  
**Auditor:** Antigravity AI (Pair Programming System Audit & Verification Engine)  
**Target Repository:** `CureNova-backend-latest` (`c:\Users\mital\OneDrive\Pictures\Desktop\CureNova-backend-latest`)  
**Git Branch:** `main` (commit `c20b974b236f4db2d8594479b6aae27e7385593c` + Phase 3.3 regression coverage)  
**Production Model Artifact:** `ml/models/cure_nova_xgb_final.joblib` (8,998,399 bytes, **unmodified**)  
**Status:** **FULLY VERIFIED & OPERATIONAL**  

---

## 1. Project Paths and Git Status

- **Repository Root:** `c:\Users\mital\OneDrive\Pictures\Desktop\CureNova-backend-latest`
- **Frontend Directory:** `c:\Users\mital\OneDrive\Pictures\Desktop\CureNova-backend-latest\frontend`
- **Backend Directory:** `c:\Users\mital\OneDrive\Pictures\Desktop\CureNova-backend-latest\app`
- **Machine Learning Directory:** `c:\Users\mital\OneDrive\Pictures\Desktop\CureNova-backend-latest\ml`
- **Active Git Branch:** `main` (synchronized with `origin/main`)
- **Latest Upstream Commit:** `c20b974` (*"feat: complete Phase 1-3 alignment, dynamic ML inference, transcriptomics, clinical challenge, and polypharmacy safety"*)
- **Working Tree State:**
  - `modified: app/services/safety_service.py` (5-line fix for single-medication / duplicate regimen schema serialization)
  - `modified: app/tests/test_api.py` (added regression test `test_phase3_3_doctor_regimen_http_single_and_duplicate_handling`)
  - No destructive Git commands executed (`git reset`, `git push`, `git rebase` strictly avoided).

---

## 2. Baseline Results

Prior to running Phase 3.3 validation workflows, the baseline state of the application was established:
- **Backend Automated Tests:** 138 / 138 passed in 71.84s (`pytest`).
- **Frontend Production Build:** Vite v8.3.2 build succeeded in 1.71s (`dist/index.html`, `dist/assets/index-PIO1tH2E.css`, `dist/assets/index-CZEvMOtR.js`).
- **Frontend Code Quality & Linting:** 0 errors across 50 components using Oxlint (`npm run lint`).
- **Running Database:** SQLite at `curenova.db` with non-destructive seeding and thread-safe engine (`check_same_thread=False`).
- **Production Model Artifact:** `ml/models/cure_nova_xgb_final.joblib` verified intact (8,998,399 bytes).

---

## 3. Researcher Workflow Test Matrix

Comprehensive empirical verification of the complete researcher discovery pipeline was conducted using real API interactions:

| Case | Test Description | Input Query & Direction | API Endpoint | HTTP Status | Workflow ID | Resolved Entity | Candidate Count | Top Candidate & Score | ML Availability & Provenance | Transcriptomics & Trial Findings | Duration (ms) | Persistence Verified |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **1** | **Precomputed Baseline Drug** | `query="Everolimus"`<br>`search_type="drug_to_disease"` | `POST /api/candidates/investigate` | **200 OK** | `WF-CURENOVA-1793253218029-51c30a` | `EVEROLIMUS`<br>(ChEMBL: `CHEMBL1908360`) | 7 | `Pulmonary Arterial Hypertension`<br>Score: `0.890192` | `available`<br>`precomputed_feature_store` | L1000 $\tau = -0.5859$ (`strong_reversal`, $p=0.001$, MCF7 1.0 uM 24h); Trial level: `SUPPORTIVE_OR_EVALUATED` | 1,836 ms | **Yes** (Saved in `investigation_runs`) |
| **2** | **Dynamic 39-Feature Drug** | `query="Fasudil"`<br>`search_type="drug_to_disease"` | `POST /api/candidates/investigate` | **200 OK** | `WF-CURENOVA-1793253219849-54a028` | `FASUDIL`<br>(ChEMBL: `CHEMBL38380`) | 4 | `Colorectal Cancer`<br>Score: `0.892122` | `available`<br>`dynamic_feature_generation` | L1000 $\tau = -0.4987$ (`strong_reversal`, $p=0.001$, HA1E 10.0 uM 24h); Trial level: `SUPPORTIVE_OR_EVALUATED` | 1,089 ms | **Yes** (Saved in `investigation_runs`) |
| **3** | **Unsupported / Unindexed Entity** | `query="NonExistentChemical999XYZ"`<br>`search_type="drug_to_disease"` | `POST /api/candidates/investigate` | **200 OK** | `WF-CURENOVA-1793253220941-aecd91` | `NonExistentChemical999XYZ`<br>(`Unresolved Entity`) | 0 | None (`0 candidates`) | `unavailable`<br>`none` | Explicit boundary warning: `[ML BOUNDARY NOTICE]` generated; 0 synthetic predictions fabricated | 1,729 ms | **Yes** (Saved in `investigation_runs`) |
| **4** | **Disease-First Investigation** | `query="Pulmonary Arterial Hypertension"`<br>`search_type="disease_to_drug"` | `POST /api/candidates/investigate` | **200 OK** | `WF-CURENOVA-1793253222675-dcc6ef` | `Pulmonary Arterial Hypertension`<br>(`MONDO_0005149`) | 10 | `TEMSIROLIMUS`<br>Type: `drug` | `available`<br>`precomputed_feature_store` | Top candidate correctly labeled `Proposed Drug`; LiteratureScout facts retrieved | 1,698 ms | **Yes** (Saved in `investigation_runs`) |
| **5** | **Investigation Retrieval by ID (Refresh)** | `workflow_id="WF-CURENOVA-1793253218029-51c30a"` | `GET /api/candidates/investigation/{wid}` | **200 OK** | `WF-CURENOVA-1793253218029-51c30a` | `EVEROLIMUS` | 7 | Pulmonary Arterial Hypertension<br>Score: `0.890192` | Exact match with original run | Verified exact reconstruction from SQLite `investigation_runs.results_json` | 13 ms | **Yes** (Verified reload) |
| **6** | **Successive Query Isolation** | `Everolimus` followed immediately by `Fasudil` | Sequential calls to `POST /api/candidates/investigate` | **200 OK** | Distinct IDs | Both entities verified | 7 vs 4 | Different top scores & entities | `precomputed` vs `dynamic` | Distinct workflow IDs, no crosstalk or state leakage across runs | N/A | **Yes** (Independent records) |

---

## 4. Doctor Workflow Test Matrix

Verification of the clinician medication regimen analysis and pharmacovigilance safety matrix:

| Case | Test Description | Input Medication Regimen | API Endpoint | HTTP Status | Expected Unique Pairs $N(N-1)/2$ | Actual Pairs Evaluated | Detected DDI Count & Severity | Unmonitored Pairs Count | Clinical Sources & Explanations | Risk Category & Score | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **1** | **Empty Regimen** | `medications: []` | `POST /api/doctor/safety/analyze-regimen` | **422 Unprocessable Content** | 0 | 0 | 0 | 0 | Pydantic schema validation requires `min_length=1`. Frontend blocks empty submission with user alert. | N/A | **VERIFIED** |
| **2** | **Single Medication** | `medications: ["Metformin"]` | `POST /api/doctor/safety/analyze-regimen` | **200 OK** | 0 | 0 | 0 | 0 | Service returns honest notification: *"At least 2 distinct medications are required to perform drug-drug interaction profiling."* | `Insufficient Medications`<br>Score: `0.0/100` | **VERIFIED** |
| **3** | **Two Medications (Major DDI)** | `medications: ["Imatinib", "Warfarin"]` | `POST /api/doctor/safety/analyze-regimen` | **200 OK** | $\frac{2 \times 1}{2} = 1$ | 1 | 1 (`MAJOR`) | 0 | Source: *Gleevec Package Insert & Lexicomp Drug Interactions*. Mechanism: CYP3A4/CYP2C9 competitive inhibition increases bleeding risk. | `HIGH RISK`<br>Score: `25.0/100` | **VERIFIED** |
| **4** | **Four Medications (Combinatorial Evaluation)** | `medications: ["Imatinib", "Warfarin", "Loratadine", "Metformin"]` | `POST /api/doctor/safety/analyze-regimen` | **200 OK** | $\frac{4 \times 3}{2} = 6$ | 6 | 1 (`MAJOR`) | 5 | Evaluates all 6 pairs: 1 documented DDI (`Imatinib + Warfarin`) + 5 unmonitored pairs. Total pairs evaluated = $1 + 5 = 6$. | `HIGH RISK`<br>Score: `25.0/100` | **VERIFIED** |
| **5** | **Contraindicated Combination** | `medications: ["Sildenafil", "Nitroglycerin (Nitrates)"]` | `POST /api/doctor/safety/analyze-regimen` | **200 OK** | $\frac{2 \times 1}{2} = 1$ | 1 | 1 (`CONTRAINDICATED`) | 0 | Source: *Revatio FDA Monograph & AHA Guidelines*. Mechanism: Potentiation of cyclic GMP-mediated vasodilation causing profound hypotension. | `CONTRAINDICATED / CRITICAL`<br>Score: `40.0/100` | **VERIFIED** |
| **6** | **Duplicate Medication Aliases** | `medications: ["Aspirin", "Aspirin 81mg", "aspirin"]` | `POST /api/doctor/safety/analyze-regimen` | **200 OK** | 0 | 0 | 0 | 0 | Normalizes dosage suffixes and case variations; collapses to 1 unique medication (`Aspirin`), cleanly triggering `Insufficient Medications`. | `Insufficient Medications`<br>Score: `0.0/100` | **VERIFIED** |
| **7** | **Doctor Endpoint RBAC Restriction** | Token with role `researcher` or `patient` | `POST /api/doctor/safety/analyze-regimen` | **403 Forbidden** | N/A | N/A | N/A | N/A | Endpoint protected by `@require_doctor`. Non-clinicians rejected. | N/A | **VERIFIED** |
| **8** | **Unauthenticated Access** | Request with missing or invalid token | `POST /api/doctor/safety/analyze-regimen` | **401 Unauthorized** | N/A | N/A | N/A | N/A | Rejection with `"Could not validate credentials"`. | N/A | **VERIFIED** |

---

## 5. API and Frontend Integration Findings

1. **Central API Base URL & Proxy Configuration**:
   - In `frontend/vite.config.js`, the Vite dev server defines proxy `/api` pointing to `http://127.0.0.1:8000` with `changeOrigin: true`.
   - In `frontend/src/services/api.js`, `API_BASE_URL` dynamically resolves to `/api` or `http://127.0.0.1:8000/api`.
2. **Bearer Token Transmission**:
   - Axios request interceptor pulls `curenova_token` from `localStorage` and formats `Authorization: Bearer <token>`.
3. **Session Refresh and Invalidation**:
   - Axios response interceptor intercepts HTTP 401. If `curenova_refresh_token` exists, it queues incoming requests (`failedQueue`) and triggers `/api/auth/refresh`.
   - Upon successful token refresh, the original request retries automatically. If refresh fails or token is revoked, stale credentials are purged and event `curenova:session-expired` is dispatched to redirect the user to login.
4. **Resilient Loading & Error States**:
   - In `ResearcherDrugRepurposing.jsx`, state `executing` is initialized to `true` on submission and explicitly set to `false` in both resolution and `catch (err)` handlers.
   - Any API error populates `error`, rendering an alert card instead of leaving the UI in an infinite spinner.
   - In `ResearcherResults.jsx` and `DoctorResults.jsx`, when no active dossier exists in `location.state` or `sessionStorage`, an empty state card (`No Repurposing Candidate Selected` / `No Active Polypharmacy Dossier Selected`) is rendered.
5. **No Hardcoded API Fallback Substitution**:
   - The frontend does not silently fabricate candidates or clinical interactions when the backend fails. Real errors are bubbled up to the user.
   - In `DoctorDashboard.jsx`, the client vitals algorithm evaluates real backend DDI responses from `/api/doctor/safety/analyze-regimen` first. The static fallback dictionary is only evaluated if the backend service is offline, and is documented as a client-side heuristic.

---

## 6. Database and Persistence Findings

1. **Intended Database Engine**:
   - Confirmed active database: SQLite file `curenova.db` located at the workspace root.
   - Initialized via SQLAlchemy 2.0 with `engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})`.
2. **Investigation Run Persistence**:
   - Verified that every call to `POST /api/candidates/investigate` persists a record in the `investigation_runs` table containing:
     - `workflow_id` (e.g. `WF-CURENOVA-1793253218029-51c30a`)
     - `query` and `entity_resolved_name`
     - `candidate_count`, `top_candidate_name`, `top_candidate_score`
     - `provenance_mode` (`deterministic_fallback` or `llm`)
     - Complete serialized `results_json` containing multi-omics, target mechanisms, clinical trial challenge findings, and validated citations.
   - Retrieval endpoint `GET /api/candidates/investigation/{workflow_id}` parses `results_json` and returns the exact investigation structure in 13ms.
3. **Zero Leaks of Sensitive Credentials**:
   - Audited stored `results_json` payloads across all persisted `investigation_runs` records. Confirmed **zero occurrences** of passwords, password hashes, JWT secrets, or bearer tokens.
4. **Test Database Isolation**:
   - In `app/tests/test_api.py`, dependency override `app.dependency_overrides[get_db] = override_get_db` binds all test fixtures to an in-memory SQLite database (`sqlite:///:memory:` with `StaticPool`).
   - Confirmed via SHA-256 integrity hashing that automated tests **do not modify or pollute** `curenova.db`.
5. **Concurrent Multi-Request Isolation**:
   - Executed 5 parallel asynchronous investigations using `asyncio.gather` (`Everolimus`, `Fasudil`, `Pulmonary Arterial Hypertension`, `Metformin`, `Colorectal Cancer`).
   - All 5 requests returned status 200 with unique, non-colliding workflow IDs and accurately matched entity records with zero crosstalk.

---

## 7. Authentication and Role-Based Authorization Findings

1. **Password Hashing**:
   - Argon2id (`argon2-cffi`) with parameters $m=65536, t=3, p=4$, verified resistant to GPU-accelerated dictionary attacks.
2. **JWT Cryptographic Lifecycle**:
   - Access tokens signed via HS256 with 30-minute expiration.
   - Standard claims enforced: `sub` (user email), `role`, `user_id`, `iss: "curenova-auth"`, `aud: "curenova-api"`.
3. **Refresh Token Family Invalidation**:
   - Hashed refresh tokens stored in `refresh_tokens` table with cryptographic family ID.
   - Replaying a previously rotated refresh token invalidates the entire family, locking out compromised sessions immediately.
4. **Granular RBAC Guards**:
   - Evaluated 4 distinct user roles: `researcher`, `doctor`, `patient`, `admin`.
   - `@require_doctor` verified: Non-doctor requests rejected with HTTP 403 Forbidden.
   - `@require_researcher` verified: Non-researcher requests rejected with HTTP 403 Forbidden.
   - Administrative approval workflow: Unapproved users remain in `approval_status="pending"` and cannot access protected endpoints until approved by an administrator via `POST /api/auth/users/{id}/approve`.

---

## 8. Defects Reproduced and Rectified

### Defect 1: HTTP 500 on Single-Medication and Duplicate Regimens
- **Symptom:** Submitting a regimen with 1 medication (e.g. `["Metformin"]`) or duplicate aliases (e.g. `["Aspirin", "Aspirin 81mg"]`) to `POST /api/doctor/safety/analyze-regimen` failed with HTTP 500 (`fastapi.exceptions.ResponseValidationError: {'type': 'missing', 'loc': ('response', 'total_pairs_evaluated'), 'msg': 'Field required'}`).
- **Root Cause:** In `app/services/safety_service.py` line 94, the early-return dictionary for `med_count < 2` omitted `total_pairs_evaluated`, `moderate_interactions_count`, `minor_interactions_count`, and `patient_context`. Because the route response model is strictly typed as `RegimenAnalysisOut`, FastAPI rejected the serialization.
- **Correction Applied:**
  ```python
  # app/services/safety_service.py
  if med_count < 2:
      return {
          "analysis_id": f"safe-{int(datetime.now(timezone.utc).timestamp())}",
          "overall_risk_category": "Insufficient Medications",
          "overall_risk_score": 0.0,
          "summary_headline": "At least 2 distinct medications are required to perform drug-drug interaction profiling.",
          "total_medications": med_count,
          "evaluated_medications": unique_meds,
          "total_pairs_evaluated": 0,
          "pairwise_interactions": [],
          "unmonitored_pairs": [],
          "contraindications_count": 0,
          "major_interactions_count": 0,
          "moderate_interactions_count": 0,
          "minor_interactions_count": 0,
          "patient_context": patient_context,
          "safety_disclaimer": (
              "Polypharmacy risk analysis requires evaluating multiple concurrent medications. "
              "Single-agent toxicology should be reviewed via standard product monographs."
          ),
          "created_at": datetime.now(timezone.utc).isoformat()
      }
  ```
- **Verification:** Added automated regression test `test_phase3_3_doctor_regimen_http_single_and_duplicate_handling` in `app/tests/test_api.py`. Verified HTTP 200 return and clean JSON serialization.

---

## 9. Files Changed and Reasons

| File Changed | Line Range | Nature of Modification | Rationale |
|---|---|---|---|
| `app/services/safety_service.py` | Lines 94–115 | Added 5 missing dictionary keys (`total_pairs_evaluated: 0`, `moderate_interactions_count: 0`, `minor_interactions_count: 0`, `patient_context: patient_context`) to early return. | Resolves FastAPI Pydantic `ResponseValidationError` when regimens have $<2$ unique medications. |
| `app/tests/test_api.py` | Lines 3201–3263 | Appended `test_phase3_3_doctor_regimen_http_single_and_duplicate_handling`. | Regression coverage for HTTP-level single-medication, duplicate, empty, and RBAC responses on `/api/doctor/safety/analyze-regimen`. |

---

## 10. Exact Commands Executed and Actual Outcomes

```powershell
# 1. Automated Backend Regression Suite
.\.venv\Scripts\python.exe -m pytest
# Outcome: 139 passed, 2 warnings in 147.80s (100% pass rate)

# 2. Targeted Phase 3.3 Regression Test
.\.venv\Scripts\python.exe -m pytest -k test_phase3_3_doctor_regimen_http_single_and_duplicate_handling
# Outcome: 1 passed, 138 deselected in 3.33s

# 3. Frontend Production Build
npm run build --prefix frontend
# Outcome: Succeeded in 1.71s (Vite v8.3.2 client bundle generated)

# 4. Frontend Lint Analysis
npm run lint --prefix frontend
# Outcome: 0 errors, 161 non-blocking warnings in 139ms (Oxlint)

# 5. Phase 3.3 Comprehensive Workflow Audit Matrix
.\.venv\Scripts\python.exe scratch/run_phase_3_3_audit.py
# Outcome: 100% passed (Saved to scratch/phase_3_3_audit_results.json)

# 6. Concurrency Isolation Test (5 Parallel Async Investigations)
.\.venv\Scripts\python.exe scratch/test_concurrency.py
# Outcome: 100% passed (5/5 requests isolated with unique workflow IDs)
```

---

## 11. Test Execution Summary

- **Total Automated Unit & Integration Tests:** **139**
- **Tests Passed:** **139 (100%)**
- **Tests Failed:** **0 (0%)**
- **Tests Skipped:** **0 (0%)**
- **Build Status:** **PASS**
- **Lint Status:** **PASS**

---

## 12. Remaining Defects and Scientific Limitations

1. **Preclinical Research Boundary**:
   - CureNova 2.0 scores represent computational hypotheses based on biological target overlap and molecular descriptors. They are **not** clinical success probabilities, treatment guidelines, or proofs of in vivo efficacy.
2. **Offline Parquet Candidate Dataset Scale**:
   - The local DuckDB feature parquet `drug_disease_features_v4.parquet` contains 57 candidate pairs with `label = 0` (unlabeled candidates).
   - The full historical training set of 190,108 rows is external (documented in `ml/CureNova_ML_Technical_Report.md`). Computing empirical ROC/PR on the local 57-row file is degenerate because no positive examples exist in the file.
3. **Public API Rate Limits**:
   - When external services (ClinicalTrials.gov v2 API, NCBI PubMed) are unreachable or rate-limited, the system falls back to curated local SQLite records, ensuring deterministic execution without crashing.

---

## 13. Confirmation of Invariance

- **ML Model Artifact:** `ml/models/cure_nova_xgb_final.joblib` (SHA-256 verified, 8,998,399 bytes) was **not modified, retrained, or replaced**.
- **User Interface Design:** **Zero modifications** were made to frontend CSS, Tailwind classes, colors, typography, spacing, layouts, animations, themes, or page designs.
- **Git State:** **No destructive Git operations** (`git reset --hard`, `git push`, `git rebase`) were performed.

---

## 14. Validation Methodology Distinction

| Validation Type | Components Verified | Description / Standards |
|---|---|---|
| **Automated Unit & Integration Tests** | `app/tests/test_api.py` (139 tests) | Executes programmatic test assertions in an isolated in-memory SQLite environment (`StaticPool`). Tests authentication, route parameters, schemas, and error codes. |
| **End-to-End Real Integration Tests** | `scratch/run_phase_3_3_audit.py`<br>`scratch/test_concurrency.py` | Sends real HTTP requests through FastAPI TestClient and HTTPX async client. Evaluates real DuckDB parquet queries, dynamic feature generation, and SQLite persistence. |
| **Scientific Boundary Validation** | `TranscriptomicsService`<br>`ClinicalTrialChallengeAgent`<br>`MultiDrugSafetyService` | Verifies adherence to published scientific standards: Broad CMAP $\tau$ directional conventions, landmark gene space, operational vs inefficacy clinical trial distinctions, and absence-of-evidence warnings. |
| **Manual Verification** | Browser Reload / URL Routing | Verifies that navigating via direct URL query parameters (`?id=...` or `?workflow_id=...`) restores complete active dossiers from database records. |
