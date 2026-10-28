"""
CureNova ML Production Inference Adapter
Model: cure_nova_xgb_final.joblib
Model Version: cure-nova-xgb-final
Features: 39 biomedical and molecular features

This module provides a unified in-process interface for:
1. Loading the XGBoost production model and feature definitions
2. Querying disease candidate drug pairs
3. Scoring candidates using the trained XGBoost model
4. Enriching candidates with Open Targets biological evidence
5. Enriching candidates with ChEMBL pharmacological activity evidence
6. Executing the independent robustness stress test engine
"""

from pathlib import Path
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("curenova.ml.predictor")

ML_DIR = Path(__file__).resolve().parent
MODEL_PATH = ML_DIR / "models" / "cure_nova_xgb_final.joblib"
METADATA_PATH = ML_DIR / "models" / "cure_nova_xgb_final.json"
CHEMBL_FILE = ML_DIR / "data" / "chembl" / "chembl_drug_evidence.json"

MODEL_VERSION = "cure-nova-xgb-final"

# Import runtime components
try:
    from .predict_v4 import predict as _raw_predict, predict_for_drug as _raw_predict_drug
    from .evidence_utils import (
        get_drug_evidence,
        get_chembl_live_evidence,
        get_combined_drug_evidence,
    )
    from .stress_test import run_stress_test
except ImportError:
    # Allow running directly as standalone script
    from predict_v4 import predict as _raw_predict, predict_for_drug as _raw_predict_drug
    from evidence_utils import (
        get_drug_evidence,
        get_chembl_live_evidence,
        get_combined_drug_evidence,
    )
    from stress_test import run_stress_test


def get_model_info() -> Dict[str, Any]:
    """Returns production model metadata and validation metrics."""
    metadata = {}
    if METADATA_PATH.exists():
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as e:
            logger.warning("Could not read metadata JSON: %s", e)

    return {
        "model_version": MODEL_VERSION,
        "model_type": "XGBoost",
        "feature_count": len(metadata.get("features", [])) or 39,
        "features": metadata.get("features", []),
        "unseen_disease_holdout": {
            "average_precision": 0.9047,
            "roc_auc": 0.9735,
        },
        "unseen_drug_holdout": {
            "average_precision": 0.8652,
            "roc_auc": 0.9580,
        },
        "score_type": "ranking_score",
        "clinical_use": False,
        "evaluation_note": (
            "Metrics are Average Precision and ROC-AUC on held-out entities. "
            "Scores are ranking scores, not calibrated clinical probabilities."
        ),
        "disclaimer": (
            "These are research hypotheses generated from biomedical data. "
            "Scores are ranking scores, not probabilities of clinical efficacy "
            "or treatment recommendations. Candidates require independent validation."
        ),
    }


def enrich_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enriches a candidate drug with:
    1. Open Targets biological evidence (mechanisms of action, targets, clinical stage)
    2. ChEMBL bioactivity evidence (pChEMBL, assays, strong targets)
    3. CureNova Stress Test robustness analysis
    """
    drug_id = candidate.get("drug_id", "")

    # 1. Open Targets evidence
    ot_evidence = get_drug_evidence(drug_id)
    candidate["evidence_refs"] = ot_evidence
    if not candidate.get("drug_name") and ot_evidence.get("drug_name"):
        candidate["drug_name"] = ot_evidence.get("drug_name")

    # 2. ChEMBL pharmacological activity evidence
    chembl = get_chembl_live_evidence(drug_id)
    candidate["chembl_evidence"] = {
        "available": chembl.get("available", False),
        "source": chembl.get("source", "ChEMBL"),
        "source_release": chembl.get("source_release"),
        "drug_name": chembl.get("drug_name"),
        "activity_record_count": chembl.get("activity_record_count", 0),
        "usable_activity_count": chembl.get("usable_activity_count", 0),
        "target_count": chembl.get("target_count", 0),
        "strong_target_count": chembl.get("strong_target_count", 0),
        "max_pchembl": chembl.get("max_pchembl"),
        "targets": chembl.get("targets", [])[:10],
        "note": chembl.get("note"),
    }

    # 3. Independent stress test
    stress = run_stress_test(candidate)
    candidate["stress_test"] = stress
    candidate["stress_score"] = stress.get("overall_score", 0.0)
    candidate["stress_interpretation"] = stress.get("interpretation", "")

    return candidate


def predict_candidates(disease_id: str, top_k: int = 10) -> Dict[str, Any]:
    """
    Queries candidate pairs for a disease and ranks them using the production XGBoost model.
    """
    return _raw_predict(disease_id=disease_id, top_k=top_k)


def predict_and_enrich(disease_id: str, top_k: int = 10) -> Dict[str, Any]:
    """
    End-to-end ML pipeline:
    1. XGBoost candidate ranking
    2. Open Targets evidence retrieval
    3. ChEMBL evidence retrieval
    4. Robustness stress test
    """
    result = predict_candidates(disease_id=disease_id, top_k=top_k)
    candidates = result.get("candidates", [])

    enriched = []
    for candidate in candidates:
        enriched.append(enrich_candidate(candidate))

    result["candidates"] = enriched
    return result


def predict_candidates_for_drug(drug_id: str, top_k: int = 10) -> Dict[str, Any]:
    """
    Queries candidate disease pairs for a drug and ranks them using the production XGBoost model.
    """
    return _raw_predict_drug(drug_id=drug_id, top_k=top_k)


def predict_and_enrich_for_drug(drug_id: str, top_k: int = 10) -> Dict[str, Any]:
    """
    End-to-end ML pipeline for drug query:
    1. XGBoost candidate disease ranking
    2. Open Targets evidence retrieval for drug
    3. ChEMBL evidence retrieval for drug
    4. Robustness stress test
    """
    result = predict_candidates_for_drug(drug_id=drug_id, top_k=top_k)
    candidates = result.get("candidates", [])

    enriched = []
    for candidate in candidates:
        enriched.append(enrich_candidate(candidate))

    result["candidates"] = enriched
    return result


class CureNovaMLPredictor:
    """Class wrapper for CureNova ML inference engine."""

    version = MODEL_VERSION

    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        return get_model_info()

    @classmethod
    def predict(cls, disease_id: str, top_k: int = 10, enrich: bool = True) -> Dict[str, Any]:
        if enrich:
            return predict_and_enrich(disease_id=disease_id, top_k=top_k)
        return predict_candidates(disease_id=disease_id, top_k=top_k)

    @classmethod
    def predict_drug(cls, drug_id: str, top_k: int = 10, enrich: bool = True) -> Dict[str, Any]:
        if enrich:
            return predict_and_enrich_for_drug(drug_id=drug_id, top_k=top_k)
        return predict_candidates_for_drug(drug_id=drug_id, top_k=top_k)

    @classmethod
    def stress_test(cls, candidate: Dict[str, Any]) -> Dict[str, Any]:
        return run_stress_test(candidate)


if __name__ == "__main__":
    import sys

    d_id = sys.argv[1] if len(sys.argv) > 1 else "MONDO_0004989"
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    print(f"Running CureNova ML Inference for {d_id} (top {k})...")
    res = predict_and_enrich(d_id, top_k=k)
    print(json.dumps(res, indent=2, ensure_ascii=False))
