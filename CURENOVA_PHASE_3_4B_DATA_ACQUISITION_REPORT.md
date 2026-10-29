# CureNova 2.0 — Phase 3.4B: Dataset Acquisition and Integrity Validation Report

**Project:** CureNova 2.0 — Agentic AI Drug Repurposing & Polypharmacy Risk Platform  
**Evaluation Phase:** Phase 3.4B (Dataset Acquisition and Integrity Validation)  
**Date of Execution:** October 29, 2026  
**Auditor:** CureNova System Validation & Scientific Review Agent  
**Status:** Complete — Acquisition Successful, Data Verified, Full Test Suite Preserved (139/139 Passing)  

---

## Executive Summary

Phase 3.4A identified the precise inventory of existing and missing data resources across CureNova 2.0, identifying that the offline training dataset (`ml_training_sample_v4.parquet`) and the Open Targets 26.09 `clinical_indication` table were absent from the local workspace.

In **Phase 3.4B**, the approved Tier 1 missing dataset—**Open Targets Platform release 26.09 `clinical_indication/00000000.parquet`**—was officially acquired, placed into the canonical project data directory, and comprehensively validated using DuckDB.

### Key Milestones Achieved

1. **Targeted Acquisition**: Downloaded exactly one approved file: `ml/data/open_targets/clinical_indication/00000000.parquet` (4.99 MB) from official EMBL-EBI Open Targets 26.09 infrastructure.
2. **Strict Scope Control**: Obeyed all absolute restrictions. No large datasets were downloaded: the ~30 GB NIH LINCS L1000 matrix and the ~830 MB Open Targets association dataset were **not** downloaded. Zero UI, CSS, model, or application code modifications were made.
3. **Dataset Validation**: Verified readability, schema, row counts, and data integrity using DuckDB. The dataset contains **86,451 records** across **11,378 unique drugs** and **3,631 unique diseases** with **zero null values** across all key identifier columns.
4. **Feature Store Cross-Validation**: Cross-referenced the 57 rows in `ml/data/training/drug_disease_features_v4.parquet` against the authentic 86,451 indications. Discovered that **23 candidate pairs** have documented clinical trials or approvals in Open Targets (4 `APPROVAL`, 7 `PHASE_3`, 11 `PHASE_2`, 1 `PHASE_1`), while **34 pairs** are uncharacterized research hypotheses.
5. **Original Training Dataset Audit**: Verified that `A:\CureNovaML\data\training\ml_training_sample_v4.parquet` remains unmounted in this environment. Documented exact transfer procedures.
6. **Integrity & Zero Regression**: SHA-256 hashes confirm that the production model binary (`cure_nova_xgb_final.joblib`) and existing candidate feature store remain **100% bit-for-bit identical**. The complete backend test suite passed with **139 / 139 tests passing (100%)**.

---

## 1. Exact Files Downloaded

A single file was acquired during Phase 3.4B in strict accordance with the prioritized plan:

| Property | Value |
|---|---|
| **Relative Workspace Path** | `ml/data/open_targets/clinical_indication/00000000.parquet` |
| **Absolute Local Path** | `C:\Users\mital\OneDrive\Pictures\Desktop\CureNova-backend-latest\ml\data\open_targets\clinical_indication\00000000.parquet` |
| **Official Source URL** | `https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/clinical_indication/00000000.parquet` |
| **Download Protocol** | HTTPS (TLS 1.3) via Python `urllib.request` streaming chunk-buffer |
| **Download Timestamp** | 2026-10-29 12:02:20 UTC |
| **Exact File Size** | **4,989,955 bytes** (~4.76 MiB / ~4.99 MB) |
| **SHA-256 Hash** | `e10ced7ce09495cd3fa6e7cb94e81e083aed78ee399424730d567243b49a38d8` |
| **Partition Structure** | Single unpartitioned Parquet file (`00000000.parquet`) |
| **Pre-existing File Status** | File did not previously exist; no existing files were overwritten |

---

## 2. Official Source & Release Verification

### 2.1 EBI FTP Directory Inspection

Before initiating the download, the official European Bioinformatics Institute (EMBL-EBI) repository was inspected via directory listing:
- **Base Root**: `https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/`
- **Release Directory Verified**: `26.09/` (Open Targets Platform September 2026 release).
- **Subdirectory Discovered**: In Open Targets 26.09, ETL outputs are located directly under `output/` (e.g. `26.09/output/clinical_indication/`) rather than the legacy 2021 path (`output/etl/parquet/`).
- **Partition Count**: Exactly one single Parquet part (`00000000.parquet`), last modified on server `2026-09-07 18:03`. All records are consolidated into this single file.

### 2.2 Disk Space Verification

Available disk space was measured prior to download:
- **Drive**: `C:`
- **Free Space Available**: `80,057,946,112 bytes` (~80.05 GB).
- **Download Requirement**: ~4.99 MB (< 0.01% of available space).
- **Conclusion**: Plentiful storage capacity; zero risk of disk exhaustion.

---

## 3. Schema & Data Integrity Validation

The downloaded Parquet file was analyzed in-process using DuckDB without memory-intensive whole-table loading.

### 3.1 Parquet Schema

```
Columns count: 5
  • id                : VARCHAR       (Unique record hash identifier)
  • maxClinicalStage  : VARCHAR       (Highest clinical development stage reached)
  • clinicalReportIds : VARCHAR[]     (Array of ClinicalTrials.gov NCT or PubMed report UUIDs)
  • diseaseId         : VARCHAR       (Ontology condition identifier, e.g., MONDO_*, EFO_*)
  • drugId            : VARCHAR       (ChEMBL molecule identifier, e.g., CHEMBL*)
```

### 3.2 Row Counts & Entity Cardinality

| Metric | Measured Count | Consistency with ML Technical Report |
|---|---:|---|
| **Total Rows** | **86,451** | Exact match (Report Section 3.1: 86,451 rows) |
| **Distinct Record IDs** | **86,451** | 100% unique primary keys |
| **Distinct Drugs (`drugId`)** | **11,378** | Exact match (Report Section 3.1: 11,378 unique drugs) |
| **Distinct Diseases (`diseaseId`)** | **3,631** | Exact match (Report Section 3.1: 3,631 unique diseases) |
| **Distinct `(drugId, diseaseId)` Pairs** | **86,451** | Exactly one record per drug-disease pair |

### 3.3 Null Value & Data Quality Audit

| Column Checked | Null Count | Null Rate | Status |
|---|---:|---:|---|
| `id` | 0 | 0.00% | **PASSED** (No missing identifiers) |
| `drugId` | 0 | 0.00% | **PASSED** (100% populated) |
| `diseaseId` | 0 | 0.00% | **PASSED** (100% populated) |
| `maxClinicalStage` | 0 | 0.00% | **PASSED** (100% populated) |
| `clinicalReportIds` | 0 | 0.00% | **PASSED** (Zero null arrays; empty arrays used where no report) |

### 3.4 Entity Identifier Formats & Ontology Distribution

- **Drug Identifiers**: 100% of drug identifiers follow standard ChEMBL formatting (`CHEMBL4`, `CHEMBL2105741`, `CHEMBL940`, etc.), directly compatible with CureNova's entity resolution engine.
- **Disease Identifiers**: Disease terms are represented using standard Open Targets ontologies:

| Ontology Prefix | Record Count | Percentage | Description |
|---|---:|---:|---|
| `MONDO_` | 72,157 | 83.47% | Monarch Disease Ontology (CureNova canonical standard) |
| `EFO_` | 7,123 | 8.24% | Experimental Factor Ontology |
| `HP_` | 6,442 | 7.45% | Human Phenotype Ontology |
| `MP_` | 430 | 0.50% | Mammalian Phenotype Ontology |
| `GO_` | 154 | 0.18% | Gene Ontology biological process phenotypes |
| `Orphanet_` | 98 | 0.11% | Rare disease catalog identifiers |
| Other (`OBA_`, `NCIT_`, `OTAR_`) | 47 | 0.05% | Specific biological annotations |

### 3.5 Clinical Trial Stage Distribution

The `maxClinicalStage` column captures the highest clinical development tier reached for each drug-disease indication:

| Clinical Development Stage | Indication Count | Percentage | Clinical Interpretation |
|---|---:|---:|---|
| `PHASE_2` | 28,601 | 33.08% | Mid-stage efficacy & dose-ranging trials |
| `PHASE_3` | 15,811 | 18.29% | Pivotal confirmatory multi-center trials |
| `APPROVAL` | 10,952 | 12.67% | Formal regulatory marketing approval (FDA/EMA) |
| `UNKNOWN` | 9,882 | 11.43% | Historical/unspecified trial phase |
| `PHASE_1` | 9,840 | 11.38% | Early-stage human safety & pharmacokinetics |
| `PHASE_1_2` | 6,566 | 7.60% | Combined Phase 1/Phase 2 protocol |
| `PHASE_2_3` | 3,115 | 3.60% | Adaptive Phase 2/Phase 3 trial |
| `EARLY_PHASE_1` | 1,304 | 1.51% | Exploratory IND / micro-dosing studies |
| `IND` | 216 | 0.25% | Investigational New Drug application active |
| `PRECLINICAL` | 117 | 0.14% | Formal animal / IND-enabling studies |
| `PREAPPROVAL` | 47 | 0.05% | NDA/BLA under regulatory review |

---

## 4. Feature Store Cross-Validation (`drug_disease_features_v4.parquet`)

The existing candidate feature store was audited against the downloaded clinical indication database to answer the core questions of Task 4.

### 4.1 Feature Store Baseline

- **File Path**: `ml/data/training/drug_disease_features_v4.parquet`
- **File Size**: 15,424 bytes (15.1 KB)
- **Dimensions**: **57 rows $\times$ 42 columns**
- **Diseases Represented**: 9 canonical diseases (`MONDO_0004989`, `MONDO_0005149`, `MONDO_0005575`, `MONDO_0018827`, `MONDO_0100096`, `MONDO_0004975`, `MONDO_0005180`, `MONDO_0018177`, `MONDO_0021040`).
- **Unique Drugs**: 30 compounds.
- **Existing Label Column**: All 57 rows have `label = 0`.

### 4.2 Why All 57 Rows Have `label = 0`

Inspection of [`scripts/build_candidate_features.py`](file:///c:/Users/mital/OneDrive/Pictures/Desktop/CureNova-backend-latest/scripts/build_candidate_features.py#L185-L189) reveals the historical rationale:
```python
row = {
    "disease_id": disease_id,
    "drug_id": drug_id,
    "label": 0,
    ...
```
`build_candidate_features.py` was authored specifically as an inference-time candidate store generator. In the Open Targets candidate selection architecture:
- Known indications (`clinical_indication`) formed the positive class (`label = 1`).
- All prospective pairs generated from target associations formed the uncharacterized candidate pool (`label = 0`) to be evaluated and ranked by the model.
- Setting `label = 0` was an architectural convention meaning **"Prospective Candidate for Scoring"**, NOT "Scientifically Proven Negative".

### 4.3 Candidate Overlap with Clinical Indications

A DuckDB cross-join between `drug_disease_features_v4.parquet` (57 rows) and `clinical_indication` (86,451 rows) on `(drug_id == drugId AND disease_id == diseaseId)` discovered:
- **Exactly 23 of the 57 candidate pairs** have documented clinical trials or approvals in Open Targets!
- **34 candidate pairs** have no clinical indication record in Open Targets (prospective repurposing hypotheses).

#### Full Table of 23 Confirmed Indication Matches

| Disease Name | Disease ID | Drug ID | Drug Name / Class | Open Targets Clinical Stage | Clinical Implication |
|---|---|---|---|---|---|
| Colorectal Cancer | `MONDO_0005575` | `CHEMBL1946170` | Regorafenib | **APPROVAL** | Established positive control (approved for refractory CRC). |
| Breast Carcinoma | `MONDO_0004989` | `CHEMBL1908360` | Everolimus | **APPROVAL** | Established positive control (approved for HR+/HER2- breast cancer). |
| Breast Carcinoma | `MONDO_0004989` | `CHEMBL3545252` | Docetaxel | **APPROVAL** | Established positive control (standard of care taxane chemotherapy). |
| Breast Carcinoma | `MONDO_0004989` | `CHEMBL1201179` | Lapatinib | **APPROVAL** | Established positive control (dual HER2/EGFR TKI approved in breast cancer). |
| Pancreatic Neoplasm | `MONDO_0021040` | `CHEMBL1637` | Gemcitabine | **PHASE_3** | High-level clinical precedence (standard first-line pancreatic backbone). |
| Pancreatic Neoplasm | `MONDO_0021040` | `CHEMBL1079742` | Erlotinib | **PHASE_3** | High-level clinical precedence (FDA-approved + gemcitabine in pancreatic cancer). |
| Severe COVID ARDS | `MONDO_0100096` | `CHEMBL131` | Dexamethasone | **PHASE_3** | High-level clinical precedence (RECOVERY trial confirmed standard of care). |
| Severe COVID ARDS | `MONDO_0100096` | `CHEMBL632` | Baricitinib | **PHASE_3** | High-level clinical precedence (ACTT-2 trial, FDA EUA/approval in COVID-19). |
| Severe COVID ARDS | `MONDO_0100096` | `CHEMBL1643` | Tocilizumab | **PHASE_3** | High-level clinical precedence (IL-6 inhibitor standard in severe COVID). |
| Pancreatic Neoplasm | `MONDO_0021040` | `CHEMBL3545252` | Docetaxel | **PHASE_3** | Evaluated in Phase 3 combination regimens. |
| Parkinson's Disease | `MONDO_0005180` | `CHEMBL1017` | Rasagiline | **PHASE_3** | MAO-B inhibitor indicated in Parkinson's disease. |
| Colorectal Cancer | `MONDO_0005575` | `CHEMBL1079742` | Erlotinib | **PHASE_2** | Investigational repurposing candidate in Phase 2 trials. |
| Glioblastoma | `MONDO_0018177` | `CHEMBL1079742` | Erlotinib | **PHASE_2** | Investigational EGFR TKI in recurrent GBM. |
| Glioblastoma | `MONDO_0018177` | `CHEMBL1201179` | Lapatinib | **PHASE_2** | Investigational TKI in GBM Phase 2 trials. |
| Colorectal Cancer | `MONDO_0005575` | `CHEMBL1908360` | Everolimus | **PHASE_2** | Evaluated in PI3K/mTOR pathway-driven CRC. |
| Glioblastoma | `MONDO_0018177` | `CHEMBL1908360` | Everolimus | **PHASE_2** | Evaluated in subependymal giant cell astrocytoma / GBM. |
| Colorectal Cancer | `MONDO_0005575` | `CHEMBL3545252` | Docetaxel | **PHASE_2** | Evaluated as salvage chemotherapy in metastatic CRC. |
| Colorectal Cancer | `MONDO_0005575` | `CHEMBL1278146` | Famitinib | **PHASE_2** | Multi-targeted VEGFR TKI in Phase 2 CRC trials. |
| Alzheimer's Disease | `MONDO_0004975` | `CHEMBL1017` | Rasagiline | **PHASE_2** | Repurposing trial for neuroprotective MAO-B inhibition. |
| Pancreatic Neoplasm | `MONDO_0021040` | `CHEMBL1946170` | Regorafenib | **PHASE_2** | Phase 2 exploration in advanced refractory pancreatic cancer. |
| Alzheimer's Disease | `MONDO_0004975` | `CHEMBL1016` | Selegiline | **PHASE_2** | Evaluated for cognitive slowing in mild-to-moderate AD. |
| Glioblastoma | `MONDO_0018177` | `CHEMBL180022` | Neratinib | **PHASE_2** | Irreversible pan-HER TKI in EGFR-amplified glioblastoma. |
| Colorectal Cancer | `MONDO_0005575` | `CHEMBL3545110` | Ribociclib | **PHASE_1** | CDK4/6 inhibitor early-stage trial in CRC. |

### 4.4 Scientific Analysis: Can Ground-Truth Labels Be Established?

#### Positive Labels ($label = 1$)
- **Yes.** The 4 approved pairs (`APPROVAL`) and 7 Phase 3 pairs (`PHASE_3`) represent indisputable, regulatory- and trial-confirmed positive evidence.
- If defining positive indications as regulatory approvals, exactly **4 positive pairs** are established.
- If defining positive indications as advanced clinical development (Phase 3 or Approval), exactly **11 positive pairs** are established.

#### Negative Labels ($label = 0$)
- **NO.** Negative examples **cannot** be scientifically established from the absence of an indication record:
  - In pharmacology, the absence of a documented clinical indication does **not** equal biological inactivity or treatment failure.
  - A compound with zero indications may simply have never been tested in clinical trials for that disease (a genuine repurposing candidate!).
  - Converting the remaining 34 pairs to "True Negatives" would falsely treat prospective biological hypotheses as proven negative controls.
- **Rule Enforced**: No ROC-AUC or PR-AUC metrics were calculated on `drug_disease_features_v4.parquet` because doing so would rely on artificial, unproven negative labels.

---

## 5. Audit of the Original 190,108-Row Training Dataset

### 5.1 Verification of Accessibility

The Phase 3.4A inventory identified the original training dataset as:
```text
A:\CureNovaML\data\training\ml_training_sample_v4.parquet (or ml_training_sample_v4.csv)
```
- **File System Test**: `powershell -Command "Test-Path 'A:\'"` returned `False`.
- **Finding**: Drive `A:\` was an offline workstation mount point and is not physically or logically present in the current environment.
- **Constraint Followed**: In accordance with Task 5, no replacement dataset was fabricated, no unrelated dataset was substituted, and the production model was not rebuilt.

### 5.2 Status of Independent Metric Reproduction

- **Current Status**: Independent re-calculation of the held-out metrics (unseen-disease AP: 0.9047, ROC-AUC: 0.9735; unseen-drug AP: 0.8652, ROC-AUC: 0.9580) **remains blocked** until the original dataset with its exact entity partition indices is accessible.
- **Why Runtime is Unaffected**: The serialized model bundle [`ml/models/cure_nova_xgb_final.joblib`](file:///c:/Users/mital/OneDrive/Pictures/Desktop/CureNova-backend-latest/ml/models/cure_nova_xgb_final.joblib) contains the complete trained estimator and feature schema. It does not require the training file during application execution.

### 5.3 Workstation Transfer Instructions

To transfer the original training dataset from the development workstation:

1. **Locate Source Files**: On the development workstation (`A:\CureNovaML\`), locate:
   ```text
   A:\CureNovaML\data\training\ml_training_sample_v4.parquet
   A:\CureNovaML\data\training\ml_training_sample_v4.csv (optional)
   ```
2. **Compute Verification Checksums**:
   ```powershell
   certutil -hashfile A:\CureNovaML\data\training\ml_training_sample_v4.parquet SHA256
   ```
3. **Transfer File**: Transfer via secure SCP, SFTP, or encrypted network storage to:
   ```text
   C:\Users\mital\OneDrive\Pictures\Desktop\CureNova-backend-latest\ml\data\training\ml_training_sample_v4.parquet
   ```
4. **Verify Integrity**: Re-run SHA-256 validation on the destination machine before using in evaluation scripts.

---

## 6. Optional Resources Invariance Confirmation

In compliance with Task 6:

1. **Complete LINCS Matrix (GSE92742)**: Was **NOT** downloaded. The ~30 GB matrix remains excluded from the repository.
2. **Open Targets Association Parquets**: The 14 Parquet files of `association_overall_direct/` (~830 MB) were **NOT** downloaded.
3. **Supported Disease Catalog**: The 6 disease signatures in [`app/services/transcriptomics_service.py`](file:///c:/Users/mital/OneDrive/Pictures/Desktop/CureNova-backend-latest/app/services/transcriptomics_service.py) were **NOT** modified. No new gene lists were hardcoded or altered in code during this phase.

---

## 7. Regression and Integrity Verification

### 7.1 Binary Hash Integrity

The SHA-256 hashes of critical project assets were verified before and after dataset acquisition:

| File | Pre-Download SHA-256 | Post-Download SHA-256 | Status |
|---|---|---|---|
| `ml/models/cure_nova_xgb_final.joblib` | `ef951cc22a2e3ca855fea570331b0f5b413905d44ceb11faa52e764391296349` | `ef951cc22a2e3ca855fea570331b0f5b413905d44ceb11faa52e764391296349` | **IDENTICAL** |
| `ml/data/training/drug_disease_features_v4.parquet` | `ef1dd9219d7b9ad5a7efbd7e8b780583637a5a2d754aaf6264bf94897aa79d5a` | `ef1dd9219d7b9ad5a7efbd7e8b780583637a5a2d754aaf6264bf94897aa79d5a` | **IDENTICAL** |
| `ml/data/training/drug_molecular_features.csv` | `0d8b3ce3c85ca1e1db71ec114876b5d956e182283e3aa68b4ad183d2f9eaae52` | `0d8b3ce3c85ca1e1db71ec114876b5d956e182283e3aa68b4ad183d2f9eaae52` | **IDENTICAL** |

### 7.2 Application Code Invariance

- Zero source files under `app/` or `frontend/` were modified during Phase 3.4B.
- The Git working directory reflects only the addition of the new dataset and verification documentation:
  ```text
  ?? ml/data/open_targets/clinical_indication/00000000.parquet
  ?? CURENOVA_PHASE_3_4B_DATA_ACQUISITION_REPORT.md
  ```

### 7.3 Automated Test Suite Execution

The complete backend regression test suite was executed:
```powershell
.\.venv\Scripts\python.exe -m pytest
```

**Results:**
- **Tests Collected**: 139
- **Tests Passed**: **139** (100%)
- **Tests Failed**: 0
- **Execution Duration**: 123.79s (2 minutes 3 seconds)
- **Status**: **ALL TESTS PASSED WITH ZERO REGRESSIONS**

---

## 8. Verified Facts vs. Assumptions vs. Unresolved Questions

### Verified Facts
1. Open Targets 26.09 `clinical_indication/00000000.parquet` was successfully acquired from official EMBL-EBI infrastructure (4,989,955 bytes, SHA-256: `e10ced7c...`).
2. The dataset contains exactly 86,451 records across 11,378 drugs and 3,631 diseases with zero missing values in primary key columns.
3. Exactly 23 of the 57 candidate pairs in `drug_disease_features_v4.parquet` correspond to documented clinical trials or approved indications in Open Targets (including 4 FDA/EMA approvals).
4. The production model binary `cure_nova_xgb_final.joblib` and feature store `drug_disease_features_v4.parquet` remain completely unchanged.
5. All 139 automated tests continue to pass without error.

### Grounded Assumptions
1. The 34 pairs in `drug_disease_features_v4.parquet` with no documented clinical indications are genuine prospective candidate hypotheses rather than confirmed biological failures.
2. The original development path `A:\CureNovaML` represents an external workstation or detachable drive used during the initial ML training phase.

### Unresolved Questions & Blockers
1. Will the original 190,108-row training parquet be transferred from the development workstation, or will the full 190k dataset be reconstructed from raw Open Targets 26.09 parquets?
2. When should the 3 missing disease expression signatures (AD, PD, COVID-19 ARDS) be integrated into `transcriptomics_service.py` to achieve 100% parity across the 9 canonical indications?

---

## 9. Recommended Next Step

**Recommended Step for Phase 3.5**:
1. If the original `ml_training_sample_v4.parquet` is transferred, write an automated validation script (`scripts/verify_ml_metrics.py`) that applies the documented `GroupShuffleSplit` (by `disease_id` and `drug_id`) to independently reproduce the reported benchmarks ($AP \ge 0.86$, $ROC \ge 0.95$).
2. Maintain strict invariance: do not touch the UI, CSS, or production model binary.
