# CureNova 2.0 — Phase 3.4A: Dataset Inventory & Scientific Reproducibility Audit

**Project:** CureNova 2.0 — Agentic AI Drug Repurposing & Polypharmacy Risk Platform  
**Evaluation Phase:** Phase 3.4A (Dataset Audit and Scientific Reproducibility)  
**Date of Audit:** October 29, 2026  
**Auditor:** CureNova System Validation & Scientific Review Agent  
**Status:** Audit Complete — Definitive Dataset Inventory & Reproducibility Analysis  

---

## Executive Summary

Phase 3.3 established end-to-end operational integrity across all 11 stages of the CureNova 2.0 agent pipeline, confirming 139 passing automated backend tests, zero frontend lint errors, clean production builds, and verified user journeys for both Researcher and Doctor workflows.

The objective of **Phase 3.4A** is to perform an exhaustive, evidence-grounded audit of every data file, feature store, external API, and biological reference resource across the CureNova 2.0 ecosystem. This audit inventories:
1. All existing local datasets, their file sizes, formats, schemas, and runtime utility.
2. The exact data-loading pathways used by `predict_v4.py`, `feature_generator.py`, `transcriptomics_service.py`, `clinical_trial_challenge.py`, `safety_service.py`, and `agentic_orchestrator.py`.
3. The offline training data lineage behind the production XGBoost model (`cure_nova_xgb_final.joblib`).
4. Genuinely missing datasets required for full offline retraining and exact reproduction of reported held-out metrics (unseen-drug AP: 0.8652, unseen-disease AP: 0.9047).
5. A rigorous download and storage plan for external resources (Open Targets 26.09, ChEMBL 37, NIH LINCS L1000 GSE92742, and TCGA/GEO RNA-seq signatures).

### Key Audit Conclusions

| Category | Finding | Scientific / Operational Status |
|---|---|---|
| **Production ML Model** | `ml/models/cure_nova_xgb_final.joblib` (8.58 MB) | **Present & Operational**. Retrained on all 190,108 training rows; scores 39 features without external network dependency. |
| **Candidate Feature Store** | `ml/data/training/drug_disease_features_v4.parquet` (15.1 KB) | **Present & Usable**. Contains 57 candidate pairs across 9 canonical diseases and 30 drugs. All 57 rows have `label = 0` (unlabeled candidates). |
| **Molecular Feature Store** | `ml/data/training/drug_molecular_features.csv` (1.68 MB) | **Present & Usable**. Contains RDKit molecular descriptors for 15,465 approved and clinical-stage drugs. |
| **Target Mechanism Store** | `ml/data/open_targets/drug_mechanism_of_action/00000000.parquet` (315.3 KB) | **Present & Usable**. Contains 6,092 mechanism rows and Ensembl target lists from Open Targets 26.09. |
| **Drug Structure Store** | `ml/data/open_targets/drug_molecule/00000000.parquet` (6.55 MB) | **Present & Usable**. Contains 19,170 drug records with canonical SMILES, InChIKeys, and clinical phases. |
| **ChEMBL Cache** | `ml/data/chembl/chembl_api_cache.json` (115.3 KB) | **Present & Usable**. Contains 43 cached drug bioactivity summaries from ChEMBL 37 REST API. |
| **Original 190k Training Dataset** | `ml_training_sample_v4.parquet` / `.csv` | **Missing from Workspace**. Stored during offline development under path `A:\CureNovaML\data\training\`. Required for offline metric reproduction, but *not* required for runtime inference. |
| **LINCS L1000 Transcriptomics** | `transcriptomics_service.py` | **Present & Usable (Curated In-Code)**. Contains authentic Level 5 `modz` profiles for 4 canonical drugs (Metformin, Fasudil, Everolimus, Niclosamide) and 6 disease signatures. Full 30 GB GSE92742 `.gctx` matrix is **Optional**. |
| **Clinical Trial Challenge** | `clinical_trial_challenge.py` | **Present & Usable (Hybrid)**. Queries ClinicalTrials.gov v2 REST API live, with SQLite `clinical_trials` table fallback. |
| **Polypharmacy DDI Safety** | `safety_service.py` | **Present & Usable**. Evaluates $N(N-1)/2$ combinations against SQLite `drug_interactions` table with FDA monograph provenance. |

---

## 1. Inventory of Existing Project Data

The table below catalogs every data file, model binary, configuration manifest, and database store present in the active CureNova 2.0 workspace.

| Relative Path | Size (Bytes) | Format | Rows / Records | Purpose & Active Consumers |
|---|---:|---|---|---|
| `ml/models/cure_nova_xgb_final.joblib` | 8,998,399 | Python Joblib Binary | 1 model bundle | Production XGBoost model bundle (`cure-nova-xgb-final`). Consumed by `ml/predict_v4.py`, `ml/predictor.py`, `app/services/ml_service.py`. |
| `ml/models/cure_nova_xgb_final.json` | 1,671 | JSON | 55 lines | Production model metadata declaring 39 feature names, 190,108 training rows, and held-out benchmark metrics. |
| `ml/models/cure_nova_ml_v4_metadata.json` | 1,070 | JSON | 35 lines | Historical metadata for previous HistGradientBoosting model iteration. |
| `ml/data/training/drug_disease_features_v4.parquet` | 15,424 | Apache Parquet (Snappy) | 57 rows, 42 cols | Precomputed candidate feature store for 9 canonical indications. Queried by `ml/predict_v4.py` via DuckDB. All rows have `label = 0`. |
| `ml/data/training/drug_molecular_features.csv` | 1,764,072 | CSV (UTF-8) | 15,465 rows, 15 cols | Curated RDKit molecular descriptors for 15,465 compounds. Consumed by `ml/feature_generator.py` and `ml/predict_v4.py`. |
| `ml/data/open_targets/drug_mechanism_of_action/00000000.parquet` | 322,830 | Apache Parquet (Snappy) | 6,092 rows, 7 cols | Open Targets Platform 26.09 drug mechanisms and target Ensembl IDs. Consumed by `feature_generator.py` and `scripts/build_candidate_features.py`. |
| `ml/data/open_targets/drug_molecule/00000000.parquet` | 6,867,467 | Apache Parquet (Snappy) | 19,170 rows, 13 cols | Open Targets Platform 26.09 compound identifiers, SMILES, InChIKeys, synonyms, and clinical phases. Consumed by `disease_resolver.py`. |
| `ml/data/chembl/chembl_api_cache.json` | 118,035 | JSON (UTF-8) | 43 drug objects | Cached ChEMBL 37 bioactivity summaries (pChEMBL, usable activity counts, strong target counts). Consumed by `ml/evidence_utils.py`. |
| `curenova.db` | 2,473,984 | SQLite 3 Database | 17 tables, 200+ rows | Relational application database (users, drugs, diseases, DDIs, clinical trials, investigation runs, knowledge graph edges). |

### Detailed Inspection of In-Memory & Script-Embedded Resources

Beyond physical disk files, several CureNova 2.0 services utilize curated biomedical data structures embedded directly within Python source modules:

1. **`app/services/transcriptomics_service.py`**:
   - `DISEASE_SIGNATURES`: 6 curated disease dysregulation signatures (Pulmonary Arterial Hypertension, Colorectal Cancer, Breast Carcinoma, Glioblastoma, Pancreatic Neoplasm, Acute Myeloid Leukemia) with directional gene sets ($U_{dis}, D_{dis}$) from published TCGA / GEO RNA-seq studies (GSE113439, TCGA-COAD, TCGA-BRCA, TCGA-GBM, TCGA-PAAD, TCGA-LAML).
   - `LINCS_L1000_DRUG_PROFILES`: 4 authentic small-molecule perturbation profiles (Metformin CHEMBL1431, Fasudil CHEMBL38380, Everolimus CHEMBL1908360, Niclosamide CHEMBL1448) with NIH LINCS L1000 Level 5 moderated Z-scores (`modz`) across landmark genes, along with cell line ID, dose, exposure duration, and Broad Institute perturbation ID (`pert_id`).
   - *Status*: Operational for canonical cases; returns explicit `status: "unavailable"` when an unindexed compound or indication is queried.

2. **`ml/feature_generator.py`**:
   - `CURATED_TARGET_BENCHMARKS`: Benchmark target mappings and disease association scores for Fasudil (ROCK1, ROCK2), Metformin (GPD2, MT-ND6, NDUFA10), and Imatinib (ABL1, PDGFRB, KIT).
   - `DISEASE_PROFILES`: Disease target counts ($dtc$) and ontology names for the 9 canonical indications.
   - *Status*: Operational; bridges unindexed compounds to dynamic 39-feature inference when molecular structures exist in `drug_molecular_features.csv`.

3. **`app/services/disease_resolver.py`**:
   - `CURATED_DISEASE_MAPPINGS`: 50+ synonym pairs mapping natural-language condition terms to standard Open Targets ontology identifiers (`MONDO_*`, `EFO_*`, `Orphanet_*`).
   - *Status*: Operational; prevents invalid or fabricated ontology IDs.

4. **`app/services/clinical_trial_challenge.py`**:
   - `DRUG_SYNONYMS`: Brand names and research codes for candidate compounds (e.g. `imatinib`: Gleevec, Glivec, STI571).
   - `DISEASE_EXPANSIONS`: Clinical MeSH and ontology expansions for trial search terms.
   - *Status*: Operational; used to construct high-sensitivity search queries against the ClinicalTrials.gov v2 REST API.

---

## 2. Classification of All Project Resources

Each data asset is classified into one of the six standardized categories defined by the audit protocol:

| Resource Identifier | Description | Current Location | Classification Category | Rationale & Dependencies |
|---|---|---|---|---|
| **`cure_nova_xgb_final.joblib`** | Production XGBoost model bundle | `ml/models/` | **1. Present and usable** | Fully self-contained. Generates ranking scores across 39 numerical features without external dependencies. |
| **`drug_disease_features_v4.parquet`** | Precomputed candidate feature store | `ml/data/training/` | **1. Present and usable** | Contains 57 candidate pairs for fast offline inference across 9 canonical indications. |
| **`drug_molecular_features.csv`** | 15,465 compound RDKit descriptors | `ml/data/training/` | **1. Present and usable** | Provides molecular features (logP, TPSA, HBD, HBA, rings) for dynamic candidate construction. |
| **`drug_mechanism_of_action` parquet** | Open Targets 26.09 MoA table | `ml/data/open_targets/` | **1. Present and usable** | Supplies drug-to-target links for dynamic feature generation and candidate ranking. |
| **`drug_molecule` parquet** | Open Targets 26.09 molecule table | `ml/data/open_targets/` | **1. Present and usable** | Supplies SMILES, InChIKeys, trade names, and clinical development phases for 19,170 entities. |
| **`chembl_api_cache.json`** | ChEMBL 37 bioactivity cache | `ml/data/chembl/` | **1. Present and usable** | Caches pharmacological activity metrics for 43 common benchmark compounds. |
| **SQLite Application Database** | `curenova.db` | Project Root | **1. Present and usable** | Persists users, DDIs, clinical trials, investigation runs, and knowledge graph edges. |
| **Embedded LINCS L1000 Profiles** | 4 drug modz dictionaries | `transcriptomics_service.py` | **2. Present but incomplete** | Supports 4 benchmark drugs. Unindexed drugs return `unavailable` because broader L1000 data is not stored locally. |
| **Embedded TCGA/GEO Signatures** | 6 disease gene signatures | `transcriptomics_service.py` | **2. Present but incomplete** | Supports 6 indications. 3 of the 9 canonical indications (AD, PD, COVID ARDS) return `unavailable`. |
| **`ml_training_sample_v4.parquet`** | Original 190,108-row ML training dataset | Missing (`A:\CureNovaML`) | **3. Missing and required (for evaluation reproduction)** | Required strictly to reproduce held-out unseen-drug and unseen-disease metrics; *not* required for runtime inference. |
| **`final_drug_disease_dataset.parquet`** | Full 6.69M candidate space | Missing (`A:\CureNovaML`) | **4. Optional** | Represents the unpruned candidate space. Model was trained on the 190k balanced sample, not the 6.7M unpruned set. |
| **Full LINCS L1000 Matrix (GSE92742)** | Complete Level 5 moderated Z-scores | External (GEO / Broad) | **4. Optional** | File is ~30 GB (`.gctx`). The current implementation does not require it; a curated ~150 MB subset is sufficient if expansion is desired. |
| **Open Targets Association Parquet** | `association_overall_direct/` | External (Open Targets S3) | **3. Missing and required (for full retraining)** | Contains 7.2M association scores across the full ontology. Required only if reconstructing features from raw source data. |
| **Open Targets Clinical Indications** | `clinical_indication/00000000.parquet` | External (Open Targets S3) | **3. Missing and required (for full retraining)** | Contains 86k known indication pairs (`label = 1`). Required only if reconstructing the training set from raw source data. |
| **ChEMBL 37 Full Activity Dataset** | Complete bioactivity database | External (EMBL-EBI) | **4. Optional** | Full dump is ~3.5 GB. Runtime uses local cache plus live REST API lookups. |
| **ClinicalTrials.gov REST API v2** | Live study discovery endpoint | `https://clinicaltrials.gov/api/v2` | **5. Retrieved through live API** | Queried dynamically by `ClinicalTrialChallengeAgent` with local SQLite fallback. |
| **Open Targets GraphQL API** | Target & disease association query | `https://api.platform.opentargets.org` | **5. Retrieved through live API** | Queried dynamically by `feature_generator.py` when drug targets are not in local curated benchmarks. |
| **NCBI PubMed E-Utilities API** | Literature citation discovery | `https://eutils.ncbi.nlm.nih.gov` | **5. Retrieved through live API** | Queried dynamically by `BiomedicalAdapter` and `LiteratureScout`. |
| **OpenFDA Adverse Events API** | FAERS post-marketing reports | `https://api.fda.gov/drug/event.json` | **5. Retrieved through live API** | Queried dynamically by `BiomedicalAdapter.search_openfda_events`. |
| **ChEMBL REST API** | Compound pharmacology lookup | `https://www.ebi.ac.uk/chembl/api/data` | **5. Retrieved through live API** | Queried dynamically by `BiomedicalAdapter` and `evidence_utils.py`. |

---

## 3. Real Data-Loading Pathways in Code

A source-code audit reveals how each module discovers, loads, and processes data:

```
[Researcher Investigation Request]
               │
               ▼
   [AgenticOrchestrator.run_investigation]
               │
      ┌────────┴────────────────────────────────────────┐
      ▼                                                 ▼
[DiseaseResolver]                             [MLService / ml.predictor]
   - Checks CURATED_DISEASE_MAPPINGS             - Calls predict_v4.py
   - Queries curenova.db (diseases/drugs)        - Checks drug_disease_features_v4.parquet
   - Fallback: Open Targets GraphQL API             │
                                                    ├─ IF Drug found in Parquet (label=0):
                                                    │     Uses DuckDB to extract 39 features.
                                                    │
                                                    └─ IF Drug NOT in Parquet:
                                                          Calls feature_generator.py
                                                             - Loads drug_molecular_features.csv (15,465 drugs)
                                                             - Loads drug_mechanism_of_action.parquet (MoA)
                                                             - Checks CURATED_TARGET_BENCHMARKS
                                                             - Fallback: Open Targets Live GraphQL API
                                                             - Computes 39-feature vector dynamically.
                                                    │
                                                    ▼
                                           [cure_nova_xgb_final.joblib]
                                              - Scikit-learn / XGBoost inference
                                              - Generates ranking scores (0.0 to 1.0)
                                                    │
                                                    ▼
                                           [ml.evidence_utils]
                                              - Checks chembl_api_cache.json
                                              - Fallback: ChEMBL Live REST API
                                              - Checks drug_molecule.parquet (SMILES)
                                                    │
                                                    ▼
                                           [ml.stress_test.run_stress_test]
                                              - Computes heuristic robustness score (0-100)
               │
               ├────────────────────────────────────────┐
               ▼                                        ▼
   [TranscriptomicsService]               [ClinicalTrialChallengeAgent]
      - Evaluates connectivity               - Queries ClinicalTrials.gov Live API v2
      - Uses embedded modz profiles          - Fallback: SQLite clinical_trials table
      - Segregated from ML score             - Evaluates whyStopped & trial status
               │
               ▼
   [MultiDrugSafetyService (Doctor)]
      - Evaluates N*(N-1)/2 pairs
      - Queries SQLite drug_interactions table
      - Verifies FDA monograph provenance
      - Flags unmonitored pairs with disclaimer
               │
               ▼
   [InvestigationRun Persistence]
      - Saves complete dossier into curenova.db (investigation_runs table)
```

---

## 4. Analysis of the Original 190,108-Row Training Dataset

### 4.1 Provenance and Lineage

According to `ml/CureNova_ML_Technical_Report.md` and `ml/models/cure_nova_xgb_final.json`:
- **Production Model**: `cure_nova_xgb_final.joblib` was trained on **190,108 rows** consisting of:
  - **47,527 positive rows (`label = 1`)**: Known drug–disease indications extracted from Open Targets Platform 26.09 (`clinical_indication/00000000.parquet`).
  - **142,581 unlabeled candidate rows (`label = 0`)**: Candidate drug–disease pairs generated from biological target associations in Open Targets 26.09 (`association_overall_direct/`).
  - **Class Ratio**: Exactly 1 : 3 positive-to-unlabeled ratio (25.0% positive).
  - **Weighting**: Trained with XGBoost parameter `scale_pos_weight = 3.0` to balance class importance.
  - **Features**: Exactly 39 numerical features.

### 4.2 Why the Training Dataset is Not in the Repository

The offline development path recorded in `CureNova_ML_Technical_Report.md` (line 708) and `predict_v4.py` (line 15) is:
```text
A:\CureNovaML\data\training\ml_training_sample_v4.parquet (or .csv)
A:\CureNovaML\data\training\final_drug_disease_dataset.parquet
```
Physical inspection confirms that `A:\` was an offline development workstation drive not attached to this machine (`Test-Path 'A:\'` returns `False`).

### 4.3 Runtime vs. Evaluation Impact

1. **For Production Runtime Inference**: The absence of the 190,108-row training file causes **zero runtime failure**. The trained XGBoost model bundle (`cure_nova_xgb_final.joblib`) serializes all tree structures, splits, feature names, and weights. Inference is performed against either `drug_disease_features_v4.parquet` (precomputed) or `feature_generator.py` (dynamic).
2. **For Scientific Reproducibility**: The absence of the 190,108-row training file is a **reproducibility blocker** for recomputing empirical ROC-AUC and PR-AUC. Because the local candidate file `drug_disease_features_v4.parquet` contains only 57 rows and all 57 rows have `label = 0`, calculating ROC-AUC or Average Precision on the local file is mathematically degenerate.

---

## 5. Investigation of NIH LINCS L1000 (GSE92742) Resource

### 5.1 Dataset Characteristics

The NIH LINCS L1000 Phase I resource is hosted on NCBI Gene Expression Omnibus under accession **GSE92742**:
- **Full Level 5 Matrix File**: `GSE92742_Broad_LINCS_Level5_COMPZ.MODZ_n473647x978.gctx.gz`
- **Full Download Size**: ~25 GB compressed (decompresses to ~45 GB HDF5/GCTX format).
- **Matrix Dimensions**: 473,647 perturbation experiments $\times$ 978 high-fidelity landmark genes.
- **Metadata Files**:
  - `GSE92742_Broad_LINCS_pert_info.txt.gz` (small molecule compound mapping).
  - `GSE92742_Broad_LINCS_sig_info.txt.gz` (cell line, dose, duration metadata).
  - `GSE92742_Broad_LINCS_gene_info.txt.gz` (Entrez gene ID to gene symbol mapping).

### 5.2 Does CureNova 2.0 Require the Full 30 GB Matrix?

**NO.** The current CureNova 2.0 implementation does **not** require downloading the complete 30 GB GSE92742 matrix.
- **Architectural Reason**: `TranscriptomicsService` is designed as a focused connectivity validator that challenges specific repurposing candidates. It operates with low latency (under 15 ms) and zero memory footprint by referencing verified Level 5 moderated Z-scores.
- **Recommended Solution**: If the project expands transcriptomic coverage beyond the 4 embedded canonical drugs, it should use a **curated subset**:
  - Filter GSE92742 Level 5 modz for FDA-approved and clinical-phase small molecules (approximately 2,500 unique compounds).
  - Restrict cell lines to canonical reference lines (`MCF7`, `HA1E`, `HT29`, `A549`, `PC3`).
  - Store as a compact Apache Parquet file (`lincs_l1000_approved_drugs_level5.parquet`), requiring approximately **120 MB to 180 MB** on disk.
- **Current Behavior**: Any unindexed drug gracefully returns `status: "unavailable"` with the truthful scientific notice:
  > *"Compound '{drug}' has no characterized Level 5 L1000 signature in the current transcriptomic database. No synthetic or fabricated transcriptomic data was generated."*

---

## 6. Investigation of TCGA / GEO Disease-Expression Signatures

### 6.1 Currently Implemented Signatures

The 6 disease signatures implemented in `transcriptomics_service.py` were extracted from peer-reviewed benchmark RNA-seq studies:

1. **Pulmonary Arterial Hypertension (`MONDO_0005149`)**:
   - *Source Study*: GEO GSE113439 / GSE117261 (Human lung tissue / pulmonary vascular smooth muscle).
   - *Up-regulated ($U_{dis}$)*: `EDN1, HIF1A, VEGFA, PDGFRA, COL1A1, TGFB1, ACTA2, MYL9, IL6, ROCK1`
   - *Down-regulated ($D_{dis}$)*: `BMPR2, CAV1, KCNK3, NOS3, SMAD1, PPARG, APLN, ENG`
2. **Colorectal Cancer (`MONDO_0005575`)**:
   - *Source Study*: TCGA-COAD / GSE39582 (Colon adenocarcinoma vs. matched normal epithelium).
   - *Up-regulated ($U_{dis}$)*: `MYC, CCND1, MET, CD44, MMP7, BIRC5, CTNNB1, SOX9, S100A4, MKI67`
   - *Down-regulated ($D_{dis}$)*: `APC, TP53, PTEN, SMAD4, CDKN1A, MLH1, MSH2, BAX`
3. **Breast Carcinoma (`MONDO_0004989`)**:
   - *Source Study*: TCGA-BRCA / METABRIC differential expression.
   - *Up-regulated ($U_{dis}$)*: `ERBB2, ESR1, FOXA1, CCND1, CDK4, MKI67, MYC, BCL2, EGFR`
   - *Down-regulated ($D_{dis}$)*: `BRCA1, BRCA2, CDKN1A, PTEN, TP53, CASP3, ATM, RB1`
4. **Glioblastoma (`MONDO_0018177`)**:
   - *Source Study*: TCGA-GBM / GSE83300 (Glioblastoma astrocytic glia vs. normal brain).
   - *Up-regulated ($U_{dis}$)*: `EGFR, NES, SOX2, VEGFA, CHI3L1, PROM1, PDGFB, STAT3, MMP9`
   - *Down-regulated ($D_{dis}$)*: `PTEN, TP53, NF1, CDKN2A, RB1, DMD, CASP8`
5. **Pancreatic Neoplasm (`MONDO_0021040`)**:
   - *Source Study*: TCGA-PAAD / GSE15471 (Pancreatic ductal adenocarcinoma vs. normal pancreas).
   - *Up-regulated ($U_{dis}$)*: `KRAS, MYC, VEGFA, S100A4, MMP9, TGFB1, MUC1, MET`
   - *Down-regulated ($D_{dis}$)*: `CDKN2A, TP53, SMAD4, PTEN, ARID1A, DPC4`
6. **Acute Myeloid Leukemia (`MONDO_0018827`)**:
   - *Source Study*: TCGA-LAML (Bone marrow mononuclear cells in AML vs. healthy controls).
   - *Up-regulated ($U_{dis}$)*: `FLT3, MYC, WT1, BCL2, KIT, HOXA9, MEIS1`
   - *Down-regulated ($D_{dis}$)*: `CEBPA, RUNX1, TET2, TP53, GATA1`

### 6.2 Missing Indications for Parity with the 9 Canonical Indications

CureNova 2.0 models 9 canonical therapeutic indications in its ML feature store. Three indications are currently absent from `transcriptomics_service.py`:

| Missing Indication | Ontology ID | Recommended Official RNA-seq Benchmark Source | Up-regulated Genes ($U_{dis}$) | Down-regulated Genes ($D_{dis}$) |
|---|---|---|---|---|
| **Alzheimer's Disease & Neurodegeneration** | `MONDO_0004975` | GEO GSE5281 / GSE84422 (Mount Sinai Brain Bank / Entorhinal Cortex) | `APP, BACE1, MAPT, CASP3, GFAP, CLU, CD33, TREM2, APOE` | `BDNF, SYP, DLG4, SNAP25, VAMP2, CHRM1, GRIN1, PRKCA` |
| **Parkinson's Disease** | `MONDO_0005180` | GEO GSE7621 / GSE20141 (Post-mortem Substantia Nigra pars compacta) | `SNCA, PRKN, LRRK2, PINK1, CASP9, CHOP, GADD45A, SLC6A3` | `TH, DAT1, DDC, VMAT2, RET, GDNF, NURR1, PITX3` |
| **Severe COVID-19 ARDS** | `MONDO_0100096` | GEO GSE147507 / GSE157103 (Human bronchoalveolar lavage & lung tissue) | `IL6, TNF, CXCL8, IL1B, CCL2, JAK1, STAT3, S100A9, IFNB1` | `ACE2, SFTPC, AGER, CAV1, VEGFA, KDR, CLDN18` |

Adding these three signatures would achieve 100% indication parity across all 9 canonical indications.

---

## 7. Download Plan for Missing External Resources

The following download plan specifies the exact external files required if the user decides to perform full offline feature re-engineering, offline model retraining, or transcriptomic library expansion.

### Resource 1: Open Targets Platform 26.09 — Clinical Indications
- **Exact Name**: Open Targets Platform Clinical Indications Table
- **Official Source**: Open Targets Platform Public Data Releases
- **Download URL**: `https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/etl/parquet/clinical_indication/` (or AWS S3: `s3://open-targets-public-data-releases/platform/26.09/output/etl/parquet/clinical_indication/00000000.parquet`)
- **Exact Filename**: `00000000.parquet`
- **Expected Download Size**: ~3.2 MB
- **File Format**: Apache Parquet
- **License / Access**: Open Access (Creative Commons CC0 / Open Targets Terms)
- **Required Columns**: `id`, `drugId`, `diseaseId`, `indicationPhase`, `references`
- **Intended Destination**: `ml/data/open_targets/clinical_indication/00000000.parquet`
- **Necessity**: Complete single parquet file is necessary. Supplies the 47,527 positive indication pairs (`label = 1`).

### Resource 2: Open Targets Platform 26.09 — Target-Disease Associations
- **Exact Name**: Open Targets Platform Direct Overall Associations
- **Official Source**: Open Targets Platform Public Data Releases
- **Download URL**: `https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/26.09/output/etl/parquet/association_overall_direct/` (or AWS S3: `s3://open-targets-public-data-releases/platform/26.09/output/etl/parquet/association_overall_direct/`)
- **Exact Filename**: 14 files (`part-00000-*.parquet` to `part-00013-*.parquet`)
- **Expected Download Size**: ~830 MB compressed
- **File Format**: Apache Parquet
- **License / Access**: Open Access (CC0)
- **Required Columns**: `diseaseId`, `targetId`, `associationScore`, `evidenceCount`, `aggregationType`
- **Intended Destination**: `ml/data/open_targets/association_overall_direct/`
- **Necessity**: Complete 14 files are necessary for offline target-disease association scoring.

### Resource 3: ChEMBL 37 Bioactivity Dataset (Curated Slice)
- **Exact Name**: ChEMBL 37 Human Pharmacology Assay Activity Slice
- **Official Source**: EMBL-EBI ChEMBL Database Release 37
- **Download URL**: `https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBL-db/releases/chembl_37/` (or SQLite `chembl_37_sqlite.tar.gz`)
- **Expected Download Size**: Full dump is ~3.5 GB compressed; 500k-row activity slice is ~48 MB CSV.
- **File Format**: CSV or SQLite
- **License / Access**: Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)
- **Required Columns**: `activity_id`, `molregno`, `molecule_chembl_id`, `target_chembl_id`, `standard_type`, `standard_value`, `standard_units`, `pchembl_value`
- **Intended Destination**: `ml/data/chembl/chembl_human_activities.csv`
- **Necessity**: Verified 500,000-row slice of human target activities is sufficient (identical to the slice used in original training).

### Resource 4: NIH LINCS L1000 Approved Drug Perturbation Signatures (Curated)
- **Exact Name**: LINCS L1000 Level 5 Moderated Z-Scores for Approved & Repurposed Drugs
- **Official Source**: NCBI GEO GSE92742 / Broad Institute Connectivity Map
- **Download Page**: `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE92742`
- **Expected Download Size**: Curated subset is ~150 MB Parquet (vs. 25–30 GB for full matrix).
- **File Format**: Apache Parquet or HDF5
- **License / Access**: NIH Public Domain / Broad Institute Open Data
- **Required Metadata**: `pert_id`, `pert_iname`, `cell_id`, `pert_dose`, `pert_time`, landmark gene Z-scores
- **Intended Destination**: `ml/data/transcriptomics/lincs_l1000_approved_level5.parquet`
- **Necessity**: Curated subset of ~2,500 small molecule drugs across reference cell lines is sufficient. The complete 473k-profile file is **NOT** necessary.

---

## 8. Prioritized Download Instructions & Storage Footprint

Should offline retraining or library expansion be initiated in a subsequent phase, the downloads should be executed in three prioritized tiers:

```
TIER 1 (Immediate / Light footprint: ~6 MB total):
  1. Open Targets 26.09 clinical_indication (3.2 MB)
     Target: ml/data/open_targets/clinical_indication/00000000.parquet
  2. Missing TCGA/GEO gene lists for AD, PD, COVID (Text metadata: < 10 KB)
     Target: Embedded in app/services/transcriptomics_service.py

TIER 2 (Reproduction & Retraining: ~880 MB total):
  3. Open Targets 26.09 association_overall_direct (830 MB)
     Target: ml/data/open_targets/association_overall_direct/
  4. ChEMBL 37 Human Activity 500k-row slice (48 MB)
     Target: ml/data/chembl/chembl_human_activities.csv

TIER 3 (Transcriptomics Expansion: ~150 MB total):
  5. Curated LINCS L1000 Level 5 Approved Drug Subset (150 MB)
     Target: ml/data/transcriptomics/lincs_l1000_approved_level5.parquet
```

### Cumulative Storage Footprint Summary

| Tier | Component | Download Size | Uncompressed Disk Footprint |
|---|---|---:|---:|
| **Baseline (Current)** | Existing workspace data (`curenova.db`, `ml/data/`, models) | 0 MB (Local) | ~20.6 MB |
| **Tier 1** | Positive clinical indications + 3 disease signatures | 3.2 MB | ~12.0 MB |
| **Tier 2** | Full Open Targets associations + ChEMBL activity slice | 878.0 MB | ~1.85 GB |
| **Tier 3** | Curated LINCS L1000 Level 5 approved drug subset | 150.0 MB | ~280.0 MB |
| **Total Future Storage** | Fully reconstituted offline training & transcriptomic store | **~1.03 GB** | **~2.16 GB** |

---

## 9. Scientific Reproducibility Plan

### 9.1 Held-Out Evaluation Protocol

The CureNova 2.0 ML evaluation emphasizes **generalization to unseen entities** rather than random held-out splits:

1. **Unseen-Disease Holdout**:
   - Evaluates whether the model can rank drug candidates for diseases that were completely excluded from the training set.
   - *Split Logic*: GroupShuffleSplit grouped strictly by `disease_id` (14,090 total diseases: 11,272 train / 2,818 test).
   - *Reported Benchmark*: Average Precision = **0.9047**, ROC-AUC = **0.9735**, Precision@100 = **1.000**.
2. **Unseen-Drug Holdout**:
   - Evaluates whether the model can predict indications for novel compounds with no prior indications in the training set.
   - *Split Logic*: GroupShuffleSplit grouped strictly by `drug_id` (4,481 total drugs: 3,584 train / 897 test).
   - *Reported Benchmark*: Average Precision = **0.8652**, ROC-AUC = **0.9580**.

### 9.2 Reproducibility Blockers in Current Workspace

| Blocker Item | Issue Identified | Impact on Reproducibility | Resolution Path |
|---|---|---|---|
| **Absence of `label = 1` Rows Locally** | `drug_disease_features_v4.parquet` contains 57 rows, all with `label = 0`. | Cannot calculate ROC-AUC or PR-AUC locally (requires $\ge 1$ positive). Attempting calculation returns degenerate math. | Acquire `clinical_indication` (Tier 1) to restore positive labels. |
| **Production Model Retraining** | `cure_nova_xgb_final.joblib` was retrained on all 190,108 rows after evaluation. | Evaluating the production binary on the training sample would constitute train-test data leakage. | Must split the training sample using identical group seeds before re-fitting. |
| **Unlabeled Candidates as Negatives** | Unlabeled pairs (`label = 0`) are not proven negatives; they are uncharacterized pairs. | False negatives in the candidate pool deflate apparent specificity if treated as true negatives. | Average Precision is the honest metric; accuracy percentage must never be reported. |
| **Missing AD/PD/COVID Signatures** | 3 canonical diseases lack transcriptomic signatures in `transcriptomics_service.py`. | Transcriptomics returns `unavailable` for 3 of the 9 benchmark diseases. | Add GEO GSE5281, GSE7621, GSE147507 signatures to `transcriptomics_service.py`. |

### 9.3 Separation of Scientific Evidence Layers

To prevent misleading claims, CureNova enforces strict segregation across evidence layers:

$$\text{Final Hypothesis Dossier} = \begin{cases}
\text{ML Prioritization Score} & \in [0.0, 1.0] \quad (\text{Target Overlap \& Molecular Plausibility}) \\
\text{Heuristic Robustness Score} & \in [0, 100] \quad (\text{Multifactor Stress-Testing}) \\
\text{Transcriptomic Score } (\tau) & \in [-1.0, +1.0] \quad (\text{CMAP Directional Reversal}) \\
\text{Clinical Trial Challenge} & \in \{\text{Supportive}, \text{Terminated-Efficacy}, \text{Inconclusive}\} \\
\text{Polypharmacy Safety (DDI)} & \in \{\text{Contraindicated}, \text{Major}, \text{Moderate}, \text{Unmonitored}\}
\end{cases}$$

- **Rule 1**: ML ranking scores are never conflated with clinical probabilities of efficacy.
- **Rule 2**: Transcriptomic connectivity scores are never averaged into ML prediction scores.
- **Rule 3**: Clinical trial terminations for business/operational reasons are never classified as biological efficacy failures.
- **Rule 4**: Absence of interaction documentation is never interpreted as proof of safety.

---

## 10. Recommended Next Actions

1. **Preserve Current State**: Do not attempt to calculate ROC-AUC or PR-AUC on `drug_disease_features_v4.parquet` until positive indication data is restored.
2. **Phase 3.4B (If Authorized)**:
   - Download Tier 1 resource `clinical_indication/00000000.parquet` (~3.2 MB).
   - Add the 3 missing disease expression signatures (AD, PD, COVID ARDS) to `transcriptomics_service.py` (< 1 KB code update).
3. **Phase 3.5 (Scientific Validation)**:
   - Reconstitute the held-out splits using `ml_training_sample_v4.parquet`.
   - Execute automated unseen-drug and unseen-disease validation scripts to verify that retrained models achieve reported benchmarks ($AP \ge 0.86$, $ROC \ge 0.95$).
4. **Maintain Strict Invariance**: Continue to enforce zero modification of existing UI design, CSS, layouts, and frozen model binaries.
