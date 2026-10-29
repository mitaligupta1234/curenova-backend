"""
CureNova 2.0 — Adversarial Clinical-Trial Challenge Agent
=========================================================
Audits proposed drug repurposing hypotheses by actively searching for clinical
evidence that challenges, refutes, or bounds the hypothesis.

Scientific Rules & Guardrails:
1. Distinguishes trial status: Completed, Terminated, Withdrawn, Suspended, Active/Recruiting.
2. Evaluates termination reasons (whyStopped): Terminated trials without documented
   inefficacy results are classified as INCONCLUSIVE (e.g. slow enrollment, funding loss),
   NOT automatically failed.
3. Classifies trials as TERMINATED_EFFICACY_FAILURE only when actual results or whyStopped
   explicitly document lack of efficacy, futility, or unacceptable toxicity.
4. Verifies whether the trial actually investigated the specific candidate drug and indication.
5. Distinguishes primary outcomes from secondary outcomes.
6. Does NOT assume the absence of trials implies efficacy or safety.
7. Segregates clinical trial challenge findings from ML model likelihood scores.
"""

import logging
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from ..config import settings
from ..models.models import ClinicalTrialRecord

logger = logging.getLogger("curenova.clinical_trial_challenge")

# Known drug synonym mappings for clinical trial discovery
DRUG_SYNONYMS: Dict[str, List[str]] = {
    "fasudil": ["fasudil", "ha-1077", "eril", "fasudil hydrochloride"],
    "everolimus": ["everolimus", "rad001", "afinitor", "certican"],
    "metformin": ["metformin", "glucophage", "metformin hydrochloride", "fortamet"],
    "niclosamide": ["niclosamide", "yomesan", "niclocide"],
    "imatinib": ["imatinib", "gleevec", "glivec", "sti571"]
}

# Known disease term expansions for clinical trial discovery
DISEASE_EXPANSIONS: Dict[str, List[str]] = {
    "pulmonary arterial hypertension": ["pulmonary arterial hypertension", "pah", "pulmonary hypertension"],
    "colorectal cancer": ["colorectal cancer", "colorectal carcinoma", "colon cancer", "rectal cancer", "colorectal neoplasms"],
    "breast carcinoma": ["breast carcinoma", "breast cancer", "triple negative breast cancer", "breast neoplasms"],
    "glioblastoma": ["glioblastoma", "glioblastoma multiforme", "gbm", "malignant glioma"],
    "pancreatic neoplasm": ["pancreatic neoplasm", "pancreatic cancer", "pancreatic ductal adenocarcinoma"],
    "acute myeloid leukemia": ["acute myeloid leukemia", "aml"]
}


class ClinicalTrialChallengeAgent:
    """
    Adversarial clinical trials agent that identifies counter-evidence,
    terminated studies, and translational hurdles for repurposing hypotheses.
    """

    @classmethod
    def get_aliases_for_drug(cls, drug_name: str) -> List[str]:
        clean = drug_name.strip().lower()
        for k, aliases in DRUG_SYNONYMS.items():
            if clean == k or clean in aliases or any(a in clean for a in aliases):
                return aliases
        return [clean]

    @classmethod
    def get_terms_for_disease(cls, disease_name: str) -> List[str]:
        clean = disease_name.strip().lower()
        for k, terms in DISEASE_EXPANSIONS.items():
            if clean == k or clean in terms or any(t in clean for t in terms):
                return terms
        return [clean]

    @classmethod
    async def fetch_trials_from_api(
        cls,
        drug_name: str,
        disease_name: str,
        max_results: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Queries official ClinicalTrials.gov REST API v2 for trials
        matching the drug and condition terms.
        """
        url = f"{settings.CLINICALTRIALS_BASE_URL}/studies"
        term = f"{drug_name} AND {disease_name}"
        params = {
            "query.term": term,
            "pageSize": max_results,
            "format": "json"
        }
        trials = []
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    for s in data.get("studies", []):
                        protocol = s.get("protocolSection", {})
                        has_results = "resultsSection" in s
                        trials.append(cls._parse_study_protocol(protocol, has_results=has_results))
        except Exception as exc:
            logger.warning("ClinicalTrials.gov v2 API live query failed: %s", str(exc))
        return trials

    @classmethod
    def _parse_study_protocol(cls, protocol: Dict[str, Any], has_results: bool = False) -> Dict[str, Any]:
        """Extracts structured fields from ClinicalTrials.gov study protocol JSON."""
        id_mod = protocol.get("identificationModule", {})
        status_mod = protocol.get("statusModule", {})
        design_mod = protocol.get("designModule", {})
        cond_mod = protocol.get("conditionsModule", {})
        arms_mod = protocol.get("armsInterventionsModule", {})
        outcomes_mod = protocol.get("outcomesModule", {})

        nct_id = id_mod.get("nctId", "NCT-Pending")
        title = id_mod.get("briefTitle", "Clinical Study")
        overall_status = status_mod.get("overallStatus", "UNKNOWN").upper()
        why_stopped = status_mod.get("whyStopped")
        phases = design_mod.get("phases", ["Phase Not Specified"])
        conditions = cond_mod.get("conditions", [])

        # Interventions
        interventions = []
        for item in arms_mod.get("interventions", []):
            name = item.get("name", "")
            itype = item.get("type", "")
            if name:
                interventions.append(f"{itype}: {name}" if itype else name)

        # Primary & Secondary Outcomes
        primary_outcomes = []
        for o in outcomes_mod.get("primaryOutcomes", []):
            measure = o.get("measure", "")
            if measure:
                primary_outcomes.append(measure)

        secondary_outcomes = []
        for o in outcomes_mod.get("secondaryOutcomes", []):
            measure = o.get("measure", "")
            if measure:
                secondary_outcomes.append(measure)

        # Dates
        start_date = status_mod.get("startDateStruct", {}).get("date")
        completion_date = status_mod.get("completionDateStruct", {}).get("date")

        return {
            "nct_id": nct_id,
            "title": title,
            "overall_status": overall_status,
            "why_stopped": why_stopped,
            "phases": phases,
            "conditions": conditions,
            "interventions": interventions,
            "primary_outcomes": primary_outcomes,
            "secondary_outcomes": secondary_outcomes,
            "has_results": has_results,
            "start_date": start_date,
            "completion_date": completion_date,
            "url": f"https://clinicaltrials.gov/study/{nct_id}",
            "source": "ClinicalTrials.gov Live API v2"
        }

    @classmethod
    def query_local_db_trials(
        cls,
        db: Session,
        drug_name: str,
        disease_name: str
    ) -> List[Dict[str, Any]]:
        """Queries local SQLite clinical_trials table for curated historical trial records."""
        try:
            records = db.query(ClinicalTrialRecord).filter(
                (ClinicalTrialRecord.condition.ilike(f"%{disease_name}%")) |
                (ClinicalTrialRecord.interventions.ilike(f"%{drug_name}%"))
            ).all()

            results = []
            for r in records:
                results.append({
                    "nct_id": r.nct_id,
                    "title": r.title,
                    "overall_status": r.status.upper(),
                    "why_stopped": None,
                    "phases": [r.phase],
                    "conditions": [r.condition],
                    "interventions": [r.interventions],
                    "primary_outcomes": [r.primary_endpoints] if r.primary_endpoints else [],
                    "secondary_outcomes": [],
                    "has_results": False,
                    "url": r.source_url or f"https://clinicaltrials.gov/study/{r.nct_id}",
                    "source": "CureNova Curated Clinical Trial Database"
                })
            return results
        except Exception as exc:
            logger.warning("Local clinical trial database query failed: %s", str(exc))
            return []

    @classmethod
    def classify_trial_finding(
        cls,
        trial: Dict[str, Any],
        target_drug: str,
        target_disease: str
    ) -> Dict[str, Any]:
        """
        Adversarially evaluates a single clinical trial record against the repurposing hypothesis.
        Distinguishes inconclusive terminations (e.g. slow accrual) from true efficacy failures.
        """
        status = trial.get("overall_status", "UNKNOWN").upper()
        why_stopped = (trial.get("why_stopped") or "").lower()
        has_results = trial.get("has_results", False)

        # Check relevance: does this trial actually investigate the target drug and disease?
        interventions_text = " ".join(trial.get("interventions", [])).lower()
        conditions_text = " ".join(trial.get("conditions", [])).lower()
        title_text = trial.get("title", "").lower()

        drug_aliases = cls.get_aliases_for_drug(target_drug)
        disease_terms = cls.get_terms_for_disease(target_disease)

        drug_matched = any(alias.lower() in interventions_text or alias.lower() in title_text for alias in drug_aliases)
        disease_matched = any(term.lower() in conditions_text or term.lower() in title_text for term in disease_terms)

        is_direct_investigation = drug_matched and disease_matched

        classification = "INCONCLUSIVE"
        challenge_impact = "NEUTRAL"
        explanation = ""

        if status == "TERMINATED":
            # Check reasons for termination
            efficacy_failure_keywords = [
                "lack of efficacy", "futility", "inefficacy", "unfavorable",
                "toxicity", "adverse event", "safety", "death", "no benefit"
            ]
            operational_keywords = [
                "accrual", "enrollment", "slow", "funding", "business", "sponsor",
                "covid", "logistics", "administrative", "feasibility"
            ]

            if any(k in why_stopped for k in efficacy_failure_keywords):
                classification = "TERMINATED_EFFICACY_FAILURE"
                challenge_impact = "HIGH_CHALLENGE"
                explanation = (
                    f"Trial {trial['nct_id']} was terminated due to documented lack of efficacy or safety concern "
                    f"('{trial.get('why_stopped')}'). This directly challenges therapeutic repurposing in {target_disease}."
                )
            elif any(k in why_stopped for k in operational_keywords):
                classification = "TERMINATED_OPERATIONAL_INCONCLUSIVE"
                challenge_impact = "INCONCLUSIVE"
                explanation = (
                    f"Trial {trial['nct_id']} was terminated due to operational/logistical hurdles ('{trial.get('why_stopped')}'). "
                    "This does NOT demonstrate biological or clinical inefficacy."
                )
            else:
                classification = "TERMINATED_UNSPECIFIED"
                challenge_impact = "INCONCLUSIVE"
                explanation = (
                    f"Trial {trial['nct_id']} was terminated without documented outcome results. "
                    "Inconclusive; absence of reported efficacy cannot be equated with drug failure."
                )

        elif status in ("WITHDRAWN", "SUSPENDED"):
            classification = f"TRIAL_{status}"
            challenge_impact = "INCONCLUSIVE"
            explanation = (
                f"Trial {trial['nct_id']} is {status.lower()} before completion. "
                "Translational feasibility challenge; trial did not generate definitive efficacy data."
            )

        elif status == "COMPLETED":
            if has_results:
                classification = "COMPLETED_WITH_RESULTS"
                challenge_impact = "SUPPORTIVE_OR_EVALUATED"
                explanation = (
                    f"Trial {trial['nct_id']} completed with public outcome endpoints posted in ClinicalTrials.gov. "
                    "Formal primary endpoints require clinical review."
                )
            else:
                classification = "COMPLETED_WITHOUT_POSTED_RESULTS"
                challenge_impact = "INCONCLUSIVE"
                explanation = (
                    f"Trial {trial['nct_id']} completed but has no public outcome results posted. "
                    "Efficacy remains unverified in published registry."
                )

        elif status in ("RECRUITING", "ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION"):
            classification = "ACTIVE_CLINICAL_EVALUATION"
            challenge_impact = "SUPPORTIVE_INVESTIGATIONAL"
            explanation = (
                f"Active ongoing human clinical evaluation ({', '.join(trial.get('phases', ['Phase?']))}). "
                f"Demonstrates active translational interest for {target_drug} in {target_disease}."
            )
        else:
            classification = f"STATUS_{status}"
            challenge_impact = "NEUTRAL"
            explanation = f"Trial {trial['nct_id']} is currently in status '{status}'."

        nct_id = trial.get("nct_id", "NCT_UNKNOWN")
        return {
            "nct_id": nct_id,
            "title": trial.get("title", ""),
            "status": status,
            "phases": trial.get("phases", []),
            "why_stopped": trial.get("why_stopped"),
            "is_direct_investigation": is_direct_investigation,
            "classification": classification,
            "challenge_impact": challenge_impact,
            "explanation": explanation,
            "primary_outcomes": trial.get("primary_outcomes", [])[:3],
            "url": trial.get("url") or (f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else None),
            "source": trial.get("source", "ClinicalTrials.gov")
        }

    @classmethod
    async def audit_hypothesis(
        cls,
        candidate_drug: str,
        proposed_indication: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Executes comprehensive adversarial audit of the drug-indication hypothesis
        against real-world clinical trials.
        """
        retrieval_time = datetime.now(timezone.utc).isoformat()

        # 1. Fetch live trials from ClinicalTrials.gov
        trials_live = await cls.fetch_trials_from_api(candidate_drug, proposed_indication, max_results=6)

        # 2. Query local DB trials if available
        trials_local = cls.query_local_db_trials(db, candidate_drug, proposed_indication) if db else []

        # Merge and deduplicate by NCT ID
        all_trials_map = {}
        for t in trials_live + trials_local:
            nct = t.get("nct_id")
            if nct and nct not in all_trials_map:
                all_trials_map[nct] = t

        evaluated_trials = []
        for t in all_trials_map.values():
            classified = cls.classify_trial_finding(t, candidate_drug, proposed_indication)
            evaluated_trials.append(classified)

        # Partition into direct drug-indication trials vs related disease context trials
        direct_trials = [t for t in evaluated_trials if t.get("is_direct_investigation")]
        indirect_trials = [t for t in evaluated_trials if not t.get("is_direct_investigation")]

        has_efficacy_failure = any(t["classification"] == "TERMINATED_EFFICACY_FAILURE" for t in direct_trials)
        has_active_trials = any(t["challenge_impact"] == "SUPPORTIVE_INVESTIGATIONAL" for t in direct_trials)
        has_completed_trials = any("COMPLETED" in t["classification"] for t in direct_trials)
        has_inconclusive_term = any(t["classification"] == "TERMINATED_OPERATIONAL_INCONCLUSIVE" for t in direct_trials)

        if has_efficacy_failure:
            overall_challenge_level = "HIGH_ADVERSARIAL_CHALLENGE"
            summary = (
                f"ADVERSARIAL WARNING: Identified clinical trial(s) terminated due to documented efficacy failure "
                f"or safety endpoints for {candidate_drug} in {proposed_indication}. Repurposing hypothesis requires critical revision."
            )
        elif has_completed_trials or has_active_trials:
            overall_challenge_level = "SUPPORTIVE_OR_EVALUATED"
            summary = (
                f"Identified {len(direct_trials)} clinical trial(s) directly investigating {candidate_drug} in connection with {proposed_indication}. "
                "No documented termination due to inefficacy detected."
            )
        elif has_inconclusive_term:
            overall_challenge_level = "INCONCLUSIVE_HISTORICAL_EVIDENCE"
            summary = (
                f"Clinical trial directly evaluating {candidate_drug} in {proposed_indication} was previously terminated for operational/enrollment reasons. "
                "Findings are inconclusive and do not refute biological plausibility."
            )
        elif not direct_trials:
            if indirect_trials:
                overall_challenge_level = "UNRESOLVED_NO_DIRECT_TRIALS"
                summary = (
                    f"No registered clinical trials found directly evaluating '{candidate_drug}' for '{proposed_indication}' in ClinicalTrials.gov. "
                    f"Found {len(indirect_trials)} related trial(s) for the condition (e.g., {indirect_trials[0].get('title', 'comparator trial')}). "
                    "Hypothesis remains strictly preclinical."
                )
            else:
                overall_challenge_level = "UNRESOLVED_NO_CLINICAL_TRIALS"
                summary = (
                    f"No registered clinical trials found evaluating '{candidate_drug}' for '{proposed_indication}' in ClinicalTrials.gov. "
                    "Hypothesis remains strictly preclinical."
                )
        else:
            overall_challenge_level = "INCONCLUSIVE"
            summary = f"Evaluated {len(direct_trials)} direct trial records; findings are inconclusive."

        return {
            "candidate_drug": candidate_drug,
            "proposed_indication": proposed_indication,
            "total_trials_evaluated": len(evaluated_trials),
            "overall_challenge_level": overall_challenge_level,
            "summary": summary,
            "evaluated_trials": evaluated_trials,
            "retrieval_timestamp": retrieval_time,
            "provenance": "ClinicalTrials.gov REST API v2 & CureNova Trial Monograph Registry",
            "limitations": (
                "Clinical trial registries index formal human protocols. Lack of registered trials does NOT prove inefficacy, "
                "nor does operational trial termination prove drug failure. Clinical trial outcomes must be corroborated with peer-reviewed literature."
            )
        }
