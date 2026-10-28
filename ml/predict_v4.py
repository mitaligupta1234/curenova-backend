from pathlib import Path
import json
import csv
import sys
import duckdb
import joblib
import numpy as np

try:
    from .feature_generator import generate_dynamic_features_for_drug
except ImportError:
    from feature_generator import generate_dynamic_features_for_drug

_LOCAL_BASE = Path(__file__).resolve().parent
BASE = _LOCAL_BASE if (_LOCAL_BASE / "models" / "cure_nova_xgb_final.joblib").exists() else Path(r"A:\CureNovaML")

MODEL_PATH = BASE / "models" / "cure_nova_xgb_final.joblib"
DATA_PATH = BASE / "data" / "training" / "drug_disease_features_v4.parquet"
MOLECULAR_PATH = BASE / "data" / "training" / "drug_molecular_features.csv"

bundle = joblib.load(MODEL_PATH)

model = bundle["model"]
FEATURES = bundle["features"]
MODEL_VERSION = bundle.get("model_version", "cure-nova-xgb-v2")


def query_candidates(disease_id):
    safe_id = str(disease_id).replace("'", "''")

    if not DATA_PATH.exists():
        return []

    sql = f"""
    SELECT *
    FROM read_parquet('{DATA_PATH.as_posix()}')
    WHERE disease_id = '{safe_id}'
      AND label = 0
    """

    try:
        con = duckdb.connect()
        rel = con.execute(sql)
        cols = [desc[0] for desc in rel.description]
        rows = rel.fetchall()
        return [dict(zip(cols, r)) for r in rows]
    except Exception as exc:
        raise RuntimeError(f"DuckDB candidate query error: {exc}")


def query_candidates_for_drug(drug_id):
    safe_id = str(drug_id).replace("'", "''")

    if not DATA_PATH.exists():
        return []

    sql = f"""
    SELECT *
    FROM read_parquet('{DATA_PATH.as_posix()}')
    WHERE drug_id = '{safe_id}'
      AND label = 0
    """

    try:
        con = duckdb.connect()
        rel = con.execute(sql)
        cols = [desc[0] for desc in rel.description]
        rows = rel.fetchall()
        return [dict(zip(cols, r)) for r in rows]
    except Exception as exc:
        raise RuntimeError(f"DuckDB candidate drug query error: {exc}")


def add_molecular_features(candidates):
    if not candidates:
        return candidates

    # Check if molecular features already present
    first = candidates[0]
    if "molecular_weight" in first and first["molecular_weight"] is not None:
        for cand in candidates:
            if "has_molecular_structure" not in cand:
                cand["has_molecular_structure"] = 1
        return candidates

    molecular_dict = {}
    if MOLECULAR_PATH.exists():
        with open(MOLECULAR_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                molecular_dict[r["drug_id"]] = r

    for cand in candidates:
        drug_id = cand.get("drug_id")
        mol_row = molecular_dict.get(drug_id, {})
        cand["has_molecular_structure"] = 1 if drug_id in molecular_dict else 0
        for col in [
            "molecular_weight", "logp", "tpsa", "hbd", "hba",
            "rotatable_bonds", "rings", "aromatic_rings", "heavy_atoms",
            "fraction_csp3", "formal_charge", "num_atoms"
        ]:
            val = mol_row.get(col)
            try:
                fval = float(val) if val is not None and val != "" else 0.0
            except Exception:
                fval = 0.0
            cand[col] = fval
            mol_col = f"molecular_{col}" if not col.startswith("molecular_") else col
            if mol_col in FEATURES:
                cand[mol_col] = fval

    return candidates


def predict(disease_id, top_k=10):
    candidates = query_candidates(disease_id)

    if not candidates:
        return {
            "disease_id": disease_id,
            "model_version": MODEL_VERSION,
            "candidate_count": 0,
            "candidates": [],
            "message": (
                "No unlabeled candidate pairs were found for this "
                "disease in the current candidate dataset."
            )
        }

    candidates = add_molecular_features(candidates)

    missing = [
        feature
        for feature in FEATURES
        if feature not in candidates[0]
    ]

    if missing:
        raise RuntimeError(
            "Missing model features: " + ", ".join(missing)
        )

    X_rows = []
    for cand in candidates:
        row_vals = []
        for feat in FEATURES:
            val = cand.get(feat, 0.0)
            if val is None or np.isnan(val) or np.isinf(val):
                val = 0.0
            row_vals.append(float(val))
        X_rows.append(row_vals)

    X = np.array(X_rows, dtype=np.float32)

    scores = model.predict_proba(X)[:, 1]

    for cand, score in zip(candidates, scores):
        cand["score"] = float(score)

    candidates = sorted(candidates, key=lambda c: c["score"], reverse=True)[:top_k]

    output = []
    for rank, cand in enumerate(candidates, start=1):
        output.append({
            "drug_id": str(cand["drug_id"]),
            "rank": rank,
            "score": round(float(cand["score"]), 6),
            "score_type": "ranking_score",
            "has_molecular_structure": int(cand.get("has_molecular_structure", 0))
        })

    return {
        "disease_id": disease_id,
        "model_version": MODEL_VERSION,
        "candidate_count": len(output),
        "candidates": output,
        "disclaimer": (
            "These are research hypotheses generated from biomedical "
            "data. Scores are ranking scores, not probabilities of "
            "clinical efficacy or treatment recommendations. "
            "Candidates require independent evidence validation."
        )
    }


def predict_for_drug(drug_id, top_k=10):
    candidates = query_candidates_for_drug(drug_id)
    provenance = "precomputed_feature_store"

    if not candidates:
        # Dynamically generate 39-feature vectors from real biological and molecular data
        dynamic_cands, limitation_reason = generate_dynamic_features_for_drug(drug_id)
        if dynamic_cands:
            candidates = dynamic_cands
            provenance = "dynamic_feature_generation"
        else:
            return {
                "drug_id": drug_id,
                "model_version": MODEL_VERSION,
                "candidate_count": 0,
                "candidates": [],
                "message": (
                    limitation_reason or
                    f"No unlabeled candidate pairs or valid dynamic features were available for drug '{drug_id}'."
                )
            }

    candidates = add_molecular_features(candidates)

    missing = [
        feature
        for feature in FEATURES
        if feature not in candidates[0]
    ]

    if missing:
        raise RuntimeError(
            "Missing model features: " + ", ".join(missing)
        )

    X_rows = []
    for cand in candidates:
        row_vals = []
        for feat in FEATURES:
            val = cand.get(feat, 0.0)
            if val is None or np.isnan(val) or np.isinf(val):
                val = 0.0
            row_vals.append(float(val))
        X_rows.append(row_vals)

    X = np.array(X_rows, dtype=np.float32)

    scores = model.predict_proba(X)[:, 1]

    for cand, score in zip(candidates, scores):
        cand["score"] = float(score)

    candidates = sorted(candidates, key=lambda c: c["score"], reverse=True)[:top_k]

    output = []
    for rank, cand in enumerate(candidates, start=1):
        output.append({
            "drug_id": str(cand["drug_id"]),
            "disease_id": str(cand["disease_id"]),
            "rank": rank,
            "score": round(float(cand["score"]), 6),
            "score_type": "ranking_score",
            "has_molecular_structure": int(cand.get("has_molecular_structure", 0)),
            "provenance": cand.get("provenance", provenance)
        })

    return {
        "drug_id": drug_id,
        "model_version": MODEL_VERSION,
        "candidate_count": len(output),
        "candidates": output,
        "disclaimer": (
            "These are research hypotheses generated from biomedical "
            "data. Scores are ranking scores, not probabilities of "
            "clinical efficacy or treatment recommendations. "
            "Candidates require independent evidence validation."
        )
    }


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        disease_id = sys.argv[1]
        top_k = int(sys.argv[2]) if len(sys.argv) >= 3 else 10
    else:
        disease_id = "MONDO_0004989"
        top_k = 10

    result = predict(disease_id, top_k)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )
