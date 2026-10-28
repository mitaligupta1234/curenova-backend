"""
CureNova Machine Learning Backend Service
Acts as the bridge between CureNova Agentic Orchestrator and the ML Inference Engine.
Wraps ml.predictor, manages candidate conversion, entity resolution, and evidence formatting.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from ..models.models import CandidatePrediction, Drug, Disease

logger = logging.getLogger("curenova.ml_service")

# Import the integrated ML inference adapter
try:
    from ml.predictor import (
        predict_and_enrich as _ml_predict_and_enrich,
        predict_candidates as _ml_predict_raw,
        predict_and_enrich_for_drug as _ml_predict_and_enrich_for_drug,
        predict_candidates_for_drug as _ml_predict_raw_drug,
        enrich_candidate as _ml_enrich_candidate,
        get_model_info as _ml_get_model_info,
        run_stress_test as _ml_run_stress_test,
        MODEL_VERSION,
    )
    ML_AVAILABLE = True
except Exception as exc:
    logger.warning("CureNova ML package could not be initialized: %s", str(exc))
    ML_AVAILABLE = False
    MODEL_VERSION = "cure-nova-xgb-final"


class MLService:
    """
    Production ML Service for Drug Repurposing Inference.
    Coordinates XGBoost candidate prediction, Open Targets & ChEMBL evidence enrichment,
    independent robustness stress-testing, and database entity linking.
    """

    @classmethod
    def is_available(cls) -> bool:
        """Returns True if the ML runtime dependencies and model are ready."""
        return ML_AVAILABLE

    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        """Returns production ML model metadata and held-out validation benchmarks."""
        if not ML_AVAILABLE:
            return {
                "status": "unavailable",
                "model_version": MODEL_VERSION,
                "model_name": "CureNova XGBoost Final",
                "score_type": "ranking_score",
                "clinical_use": False
            }
        return _ml_get_model_info()

    @classmethod
    def generate_repurposing_candidates(
        cls,
        db: Session,
        disease_id: str,
        disease_name: str,
        top_k: int = 10
    ) -> Optional[List[CandidatePrediction]]:
        """
        Executes end-to-end ML inference for a normalized disease identifier.

        Args:
            db: Database session for entity resolution
            disease_id: Normalized ontology ID (e.g. 'MONDO_0004989')
            disease_name: Human-readable disease display name
            top_k: Number of ranked candidate hypotheses (1 to 50)

        Returns:
            List of CandidatePrediction instances if successful, or None on failure.
        """
        if not ML_AVAILABLE:
            logger.warning("ML inference skipped: ML runtime is not available.")
            return None

        if not disease_id:
            logger.warning("ML inference skipped: disease_id is empty or unnormalized.")
            return None

        try:
            logger.info("Executing CureNova XGBoost inference for %s (%s), top_k=%d", disease_id, disease_name, top_k)
            raw_result = _ml_predict_and_enrich(disease_id=disease_id, top_k=top_k)

            raw_candidates = raw_result.get("candidates", [])
            if not raw_candidates:
                logger.info("ML inference returned 0 candidate pairs for disease %s.", disease_id)
                return None

            # Resolve Disease in database if present
            db_disease = db.query(Disease).filter(
                (Disease.name.ilike(f"%{disease_name}%")) | (Disease.mesh_id == disease_id)
            ).first()
            resolved_disease_id = db_disease.id if db_disease else None

            candidate_predictions: List[CandidatePrediction] = []

            for cand_data in raw_candidates:
                chembl_id = cand_data.get("drug_id", "")
                drug_name = cand_data.get("drug_name") or chembl_id
                rank = int(cand_data.get("rank", 1))
                score = round(float(cand_data.get("score", 0.0)), 6)

                # Resolve Drug in database if present
                db_drug = db.query(Drug).filter(
                    (Drug.chembl_id == chembl_id) | (Drug.name.ilike(drug_name))
                ).first()
                resolved_drug_id = db_drug.id if db_drug else None

                # Extract Open Targets evidence
                ev_refs = cand_data.get("evidence_refs") or {}
                clinical_stage = ev_refs.get("maximum_clinical_stage") or "Preclinical / Investigational"
                mechanisms = ev_refs.get("mechanisms") or []
                mech_strs = [
                    f"{m.get('mechanism', '')} ({m.get('action_type', '')} -> {m.get('target_name', '')})"
                    for m in mechanisms if m.get("mechanism")
                ]
                biological_mechanism = "; ".join(mech_strs) if mech_strs else "Modulation of disease target signaling pathway"

                # Extract ChEMBL evidence
                chembl = cand_data.get("chembl_evidence") or {}
                strong_target_count = chembl.get("strong_target_count", 0)
                max_pchembl = chembl.get("max_pchembl")
                usable_activity_count = chembl.get("usable_activity_count", 0)

                # Extract Stress Test results
                stress = cand_data.get("stress_test") or {}
                stress_score = cand_data.get("stress_score") or stress.get("overall_score", 0.0)
                stress_interp = cand_data.get("stress_interpretation") or stress.get("interpretation", "RESEARCH HYPOTHESIS")
                stress_flags = stress.get("flags") or []

                # Synthesize concise, factual rationale
                rationale_parts = []
                if mechanisms:
                    rationale_parts.append(f"Target mechanism: {mechanisms[0].get('mechanism')}.")
                if strong_target_count > 0 and max_pchembl is not None:
                    rationale_parts.append(f"ChEMBL confirms strong affinity against {strong_target_count} target(s) (max pChEMBL {max_pchembl:.2f}).")
                elif chembl.get("available"):
                    rationale_parts.append(f"ChEMBL bioactivity recorded across {usable_activity_count} assays.")
                rationale_parts.append(f"Heuristic Robustness: {stress_score:.1f}/100 ({stress_interp}).")
                rationale = " ".join(rationale_parts)

                evidence_count = len(mechanisms) + (1 if chembl.get("available") else 0)

                # Construct CandidatePrediction instance
                # Do NOT fabricate confidence intervals, probabilities, or uncertainty metrics
                cand = CandidatePrediction(
                    id=resolved_drug_id or (1000 + rank),
                    project_id=1,
                    drug_id=resolved_drug_id,
                    drug_name=drug_name,
                    chembl_id=chembl_id,
                    disease_id=resolved_disease_id,
                    disease_name=disease_name,
                    model_name="CureNova XGBoost Final",
                    model_version=MODEL_VERSION,
                    prediction_score=score,
                    confidence_interval_low=score,  # Point ranking estimate (no fabricated interval)
                    confidence_interval_high=score, # Point ranking estimate (no fabricated interval)
                    calibration_status="Uncalibrated ranking score (Held-out AP: 0.9047, ROC-AUC: 0.9735)",
                    epistemic_uncertainty=None,     # Uncalibrated / unfabricated
                    aleatoric_uncertainty=None,     # Uncalibrated / unfabricated
                    rank=rank,
                    rationale=rationale,
                    biological_mechanism=biological_mechanism,
                    status="Hypothesis",
                    approval_status=clinical_stage,
                    evidence_count=evidence_count,
                    is_bookmarked=False,
                    last_updated=datetime.now(timezone.utc)
                )

                # Attach rich runtime payloads as dynamic attributes for orchestrator
                cand.stress_test = stress
                cand.stress_score = stress_score
                cand.stress_interpretation = stress_interp
                cand.stress_flags = stress_flags
                cand.evidence_refs = ev_refs
                cand.chembl_evidence = chembl
                cand.score_type = "ranking_score"

                candidate_predictions.append(cand)

            logger.info("Successfully generated %d ML candidate predictions for %s", len(candidate_predictions), disease_name)
            return candidate_predictions

        except Exception as exc:
            logger.error("ML candidate generation failed for %s (%s): %s", disease_id, disease_name, str(exc), exc_info=True)
            return None

    @classmethod
    def generate_repurposing_candidates_for_drug(
        cls,
        db: Session,
        drug_id: str,
        drug_name: str,
        top_k: int = 10
    ) -> Optional[List[CandidatePrediction]]:
        """
        Executes end-to-end ML inference for a normalized drug identifier across candidate disease indications.

        Args:
            db: Database session for entity resolution
            drug_id: Normalized ChEMBL ID (e.g. 'CHEMBL1908360')
            drug_name: Human-readable drug display name
            top_k: Number of ranked candidate hypotheses (1 to 50)

        Returns:
            List of CandidatePrediction instances if successful, or None on failure.
        """
        if not ML_AVAILABLE:
            logger.warning("ML inference skipped: ML runtime is not available.")
            return None

        if not drug_id:
            logger.warning("ML inference skipped: drug_id is empty or unnormalized.")
            return None

        try:
            logger.info("Executing CureNova XGBoost inference for drug %s (%s), top_k=%d", drug_id, drug_name, top_k)
            raw_result = _ml_predict_and_enrich_for_drug(drug_id=drug_id, top_k=top_k)

            raw_candidates = raw_result.get("candidates", [])
            if not raw_candidates:
                logger.info("ML inference returned 0 candidate pairs for drug %s.", drug_id)
                return None

            # Resolve Drug in database if present
            db_drug = db.query(Drug).filter(
                (Drug.chembl_id == drug_id) | (Drug.name.ilike(drug_name))
            ).first()
            resolved_drug_id = db_drug.id if db_drug else None

            # Disease canonical name mapping
            MONDO_NAMES = {
                "MONDO_0004989": "Breast Carcinoma",
                "MONDO_0005149": "Pulmonary Arterial Hypertension",
                "MONDO_0005575": "Colorectal Cancer",
                "MONDO_0018827": "Acute Myeloid Leukemia",
                "MONDO_0100096": "Severe COVID-19 Acute Respiratory Distress",
                "MONDO_0004975": "Alzheimer's Disease & Neurodegeneration",
                "MONDO_0005180": "Parkinson's Disease",
                "MONDO_0018177": "Glioblastoma Multiforme",
                "MONDO_0021040": "Pancreatic Neoplasm",
            }

            candidate_predictions: List[CandidatePrediction] = []

            for cand_data in raw_candidates:
                target_disease_id = cand_data.get("disease_id", "")
                disease_display_name = MONDO_NAMES.get(target_disease_id, target_disease_id)

                db_disease = db.query(Disease).filter(
                    (Disease.mesh_id == target_disease_id) | (Disease.name.ilike(f"%{disease_display_name}%"))
                ).first()
                resolved_disease_id = db_disease.id if db_disease else None
                if db_disease:
                    disease_display_name = db_disease.name

                rank = int(cand_data.get("rank", 1))
                score = round(float(cand_data.get("score", 0.0)), 6)

                # Extract Open Targets evidence
                ev_refs = cand_data.get("evidence_refs") or {}
                clinical_stage = ev_refs.get("maximum_clinical_stage") or "Preclinical / Investigational"
                mechanisms = ev_refs.get("mechanisms") or []
                mech_strs = [
                    f"{m.get('mechanism', '')} ({m.get('action_type', '')} -> {m.get('target_name', '')})"
                    for m in mechanisms if m.get("mechanism")
                ]
                biological_mechanism = "; ".join(mech_strs) if mech_strs else "Modulation of disease target signaling pathway"

                # Extract ChEMBL evidence
                chembl = cand_data.get("chembl_evidence") or {}
                strong_target_count = chembl.get("strong_target_count", 0)
                max_pchembl = chembl.get("max_pchembl")
                usable_activity_count = chembl.get("usable_activity_count", 0)

                # Extract Stress Test results
                stress = cand_data.get("stress_test") or {}
                stress_score = cand_data.get("stress_score") or stress.get("overall_score", 0.0)
                stress_interp = cand_data.get("stress_interpretation") or stress.get("interpretation", "RESEARCH HYPOTHESIS")
                stress_flags = stress.get("flags") or []

                rationale_parts = []
                if mechanisms:
                    rationale_parts.append(f"Target mechanism: {mechanisms[0].get('mechanism')}.")
                if strong_target_count > 0 and max_pchembl is not None:
                    rationale_parts.append(f"ChEMBL confirms strong affinity against {strong_target_count} target(s) (max pChEMBL {max_pchembl:.2f}).")
                elif chembl.get("available"):
                    rationale_parts.append(f"ChEMBL bioactivity recorded across {usable_activity_count} assays.")
                rationale_parts.append(f"Heuristic Robustness: {stress_score:.1f}/100 ({stress_interp}).")
                rationale = " ".join(rationale_parts)

                evidence_count = len(mechanisms) + (1 if chembl.get("available") else 0)

                cand = CandidatePrediction(
                    id=resolved_disease_id or (2000 + rank),
                    project_id=1,
                    drug_id=resolved_drug_id,
                    drug_name=drug_name,
                    chembl_id=drug_id,
                    disease_id=resolved_disease_id,
                    disease_name=disease_display_name,
                    model_name="CureNova XGBoost Final",
                    model_version=MODEL_VERSION,
                    prediction_score=score,
                    confidence_interval_low=score,
                    confidence_interval_high=score,
                    calibration_status="Uncalibrated ranking score (Held-out AP: 0.9047, ROC-AUC: 0.9735)",
                    epistemic_uncertainty=None,
                    aleatoric_uncertainty=None,
                    rank=rank,
                    rationale=rationale,
                    biological_mechanism=biological_mechanism,
                    status="Hypothesis",
                    approval_status=clinical_stage,
                    evidence_count=evidence_count,
                    is_bookmarked=False,
                    last_updated=datetime.now(timezone.utc)
                )

                cand.stress_test = stress
                cand.stress_score = stress_score
                cand.stress_interpretation = stress_interp
                cand.stress_flags = stress_flags
                cand.evidence_refs = ev_refs
                cand.chembl_evidence = chembl
                cand.score_type = "ranking_score"
                cand.provenance = cand_data.get("provenance", "ml_inference")

                candidate_predictions.append(cand)

            logger.info("Successfully generated %d ML candidate predictions for drug %s", len(candidate_predictions), drug_name)
            return candidate_predictions

        except Exception as exc:
            logger.error("ML candidate generation failed for drug %s (%s): %s", drug_id, drug_name, str(exc), exc_info=True)
            return None

    @classmethod
    def extract_evidence_facts(
        cls,
        candidate: CandidatePrediction
    ) -> List[Dict[str, Any]]:
        """
        Transforms genuine Open Targets mechanisms and ChEMBL pharmacological data
        into structured evidence facts for LiteratureScout, TargetMechanist, and Synthesizer.

        CRITICAL: Never fabricates PMIDs, DOIs, authors, or publication metadata for database records.
        """
        facts: List[Dict[str, Any]] = []
        fact_counter = 9000

        ev_refs = getattr(candidate, "evidence_refs", None) or {}
        chembl = getattr(candidate, "chembl_evidence", None) or {}
        chembl_id = candidate.chembl_id or ""
        drug_name = candidate.drug_name

        # 1. Open Targets Mechanism of Action Facts
        mechanisms = ev_refs.get("mechanisms") or []
        clinical_stage = ev_refs.get("maximum_clinical_stage", "Preclinical")
        for m in mechanisms:
            fact_counter += 1
            mech_name = m.get("mechanism") or "Biological Mechanism"
            action_type = m.get("action_type") or "Modulator"
            target_name = m.get("target_name") or "Biological Target"

            facts.append({
                "id": fact_counter,
                "title": f"Open Targets: {mech_name}",
                "pmid": None,
                "doi": None,
                "authors": "Open Targets Consortium",
                "journal": "Open Targets Platform 26.09",
                "year": 2026,
                "study_type": "Curated Mechanism of Action",
                "evidence_direction": "supporting",
                "excerpt": f"{drug_name} acts as {action_type} against target {target_name}. Curated clinical stage: {clinical_stage}.",
                "sample_size": None,
                "provenance_url": f"https://platform.opentargets.org/drug/{chembl_id}",
                "is_retrieved_fact": True,
                "evidence_category": "mechanism"
            })

        # 2. ChEMBL Pharmacology Activity Facts
        targets = chembl.get("targets") or []
        for t in targets:
            if not t.get("strong_activity"):
                continue
            fact_counter += 1
            t_name = t.get("target_name") or t.get("target_chembl_id", "Target")
            t_id = t.get("target_chembl_id", "")
            max_pchembl = t.get("max_pchembl", 0.0)
            median_pchembl = t.get("median_pchembl", 0.0)
            assays = t.get("activity_count", 1)

            facts.append({
                "id": fact_counter,
                "title": f"ChEMBL Pharmacology: {t_name}",
                "pmid": None,
                "doi": None,
                "authors": "EMBL-EBI ChEMBL Database",
                "journal": "ChEMBL_37 Bioactivity Dataset",
                "year": 2026,
                "study_type": "In Vitro Pharmacological Assay",
                "evidence_direction": "supporting",
                "excerpt": f"Strong binding activity against {t_name} [{t_id}]: max pChEMBL = {max_pchembl:.2f}, median pChEMBL = {median_pchembl:.2f} across {assays} independent bioactivity assay records.",
                "sample_size": f"{assays} bioassays",
                "provenance_url": f"https://www.ebi.ac.uk/chembl/target_report_card/{t_id}/" if t_id else None,
                "is_retrieved_fact": True,
                "evidence_category": "pharmacology"
            })

        # If no strong target was found but ChEMBL records exist
        if not facts and chembl.get("available"):
            fact_counter += 1
            facts.append({
                "id": fact_counter,
                "title": f"ChEMBL Target Activity Summary: {drug_name}",
                "pmid": None,
                "doi": None,
                "authors": "EMBL-EBI ChEMBL Database",
                "journal": "ChEMBL_37 Bioactivity Dataset",
                "year": 2026,
                "study_type": "Pharmacological Assay",
                "evidence_direction": "inconclusive",
                "excerpt": f"ChEMBL records available for {chembl.get('target_count', 0)} targets, but none achieved high-potency threshold (max pChEMBL = {chembl.get('max_pchembl') or 'N/A'}).",
                "sample_size": None,
                "provenance_url": f"https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}/",
                "is_retrieved_fact": True,
                "evidence_category": "pharmacology"
            })

        return facts
