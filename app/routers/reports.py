import json
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import CandidatePrediction, EvidenceRecord, StressTestRun, User, InvestigationRun
from ..dependencies.auth import get_current_active_user

router = APIRouter(prefix="/reports", tags=["Research Dossier Reports"])

@router.get("/candidate/{candidate_id}/markdown")
def download_candidate_report_markdown(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    candidate = db.query(CandidatePrediction).filter(CandidatePrediction.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    evidence_records = db.query(EvidenceRecord).filter(EvidenceRecord.candidate_id == candidate_id).all()
    
    pred_str = f"{candidate.prediction_score:.4f}" if candidate.prediction_score is not None else "N/A"
    ci_low_str = f"{candidate.confidence_interval_low:.4f}" if candidate.confidence_interval_low is not None else "N/A"
    ci_high_str = f"{candidate.confidence_interval_high:.4f}" if candidate.confidence_interval_high is not None else "N/A"
    epistemic_str = f"{candidate.epistemic_uncertainty:.2f}" if candidate.epistemic_uncertainty is not None else "None / Uncalibrated"
    aleatoric_str = f"{candidate.aleatoric_uncertainty:.2f}" if candidate.aleatoric_uncertainty is not None else "None / Uncalibrated"

    md_content = f"""# CURENOVA 2.0 — DRUG REPURPOSING RESEARCH DOSSIER
**Date**: {candidate.last_updated.strftime("%Y-%m-%d %H:%M:%S UTC") if hasattr(candidate.last_updated, "strftime") else str(candidate.last_updated)}  
**Document Classification**: Preclinical Computational Research Hypothesis  
**System**: CureNova 2.0 Intelligence Platform  

---

## 1. EXECUTIVE SUMMARY & TARGET CANDIDATE
- **Drug Candidate**: {candidate.drug_name} ({candidate.chembl_id or "ChEMBL Pending"})
- **Target Disease**: {candidate.disease_name}
- **Current Regulatory Status**: {candidate.approval_status}
- **Computational Rank**: #{candidate.rank}
- **Computational Score**: {pred_str} (Score Type: {candidate.score_type or 'ranking_score'})
- **Confidence Bounds**: [{ci_low_str}, {ci_high_str}]
- **Calibration Method**: {candidate.calibration_status}
- **Epistemic Uncertainty (Data Gaps)**: {epistemic_str}
- **Aleatoric Uncertainty (Biological Variance)**: {aleatoric_str}

---

## 2. BIOLOGICAL MECHANISM OF ACTION
{candidate.biological_mechanism or "Detailed mechanistic pathway under curation."}

### Rationale
{candidate.rationale}

---

## 3. EVIDENCE RECORD AUDIT ({len(evidence_records)} Retrieved Records)
"""
    supporting = [e for e in evidence_records if e.evidence_direction == "supporting"]
    contradictory = [e for e in evidence_records if e.evidence_direction == "contradictory"]
    inconclusive = [e for e in evidence_records if e.evidence_direction == "inconclusive"]

    md_content += f"\n### A. Supporting Findings ({len(supporting)})\n"
    for s in supporting:
        md_content += f"- **{s.title}** ({s.journal}, {s.year}) [{s.study_type}]\n  *Excerpt*: \"{s.excerpt}\"\n  *PMID*: {s.pmid or 'N/A'} | *Sample*: {s.sample_size or 'N/A'}\n\n"

    md_content += f"\n### B. Contradictory & Adverse Signals ({len(contradictory)})\n"
    for c in contradictory:
        md_content += f"- **{c.title}** ({c.journal}, {c.year}) [{c.study_type}]\n  *Excerpt*: \"{c.excerpt}\"\n  *PMID*: {c.pmid or 'N/A'} | *Sample*: {c.sample_size or 'N/A'}\n\n"

    md_content += f"\n### C. Inconclusive or Equivocal Data ({len(inconclusive)})\n"
    for i in inconclusive:
        md_content += f"- **{i.title}** ({i.journal}, {i.year}) [{i.study_type}]\n  *Excerpt*: \"{i.excerpt}\"\n  *PMID*: {i.pmid or 'N/A'}\n\n"

    md_content += """
---

## 4. COMPUTATIONAL REPRODUCIBILITY & STRESS-TEST SUMMARY
Computational predictions from the CureNova GraphEnsemble model must be audited across the Stress-Test Lab:
- Generalization splits ensure findings are not artifacts of high node degrees in publication networks.
- Perturbation dropout measures whether candidate ranking survives biological link degradation.
- Temporal cutoff prevents retrospective leakage of post-study trial registries.

---

## 5. MANDATORY SCIENTIFIC DISCLAIMER
*This dossier is an automated scientific intelligence synthesis produced by CureNova 2.0. 
Computational prediction scores represent likelihood of biomedical association and DO NOT establish clinical efficacy, 
safety, tolerability, or prescribing suitability. Independent laboratory validation and formal clinical trials are required.*
"""
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=curenova_dossier_{candidate.drug_name.lower()}_{candidate_id}.md"}
    )


@router.get("/investigation/{workflow_id}/markdown")
def download_investigation_report_markdown(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Downloads complete multi-stage investigation research dossier.
    Enforces authorization: only owner or administrator may download.
    """
    run = db.query(InvestigationRun).filter(InvestigationRun.workflow_id == workflow_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Investigation run not found")
        
    if current_user.role != "admin" and run.user_id is not None and run.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have permission to download this investigation dossier."
        )

    candidates = db.query(CandidatePrediction).filter(
        CandidatePrediction.investigation_id == run.id
    ).order_by(CandidatePrediction.rank.asc()).all()

    payload = {}
    try:
        payload = json.loads(run.results_json)
    except Exception:
        pass

    synthesis_report = payload.get("synthesis_report", "")
    limitations = payload.get("limitations_and_boundary_warning", "")
    trans = payload.get("transcriptomic_connectivity") or {}
    trials = payload.get("clinical_trial_challenge") or {}

    date_str = run.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if hasattr(run.created_at, "strftime") else str(run.created_at)

    md_content = f"""# CURENOVA 2.0 — MULTI-STAGE INVESTIGATION DOSSIER
**Workflow ID**: `{run.workflow_id}`  
**Investigated Query**: {run.query} ({run.entity_resolved_name}) [{run.entity_type}]  
**Search Direction**: {run.search_type or 'drug_to_disease'}  
**Execution Status**: {run.status} ({run.execution_duration_ms or 0} ms)  
**Model Provenance**: {run.model_version} ({run.provenance_mode})  
**Date**: {date_str}  
**Document Classification**: Preclinical Computational Research Hypothesis  

---

## 1. EXECUTIVE SYNTHESIS REPORT
{synthesis_report or f"Completed investigation protocol for '{run.entity_resolved_name}'. Generated {len(candidates)} ranked candidates."}

---

## 2. RANKED REPURPOSING CANDIDATE HYPOTHESES ({len(candidates)} Candidates)
"""
    for c in candidates:
        mol_feats = ""
        if c.molecular_features_json:
            try:
                m_dict = json.loads(c.molecular_features_json)
                mol_feats = f"  *Molecular Descriptors*: MW: {m_dict.get('molecular_weight', 'N/A')} | LogP: {m_dict.get('logp', 'N/A')} | TPSA: {m_dict.get('tpsa', 'N/A')} | HBD: {m_dict.get('hbd', 'N/A')} | HBA: {m_dict.get('hba', 'N/A')}\n"
            except Exception:
                pass

        ev_records = db.query(EvidenceRecord).filter(EvidenceRecord.candidate_id == c.id).all()
        md_content += f"""
### Rank #{c.rank}: {c.drug_name} &rarr; {c.disease_name}
- **Computational Score**: {c.prediction_score:.4f} ({c.score_type})
- **Provenance Engine**: {c.provenance} ({c.model_name})
- **Regulatory Status**: {c.approval_status}
- **Target Mechanism**: {c.biological_mechanism or "Target modulation"}
- **Rationale**: {c.rationale or "Evaluated across biomedical graph."}
{mol_feats}- **Evidence Records Validated**: {len(ev_records)}
"""
        for ev in ev_records:
            md_content += f"  - *[{ev.evidence_direction.upper()}]* **{ev.title}** ({ev.journal}, {ev.year or 'N/A'}): \"{ev.excerpt}\" (PMID: {ev.pmid or 'N/A'})\n"

    md_content += f"""
---

## 3. MULTI-OMICS TRANSCRIPTOMIC CONNECTIVITY (LINCS L1000)
- **Status**: {trans.get('status', 'unavailable')}
- **Connectivity Score (tau)**: {trans.get('connectivity_score', 'N/A')} ({trans.get('directionality', 'N/A')})
- **Interpretation**: {trans.get('interpretation', 'No transcriptomic signature matched.')}

---

## 4. ADVERSARIAL CLINICAL-TRIAL AUDIT (ClinicalTrials.gov)
- **Challenge Level**: {trials.get('overall_challenge_level', 'NOT_EVALUATED')}
- **Summary**: {trials.get('summary', 'No past clinical trial termination signals.')}
- **Evaluated Trials**: {len(trials.get('evaluated_trials', []))} records audited.

---

## 5. MANDATORY SCIENTIFIC DISCLAIMER & DATA LIMITATIONS
{limitations or "Computational predictions represent preclinical research hypotheses and do not imply clinical safety, efficacy, or treatment suitability."}
"""

    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=curenova_investigation_{run.workflow_id}.md"}
    )
