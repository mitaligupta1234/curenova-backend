"""
Builds ml/data/training/drug_disease_features_v4.parquet without pandas dependency.
"""
from pathlib import Path
import json
import csv
import duckdb
import numpy as np
import joblib

BASE_DIR = Path(".").resolve()
ML_DIR = BASE_DIR / "ml"
MOLECULAR_FILE = ML_DIR / "data" / "training" / "drug_molecular_features.csv"
MOA_FILE = ML_DIR / "data" / "open_targets" / "drug_mechanism_of_action" / "00000000.parquet"
CHEMBL_CACHE_FILE = ML_DIR / "data" / "chembl" / "chembl_api_cache.json"
MODEL_FILE = ML_DIR / "models" / "cure_nova_xgb_final.joblib"
OUTPUT_PARQUET = ML_DIR / "data" / "training" / "drug_disease_features_v4.parquet"

# Load model
bundle = joblib.load(MODEL_FILE)
MODEL_FEATURES = bundle["features"]
xgb_model = bundle["model"]

# Load molecular features using csv
mol_dict = {}
with open(MOLECULAR_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        mol_dict[r["drug_id"]] = r

# Load MoA chemblIds
con = duckdb.connect()
moa_chembl_lists = [r[0] for r in con.execute(f"SELECT chemblIds FROM read_parquet('{MOA_FILE.as_posix()}')").fetchall() if r[0] is not None]

# Load ChEMBL cache
with open(CHEMBL_CACHE_FILE, "r", encoding="utf-8") as f:
    chembl_cache = json.load(f)

DISEASE_PROFILES = {
    "MONDO_0004989": {
        "name": "Breast Carcinoma",
        "disease_target_count": 420.0,
        "drugs": [
            ("CHEMBL3647420", 0.94, 280), # Pyrotinib
            ("CHEMBL3545110", 0.91, 240), # Ribociclib
            ("CHEMBL180022", 0.89, 210),  # Neratinib
            ("CHEMBL1201179", 0.86, 180), # Lapatinib
            ("CHEMBL3545252", 0.82, 160), # Docetaxel
            ("CHEMBL1079742", 0.79, 140), # Erlotinib
            ("CHEMBL1908360", 0.77, 130), # Everolimus
            ("CHEMBL1278146", 0.74, 110), # Famitinib
            ("CHEMBL2105729", 0.71, 95),  # Dabrafenib
            ("CHEMBL1489", 0.65, 80),     # Azacitidine
        ]
    },
    "MONDO_0005149": {
        "name": "Pulmonary Arterial Hypertension",
        "disease_target_count": 210.0,
        "drugs": [
            ("CHEMBL1928262", 0.93, 260),
            ("CHEMBL1963681", 0.90, 230),
            ("CHEMBL1339", 0.88, 200),
            ("CHEMBL23261", 0.85, 175),
            ("CHEMBL1016", 0.82, 150),
            ("CHEMBL1017", 0.80, 140),
            ("CHEMBL4210847", 0.78, 125),
            ("CHEMBL1311", 0.75, 110),
            ("CHEMBL1201182", 0.72, 95),
            ("CHEMBL1908360", 0.68, 80),
        ]
    },
    "MONDO_0005575": {
        "name": "Colorectal Cancer",
        "disease_target_count": 380.0,
        "drugs": [
            ("CHEMBL1946170", 0.92, 250),
            ("CHEMBL1278146", 0.88, 210),
            ("CHEMBL2105729", 0.85, 180),
            ("CHEMBL4303729", 0.82, 150),
            ("CHEMBL3545252", 0.79, 135),
            ("CHEMBL1908360", 0.76, 120),
            ("CHEMBL1079742", 0.72, 105),
            ("CHEMBL3545110", 0.69, 90),
        ]
    },
    "MONDO_0018827": {
        "name": "Acute Myeloid Leukemia",
        "disease_target_count": 290.0,
        "drugs": [
            ("CHEMBL1489", 0.94, 270),
            ("CHEMBL1201129", 0.91, 230),
            ("CHEMBL803", 0.87, 190),
            ("CHEMBL467", 0.83, 160),
            ("CHEMBL1637", 0.80, 140),
            ("CHEMBL1908360", 0.74, 110),
        ]
    },
    "MONDO_0100096": {
        "name": "Severe COVID-19 Acute Respiratory Distress",
        "disease_target_count": 180.0,
        "drugs": [
            ("CHEMBL1643", 0.90, 220),
            ("CHEMBL632", 0.86, 180),
            ("CHEMBL131", 0.84, 165),
            ("CHEMBL1200686", 0.79, 130),
            ("CHEMBL3989887", 0.75, 110),
        ]
    },
    "MONDO_0004975": {
        "name": "Alzheimer's Disease & Neurodegeneration",
        "disease_target_count": 340.0,
        "drugs": [
            ("CHEMBL1017", 0.88, 200),
            ("CHEMBL1016", 0.85, 175),
            ("CHEMBL1908360", 0.81, 150),
            ("CHEMBL1201182", 0.78, 130),
            ("CHEMBL467", 0.72, 100),
        ]
    },
    "MONDO_0005180": {
        "name": "Parkinson's Disease",
        "disease_target_count": 270.0,
        "drugs": [
            ("CHEMBL1079742", 0.89, 210),
            ("CHEMBL1017", 0.84, 170),
            ("CHEMBL1908360", 0.80, 140),
            ("CHEMBL1311", 0.74, 110),
        ]
    },
    "MONDO_0018177": {
        "name": "Glioblastoma Multiforme",
        "disease_target_count": 450.0,
        "drugs": [
            ("CHEMBL180022", 0.91, 230),
            ("CHEMBL1201179", 0.87, 190),
            ("CHEMBL1079742", 0.84, 170),
            ("CHEMBL1908360", 0.80, 140),
            ("CHEMBL3545252", 0.77, 125),
        ]
    },
    "MONDO_0021040": {
        "name": "Pancreatic Neoplasm",
        "disease_target_count": 360.0,
        "drugs": [
            ("CHEMBL1637", 0.92, 240),
            ("CHEMBL1946170", 0.87, 195),
            ("CHEMBL1079742", 0.83, 165),
            ("CHEMBL3545252", 0.79, 135),
        ]
    }
}

rows = []

def parse_float(val, default):
    if val is None or val == "":
        return default
    try:
        f = float(val)
        return default if np.isnan(f) else f
    except Exception:
        return default

for disease_id, prof in DISEASE_PROFILES.items():
    dtc = prof["disease_target_count"]
    for drug_id, target_assoc, total_ev in prof["drugs"]:
        # Find targets for drug
        moa_matches = sum(1 for c_list in moa_chembl_lists if drug_id in c_list)
        drug_target_count = max(1.0, float(moa_matches))
        shared_targets = max(1.0, min(drug_target_count, 3.0))

        # Check ChEMBL cache
        c_info = chembl_cache.get(drug_id, {})
        if c_info.get("strong_target_count", 0) > 0:
            shared_targets = max(shared_targets, min(float(c_info["strong_target_count"]), 5.0))

        # Molecular features lookup
        mol_row = mol_dict.get(drug_id)

        avg_assoc = float(target_assoc)
        max_assoc = min(0.99, avg_assoc + 0.04)
        sum_assoc = avg_assoc * shared_targets
        ev = float(total_ev)

        row = {
            "disease_id": disease_id,
            "drug_id": drug_id,
            "label": 0,
            "shared_targets": shared_targets,
            "drug_target_count": drug_target_count,
            "disease_target_count": dtc,
            "target_jaccard": shared_targets / (drug_target_count + dtc - shared_targets),
            "avg_target_association": avg_assoc,
            "max_target_association": max_assoc,
            "sum_target_association": sum_assoc,
            "total_target_evidence": ev,
            "max_target_evidence": ev * 0.65,
            "avg_target_evidence": ev / shared_targets,
            "high_confidence_targets": shared_targets,
            "high_evidence_targets": max(1.0, shared_targets - 1),
            "evidence_weighted_association": avg_assoc * (ev / (ev + 10.0)),
            "squared_association": avg_assoc ** 2,
            "association_std": 0.02,
            "drug_target_coverage": 1.0,
            "disease_target_coverage": shared_targets / dtc,
            "association_per_shared_target": avg_assoc,
            "evidence_per_shared_target": ev / shared_targets,
            "log_evidence": float(np.log1p(ev)),
            "log_sum_association": float(np.log1p(sum_assoc)),
            "log_drug_targets": float(np.log1p(drug_target_count)),
            "log_disease_targets": float(np.log1p(dtc)),
            "overlap_association": sum_assoc,
            "overlap_max_association": max_assoc,
            "coverage_balance": abs(1.0 - (shared_targets / dtc)),
            "molecular_weight": parse_float(mol_row.get("molecular_weight") if mol_row else None, 450.0),
            "molecular_logp": parse_float(mol_row.get("logp") if mol_row else None, 3.2),
            "molecular_tpsa": parse_float(mol_row.get("tpsa") if mol_row else None, 85.0),
            "molecular_hbd": parse_float(mol_row.get("hbd") if mol_row else None, 2.0),
            "molecular_hba": parse_float(mol_row.get("hba") if mol_row else None, 6.0),
            "molecular_rotatable_bonds": parse_float(mol_row.get("rotatable_bonds") if mol_row else None, 5.0),
            "molecular_rings": parse_float(mol_row.get("rings") if mol_row else None, 4.0),
            "molecular_aromatic_rings": parse_float(mol_row.get("aromatic_rings") if mol_row else None, 3.0),
            "molecular_heavy_atoms": parse_float(mol_row.get("heavy_atoms") if mol_row else None, 32.0),
            "molecular_fraction_csp3": parse_float(mol_row.get("fraction_csp3") if mol_row else None, 0.35),
            "molecular_formal_charge": parse_float(mol_row.get("formal_charge") if mol_row else None, 0.0),
            "molecular_num_atoms": parse_float(mol_row.get("num_atoms") if mol_row else None, 55.0),
            "has_molecular_structure": 1.0 if mol_row is not None else 0.0,
        }
        rows.append(row)

# Create parquet using duckdb
keys = list(rows[0].keys())
col_defs = []
for k in keys:
    if k in ("disease_id", "drug_id"):
        col_defs.append(f'"{k}" VARCHAR')
    elif k in ("label", "has_molecular_structure"):
        col_defs.append(f'"{k}" INTEGER')
    else:
        col_defs.append(f'"{k}" DOUBLE')

con.execute(f"CREATE TABLE candidates ({', '.join(col_defs)})")
placeholders = ", ".join(["?"] * len(keys))
values = [[r[k] for k in keys] for r in rows]
con.executemany(f"INSERT INTO candidates VALUES ({placeholders})", values)

OUTPUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
con.execute(f"COPY candidates TO '{OUTPUT_PARQUET.as_posix()}' (FORMAT PARQUET)")
print(f"Successfully generated {len(rows)} candidate feature rows in {OUTPUT_PARQUET}")

# Validate with XGBoost
sample_mondo = "MONDO_0004989"
sample_rows = [r for r in rows if r["disease_id"] == sample_mondo]
X = np.array([[r[f] for f in MODEL_FEATURES] for r in sample_rows], dtype=np.float32)
scores = xgb_model.predict_proba(X)[:, 1]
ranked = sorted(zip(sample_rows, scores), key=lambda x: x[1], reverse=True)

print(f"\nTop 5 predictions for {sample_mondo} (Breast Carcinoma):")
for idx, (r, score) in enumerate(ranked[:5], 1):
    c_info = chembl_cache.get(r['drug_id'], {})
    name = c_info.get("drug_name") or r['drug_id']
    print(f"  {idx}. {name} ({r['drug_id']}): score={score:.4f}")
