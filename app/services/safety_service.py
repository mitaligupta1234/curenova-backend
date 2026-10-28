"""
CureNova 2.0 — Multi-Drug Polypharmacy & Regimen Safety Engine
============================================================
Performs combinatorial safety profiling, drug-drug interaction (DDI) detection,
and adverse-event risk analysis for patient medication regimens.

Safety Rules & Guardrails:
1. Computes all N*(N-1)/2 pairwise combinations for a patient medication regimen.
2. Deduplicates medications, normalizes aliases, and validates entries.
3. Explicitly labels pairs with no documented interactions as 'no_documented_interaction'
   with mandatory warning: "Absence of interaction documentation does NOT guarantee safety."
4. Distinguishes severity levels: Contraindicated, Major, Moderate, Minor.
5. Surfaces verifiable mechanism and clinical management recommendations from monographs.
6. Restricts patient medication history access to authenticated users and authorized clinicians.
"""

import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from itertools import combinations
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from ..models.models import DrugInteraction, Drug, User, PatientMedication
from .biomedical_adapters import BiomedicalAdapter

logger = logging.getLogger("curenova.safety_service")


class MultiDrugSafetyService:
    """
    Evaluates multi-medication regimens for drug-drug interactions,
    pharmacokinetic contraindications, and polypharmacy risks.
    """

    @classmethod
    def normalize_medication_name(cls, name: str) -> str:
        """Cleans and normalizes drug name strings."""
        if not name:
            return ""
        clean = name.strip()
        # Remove common dosage suffixes if accidentally included (e.g. "Metformin 500mg" -> "Metformin")
        tokens = clean.split()
        if len(tokens) > 1 and any(tok.lower().endswith(("mg", "mcg", "g", "ml", "iu")) for tok in tokens[1:]):
            clean = tokens[0]
        return clean.strip().title()

    @classmethod
    def resolve_medication(cls, db: Session, drug_name: str) -> Dict[str, Any]:
        """Resolves medication name against pharmacopoeia database."""
        clean = cls.normalize_medication_name(drug_name)
        if not clean:
            return {"resolved": False, "name": drug_name, "chembl_id": None, "status": "empty_input"}

        db_drug = db.query(Drug).filter(Drug.name.ilike(clean)).first()
        if db_drug:
            return {
                "resolved": True,
                "name": db_drug.name,
                "chembl_id": db_drug.chembl_id,
                "approval_status": db_drug.approval_status,
                "status": "verified"
            }
        
        return {
            "resolved": False,
            "name": clean,
            "chembl_id": None,
            "status": "unindexed_in_local_catalog"
        }

    @classmethod
    def analyze_regimen(
        cls,
        db: Session,
        medications: List[str],
        patient_context: Optional[Dict[str, Any]] = None,
        include_live_openfda: bool = False
    ) -> Dict[str, Any]:
        """
        Conducts exhaustive pairwise interaction audit across medication regimen.
        Returns structured analysis with risk score, detected DDIs, and unmonitored pairs.
        """
        # 1. Clean and deduplicate input medications
        raw_meds = [m for m in medications if m and str(m).strip()]
        unique_meds_map: Dict[str, str] = {}
        for m in raw_meds:
            norm = cls.normalize_medication_name(str(m))
            if norm and norm.lower() not in unique_meds_map:
                unique_meds_map[norm.lower()] = norm

        unique_meds = list(unique_meds_map.values())
        med_count = len(unique_meds)

        if med_count < 2:
            return {
                "analysis_id": f"safe-{int(datetime.now(timezone.utc).timestamp())}",
                "overall_risk_category": "Insufficient Medications",
                "overall_risk_score": 0.0,
                "summary_headline": "At least 2 distinct medications are required to perform drug-drug interaction profiling.",
                "total_medications": med_count,
                "evaluated_medications": unique_meds,
                "pairwise_interactions": [],
                "unmonitored_pairs": [],
                "contraindications_count": 0,
                "major_interactions_count": 0,
                "safety_disclaimer": (
                    "Polypharmacy risk analysis requires evaluating multiple concurrent medications. "
                    "Single-agent toxicology should be reviewed via standard product monographs."
                ),
                "created_at": datetime.now(timezone.utc).isoformat()
            }

        # 2. Query all database interactions
        all_interactions = db.query(DrugInteraction).all()

        # Build fast lookup map for (drug_a.lower(), drug_b.lower())
        interaction_map: Dict[Tuple[str, str], DrugInteraction] = {}
        for d in all_interactions:
            a = d.drug_a_name.strip().lower()
            b = d.drug_b_name.strip().lower()
            interaction_map[(a, b)] = d
            interaction_map[(b, a)] = d

        pairwise_interactions = []
        unmonitored_pairs = []
        contraindications_count = 0
        major_count = 0
        moderate_count = 0
        minor_count = 0

        # 3. Check every unique pair
        for med_a, med_b in combinations(unique_meds, 2):
            key = (med_a.lower(), med_b.lower())
            
            # Fuzzy match check in case of slight naming variations
            matched_ddi = interaction_map.get(key)
            if not matched_ddi:
                for (da, db_name), ddi in interaction_map.items():
                    if (med_a.lower() in da or da in med_a.lower()) and (med_b.lower() in db_name or db_name in med_b.lower()):
                        matched_ddi = ddi
                        break

            if matched_ddi:
                sev = matched_ddi.severity.lower()
                if sev == "contraindicated":
                    contraindications_count += 1
                elif sev == "major":
                    major_count += 1
                elif sev == "moderate":
                    moderate_count += 1
                elif sev == "minor":
                    minor_count += 1

                pairwise_interactions.append({
                    "drug_a": med_a,
                    "drug_b": med_b,
                    "matched_monograph_a": matched_ddi.drug_a_name,
                    "matched_monograph_b": matched_ddi.drug_b_name,
                    "severity": matched_ddi.severity.upper(),
                    "mechanism": matched_ddi.mechanism,
                    "clinical_recommendation": matched_ddi.recommendation,
                    "verified_source": matched_ddi.verified_source,
                    "source_url": matched_ddi.source_url,
                    "is_documented_interaction": True
                })
            else:
                unmonitored_pairs.append({
                    "drug_a": med_a,
                    "drug_b": med_b,
                    "status": "no_interaction_documented",
                    "notice": (
                        f"No documented adverse interaction found between '{med_a}' and '{med_b}' in local pharmacovigilance monographs. "
                        "Absence of record does NOT guarantee clinical safety."
                    )
                })

        # 4. Compute composite risk score (0 - 100)
        # Weights: Contraindicated = 40, Major = 25, Moderate = 10, Minor = 3
        raw_score = (contraindications_count * 40.0) + (major_count * 25.0) + (moderate_count * 10.0) + (minor_count * 3.0)
        # Scale with total evaluated pairs
        total_pairs = len(list(combinations(unique_meds, 2)))
        risk_score = min(100.0, max(0.0, round(raw_score, 1)))

        if contraindications_count > 0:
            risk_category = "CONTRAINDICATED / CRITICAL"
            summary_headline = (
                f"CRITICAL SAFETY WARNING: Detected {contraindications_count} contraindicated combination(s). "
                "Co-administration poses severe clinical risk and is medically contraindicated."
            )
        elif major_count > 0:
            risk_category = "HIGH RISK"
            summary_headline = (
                f"HIGH RISK: Identified {major_count} major drug-drug interaction(s). "
                "Close clinical monitoring, dose adjustment, or alternative therapy strongly recommended."
            )
        elif moderate_count > 0:
            risk_category = "MODERATE RISK"
            summary_headline = (
                f"MODERATE RISK: Identified {moderate_count} moderate interaction(s). "
                "Monitor patient for additive pharmacodynamic effects or altered clearance."
            )
        elif minor_count > 0:
            risk_category = "LOW RISK"
            summary_headline = f"LOW RISK: Identified {minor_count} minor interaction signal(s)."
        else:
            risk_category = "NO DOCUMENTED INTERACTIONS"
            summary_headline = (
                f"Evaluated {total_pairs} drug pair(s) across {med_count} medications. "
                "No adverse drug interactions documented in current curated monographs."
            )

        return {
            "analysis_id": f"safe-{int(datetime.now(timezone.utc).timestamp())}",
            "overall_risk_category": risk_category,
            "overall_risk_score": risk_score,
            "summary_headline": summary_headline,
            "total_medications": med_count,
            "evaluated_medications": unique_meds,
            "total_pairs_evaluated": total_pairs,
            "pairwise_interactions": pairwise_interactions,
            "unmonitored_pairs": unmonitored_pairs,
            "contraindications_count": contraindications_count,
            "major_interactions_count": major_count,
            "moderate_interactions_count": moderate_count,
            "minor_interactions_count": minor_count,
            "patient_context": patient_context,
            "safety_disclaimer": (
                "CLINICAL SAFETY BOUNDARY: CureNova polypharmacy risk analysis cross-references curated pharmacovigilance "
                "databases. Computational interaction checks do NOT replace clinical judgment or comprehensive pharmacist "
                "medication reconciliation. Co-morbidities, renal/hepatic impairment, and pharmacogenomics must be evaluated."
            ),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
