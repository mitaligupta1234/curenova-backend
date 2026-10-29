# CureNova 2.0 — Researcher Module Database and Data Pipeline Completion Report

**Audit & Completion Date:** October 29, 2026  
**Auditor / Engineer:** Antigravity AI  
**Repository:** `CureNova-backend-latest` (`c:\Users\mital\OneDrive\Pictures\Desktop\CureNova-backend-latest`)  
**Active Model:** `ml/models/cure_nova_xgb_final.joblib` (8,998,399 bytes, **unmodified & frozen**)  
**Test Results:** **147 / 147 passed** (0 failures, in 139.90s)  
**Frontend Build:** **Production build succeeded** in 2.04s (`dist/`, 0 errors)  
**Frontend Lint:** **0 errors** (161 warnings across 50 files)  
**Status:** **COMPLETE — FULLY VERIFIED & OPERATIONAL**  

---

## 1. Executive Summary

The Researcher Module of CureNova 2.0 has been completed and brought to full relational database persistence, end-to-end data integrity, and role-based security isolation without requiring a platform rebuild or disturbing existing models and UI designs.

Prior to this completion, the `AgenticOrchestrator` generated candidate hypotheses and validated citations in-memory, serializing the final JSON blob into `investigation_runs.results_json`. Individual candidate hypotheses and literature evidence records were never instantiated or linked in relational database tables, `InvestigationRun` lacked execution status, duration, search type, and error tracking, and researcher endpoints lacked proper tenant isolation.

### Key Achievements
1. **Database Schema Non-Destructive Extension**: Extended `investigation_runs` and `candidate_predictions` with relational keys, provenance metadata, execution metrics, and molecular descriptors.
2. **Atomic Relational Persistence**: Every investigation run now atomically persists:
   - The master `InvestigationRun` record (`workflow_id`, `user_id`, `search_type`, `status`, `execution_duration_ms`, `model_version`, `error_message`).
   - Distinct `CandidatePrediction` records linked via `investigation_id` and `workflow_id`, storing prediction ranking scores, provenance source, and serialized molecular descriptors.
   - Distinct `EvidenceRecord` citations linked directly to candidates via `candidate_id`.
3. **Robust Partial Failure Tracking**: Unhandled pipeline failures are trapped and recorded with `status="failed"`, `error_message`, and `candidate_count=0` rather than vanishing without a trace.
4. **Researcher Authorization & Privacy**: Enforced role-based access control. Researchers can only inspect and download dossiers for their own private investigations (`403 Forbidden` on unauthorized cross-researcher access), while system administrators retain universal access.
5. **Full Backward & Frontend Compatibility**: Schema responses (`EvidenceRecordOut`, `CandidateSummaryOut`, `AgentWorkflowResponse`) were enhanced with computed compatibility aliases (`summary`, `findings`, `url`, `source`, `evidence_level`, `curenova_ranking`, `display_title`, etc.), ensuring zero UI regressions or undefined card states in `EvidenceExplorer` or `ResearcherDrugRepurposing`.

---

## 2. Database Audit & Schema Inventory

### 2.1 Connection Configuration
- **Database Engine**: SQLite 3 (`sqlite:///./curenova.db`)
- **Engine Setup**: `create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})`
- **Session Management**: SQLAlchemy `sessionmaker(autocommit=False, autoflush=False)` with scoped session dependency injection (`get_db`).

### 2.2 Existing Tables and Row Count Audit
At the start of this phase, an exhaustive audit of `curenova.db` was conducted via `audit_db_tables.py`:

| Table Name | Initial Rows | Key Purpose & Existing Columns |
| :--- | :---: | :--- |
| `users` | 6 | Platform accounts (`researcher`, `doctor`, `patient`, `admin`) with Argon2id credentials. |
| `refresh_tokens` | 59 | Cryptographically hashed refresh tokens with family reuse detection. |
| `research_projects` | 3 | Umbrella disease-focus research containers. |
| `drugs` | 8 | Preclinical benchmark compounds (ChEMBL IDs, indications, targets). |
| `diseases` | 5 | Disease pathology profiles with MeSH and MONDO mappings. |
| `targets` | 0 | Target gene and UniProt ontology nodes. |
| `candidate_predictions` | 7 | Precomputed seed candidate predictions. |
| `evidence_records` | 9 | Literature evidence facts linked to candidate predictions. |
| `research_notes` | 1 | Verified research notes linked to candidate predictions. |
| `research_feedback` | 0 | Human-in-the-loop qualitative feedback records. |
| `investigation_runs` | 95 | Master investigation workflow traces. |
| `knowledge_nodes` | 26 | Biological entity nodes for the Biomedical Knowledge Graph. |
| `knowledge_edges` | 23 | Directed biological edges (inhibits, treats, activates). |
| `stress_test_runs` | 3 | Stress-test robustness evaluation runs. |
| `drug_interactions` | 5 | Clinical drug-drug interactions with severity classification. |
| `clinical_trials` | 4 | Real and challenge clinical trials from ClinicalTrials.gov. |
| `patient_medicine_guides` | 4 | Patient-friendly plain language guides. |
| `patient_medications` | 1 | Patient active daily medication regimens. |

---

## 3. Schema Enhancements & Relational Model Updates

To fulfill research persistence requirements without data loss, non-destructive schema additions were applied to SQLite and mapped in SQLAlchemy models:

### 3.1 `investigation_runs` Table
```sql
ALTER TABLE investigation_runs ADD COLUMN search_type VARCHAR(50) DEFAULT 'drug_to_disease';
ALTER TABLE investigation_runs ADD COLUMN status VARCHAR(50) DEFAULT 'completed';
ALTER TABLE investigation_runs ADD COLUMN execution_duration_ms INTEGER;
ALTER TABLE investigation_runs ADD COLUMN model_version VARCHAR(50) DEFAULT 'cure-nova-xgb-final';
ALTER TABLE investigation_runs ADD COLUMN error_message TEXT;

CREATE INDEX IF NOT EXISTS ix_investigation_runs_status ON investigation_runs(status);
CREATE INDEX IF NOT EXISTS ix_investigation_runs_user_id ON investigation_runs(user_id);
```

### 3.2 `candidate_predictions` Table
```sql
ALTER TABLE candidate_predictions ADD COLUMN investigation_id INTEGER REFERENCES investigation_runs(id);
ALTER TABLE candidate_predictions ADD COLUMN workflow_id VARCHAR(100);
ALTER TABLE candidate_predictions ADD COLUMN score_type VARCHAR(50) DEFAULT 'ranking_score';
ALTER TABLE candidate_predictions ADD COLUMN provenance VARCHAR(100) DEFAULT 'precomputed_feature_store';
ALTER TABLE candidate_predictions ADD COLUMN molecular_features_json TEXT;

CREATE INDEX IF NOT EXISTS ix_candidate_predictions_investigation_id ON candidate_predictions(investigation_id);
CREATE INDEX IF NOT EXISTS ix_candidate_predictions_workflow_id ON candidate_predictions(workflow_id);
CREATE INDEX IF NOT EXISTS ix_candidate_predictions_inv_rank ON candidate_predictions(investigation_id, rank);
```

### 3.3 Relational Model Mapping (`app/models/models.py`)
- **`InvestigationRun`**:
  - `candidates = relationship("CandidatePrediction", back_populates="investigation", cascade="all, delete-orphan")`
- **`CandidatePrediction`**:
  - `investigation = relationship("InvestigationRun", back_populates="candidates")`
  - `evidence_records = relationship("EvidenceRecord", back_populates="candidate", cascade="all, delete-orphan")`
  - `notes = relationship("ResearchNote", back_populates="candidate", cascade="all, delete-orphan")`

---

## 4. Files Changed and Technical Rationale

| File Path | Changes Made | Technical Rationale |
| :--- | :--- | :--- |
| `app/models/models.py` | Added relational foreign keys and persistence columns to `InvestigationRun` and `CandidatePrediction`. Added bidirectional relationships. | Enables relational SQL queries, cascading lifecycle management, and transparent provenance tracking for investigations and candidates. |
| `app/schemas/schemas.py` | 1. Added `model_validator` to `EvidenceRecordOut` to populate `summary`, `findings`, `url`, `source`, `evidence_level`.<br>2. Added `model_validator` to `CandidateSummaryOut` for `curenova_ranking`, `display_title`, etc.<br>3. Defined `InvestigationRunOut`.<br>4. Added `status`, `execution_duration_ms`, `error_message` to `AgentWorkflowResponse`. | Eliminates response-shape mismatches between backend outputs and frontend expectations (`EvidenceExplorer.jsx` and `ResearcherDrugRepurposing.jsx`) without modifying UI components. |
| `app/services/agentic_orchestrator.py` | 1. Integrated `get_molecular_dict()` from `ml.feature_generator` to pull molecular descriptors for candidates.<br>2. Wrapped investigation execution in atomic DB transaction.<br>3. Persisted `InvestigationRun`, all `CandidatePrediction` records, and validated citations as `EvidenceRecord` rows.<br>4. Added failure trap saving `status="failed"` records upon unhandled exceptions. | Guarantees that every completed or failed run is permanently recorded in SQLite with relational links, molecular features, and citations. |
| `app/routers/candidates.py` | 1. Added `investigation_id` and `workflow_id` query filters to `GET /candidates`.<br>2. Updated `GET /candidates/investigations` to scope private runs to `current_user.id` for researchers.<br>3. Updated `GET /candidates/investigation/{workflow_id}` to reject cross-researcher access with `HTTP 403 Forbidden`.<br>4. Included execution duration, search type, status, and error message in run listings. | Enforces strict data isolation between researchers while permitting administrative oversight, and allows direct querying of candidates by investigation. |
| `app/routers/reports.py` | Added `GET /reports/investigation/{workflow_id}/markdown` endpoint generating a complete research dossier for an entire investigation run with authorization enforcement. | Provides researchers and doctors with full, exportable dossiers covering ranked candidates, molecular descriptors, LINCS L1000 connectivity, and ClinicalTrials.gov audits. |
| `frontend/src/services/api.js` | Extracted `formatInvestigationResponse` helper applied consistently to both `analyze` and `getInvestigation`. Added `downloadInvestigationReport` and `downloadCandidateReport`. | Ensures identical normalized candidate structures whether loaded via live analysis, deep link, or browser refresh. |
| `app/tests/test_api.py` | Added 8 comprehensive regression tests (`test_researcher_*`) verifying schema columns, atomic persistence, history retrieval, candidate filtering by investigation ID, cross-researcher authorization, markdown dossier download, and Evidence Explorer compatibility. | Provides continuous verification that all researcher persistence and security requirements pass without breaking existing tests. |

---

## 5. Verification & Test Execution Results

### 5.1 Backend Test Execution Evidence
The complete backend automated test suite was executed using pytest within the isolated test environment:

```
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\mital\OneDrive\Pictures\Desktop\CureNova-backend-latest
collected 147 items

app\tests\test_api.py ........................................................................ [ 48%]
.............................................................................................. [ 97%]
...                                                                                            [100%]

============================== 147 passed, 2 warnings in 139.90s (0:02:19) ==============================
```

#### Detailed Test Case Counts
- **Total Test Cases**: 147
- **Passed**: 147 (100%)
- **Failed**: 0 (0%)
- **Skipped / Deselected**: 0
- **Duration**: 139.90 seconds
- **Database Safeguard**: Passed (`guard_dev_database_session` verified development database `curenova.db` was never mutated or deleted by test runners).

### 5.2 Specific Researcher Persistence Tests
The 8 dedicated researcher module test cases executed cleanly:
1. `test_researcher_schema_columns_and_relationships` — **PASSED**
2. `test_researcher_investigation_atomic_persistence` — **PASSED**
3. `test_researcher_history_retrieval_and_filtering` — **PASSED**
4. `test_researcher_candidate_filtering_by_investigation_id` — **PASSED**
5. `test_researcher_authorization_cross_isolation` — **PASSED**
6. `test_researcher_markdown_dossier_download_and_auth` — **PASSED**
7. `test_researcher_evidence_explorer_compatibility_fields` — **PASSED**
8. `test_researcher_candidate_bookmark_and_notes` — **PASSED**

### 5.3 Frontend Build & Lint Evidence
- **Build Command**: `npm run build` in `frontend/`
  - Output: `vite v8.3.2 building client environment for production... built in 2.04s.`
  - Result: **SUCCESS (Exit Code: 0)**
- **Lint Command**: `npm run lint` in `frontend/`
  - Output: `Found 161 warnings and 0 errors. Finished in 173ms on 50 files.`
  - Result: **SUCCESS (Exit Code: 0)**

---

## 6. Migration, Backup, and Rollback Considerations

1. **Non-Destructive Alterations**:
   - All schema updates used `ALTER TABLE ... ADD COLUMN` with safe default values (`DEFAULT 'completed'`, `DEFAULT 'drug_to_disease'`).
   - No tables were dropped, renamed, or recreated.
   - All 95 existing investigation runs and 7 seed candidate predictions remain intact and functional.
2. **Database Immutability During Testing**:
   - Tests execute against an isolated in-memory SQLite database (`StaticPool`), preventing test fixtures from polluting `curenova.db`.
3. **Backup Strategy**:
   - Prior to applying alterations, `curenova.db` is backed up simply by standard file copy (`copy curenova.db curenova.db.bak`).
4. **Rollback Strategy**:
   - Because all newly added columns are nullable or possess defaults, legacy code paths that do not reference the new columns can execute on the database without errors.

---

## 7. Requirement Status Matrix

| ID | Requirement Area | Status | Verification Evidence |
| :---: | :--- | :---: | :--- |
| **1** | **Database Audit** | **PASS** | Audited all 18 tables, relationships, and connection configurations. Cataloged existing schema and identified missing columns in `investigation_runs` and `candidate_predictions`. Zero data deleted. |
| **2** | **Research Persistence** | **PASS** | Every investigation atomically persists: `workflow_id`, `user_id`, input `query`, `search_type`, `status`, `execution_duration_ms`, `model_version`, candidate predictions with `prediction_score`, `molecular_features_json`, ranking criteria, and linked `EvidenceRecord` citations. |
| **3** | **Data Integrity** | **PASS** | Primary keys, foreign keys (`investigation_id -> investigation_runs.id`, `candidate_id -> candidate_predictions.id`), and indices established. Writes wrapped in atomic transactions (`db.flush()` / `db.commit()` / `db.rollback()`). |
| **4** | **API & Frontend Integration** | **PASS** | Endpoints `/candidates`, `/candidates/investigate`, `/candidates/investigations`, `/candidates/investigation/{workflow_id}`, `/evidence`, `/reports` read and write persistent DB records. Responses normalized via `formatInvestigationResponse`. UI design, CSS, colors, and layout preserved intact. |
| **5** | **ML & Evidence Integration** | **PASS** | Live XGBoost model (`cure_nova_xgb_final.joblib`, 39 features) inference outputs stored separately from transcriptomic $\tau$ and clinical trial challenge audits. No mock scores labeled as live predictions. Molecular features serialized. |
| **6** | **Security & Privacy** | **PASS** | `require_researcher` enforced. Cross-researcher isolation verified (`test_researcher_authorization_cross_isolation` returns `403 Forbidden` when Researcher B attempts to access Researcher A's investigation). |
| **7** | **Testing** | **PASS** | All 147 backend tests passed in 139.90s. Frontend production build succeeded in 2.04s. Frontend lint reported 0 errors. |
| **8** | **Final Report** | **PASS** | Comprehensive documentation provided in `CURENOVA_RESEARCHER_MODULE_COMPLETION.md`. |

---

## 8. Unresolved Blockers

**None.** The Researcher Module database and data pipeline are fully complete, verified, and operational.
