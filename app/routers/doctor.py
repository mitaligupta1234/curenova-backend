from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.models import DrugInteraction, ClinicalTrialRecord, Drug, User
from ..schemas.schemas import DDIAlert, ClinicalTrialOut, RegimenAnalysisRequest, RegimenAnalysisOut
from ..services.biomedical_adapters import BiomedicalAdapter
from ..services.safety_service import MultiDrugSafetyService
from ..dependencies.auth import require_doctor
from ..services.auth_service import get_client_ip, outbound_rate_limiter


router = APIRouter(prefix="/doctor", tags=["Doctor Portal — Clinical Evidence & Safety"])

@router.get("/interactions", response_model=List[DDIAlert])
def check_interactions(
    drug_names: Optional[str] = Query(None, max_length=500, description="Comma-separated list of drug names to check"),
    severity: Optional[str] = Query(None, max_length=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    query = db.query(DrugInteraction)
    if severity:
        query = query.filter(DrugInteraction.severity == severity)
        
    if drug_names:
        names = [n.strip().lower() for n in drug_names.split(",") if n.strip()]
        if names:
            # Match where any of the provided drugs is drug_a or drug_b
            results = []
            all_ddis = query.all()
            for d in all_ddis:
                if any(n in d.drug_a_name.lower() or n in d.drug_b_name.lower() for n in names):
                    results.append(d)
            return [
                DDIAlert(
                    id=d.id,
                    drug_a=d.drug_a_name,
                    drug_b=d.drug_b_name,
                    severity=d.severity,
                    mechanism=d.mechanism,
                    recommendation=d.recommendation,
                    verified_source=d.verified_source,
                    source_url=d.source_url
                ) for d in results
            ]
            
    all_ddis = query.all()
    return [
        DDIAlert(
            id=d.id,
            drug_a=d.drug_a_name,
            drug_b=d.drug_b_name,
            severity=d.severity,
            mechanism=d.mechanism,
            recommendation=d.recommendation,
            verified_source=d.verified_source,
            source_url=d.source_url
        ) for d in all_ddis
    ]

@router.get("/clinical-trials", response_model=List[ClinicalTrialOut])
def get_clinical_trials(
    condition: Optional[str] = Query(None, max_length=150),
    phase: Optional[str] = Query(None, max_length=50),
    status: Optional[str] = Query(None, max_length=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    query = db.query(ClinicalTrialRecord)
    if condition:
        query = query.filter(ClinicalTrialRecord.condition.ilike(f"%{condition}%"))
    if phase:
        query = query.filter(ClinicalTrialRecord.phase.ilike(f"%{phase}%"))
    if status:
        query = query.filter(ClinicalTrialRecord.status.ilike(f"%{status}%"))
    return query.all()

@router.get("/clinical-trials/live")
async def fetch_live_clinical_trials(
    request: Request,
    condition: str = Query(..., min_length=2, max_length=150, description="Condition or disease name"),
    drug: Optional[str] = Query(None, max_length=100),
    current_user: User = Depends(require_doctor)
):
    """Fetches live human clinical trial records from ClinicalTrials.gov REST API v2."""
    client_ip = get_client_ip(request)
    outbound_rate_limiter.check_rate_limit(f"{client_ip}:trials")
    trials = await BiomedicalAdapter.search_clinical_trials(condition=condition, drug=drug, max_results=5)
    return {
        "condition": condition,
        "drug": drug,
        "count": len(trials),
        "results": trials
    }

@router.get("/adverse-events")
async def get_adverse_events(
    request: Request,
    drug: str = Query(..., min_length=2, max_length=100, description="Drug name to query OpenFDA for adverse events"),
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(require_doctor)
):
    """
    Fetches real post-marketing adverse events from OpenFDA FAERS database.
    Note: OpenFDA records represent spontaneous post-marketing reports and do NOT confirm causality.
    """
    client_ip = get_client_ip(request)
    outbound_rate_limiter.check_rate_limit(f"{client_ip}:openfda")
    events = await BiomedicalAdapter.search_openfda_events(drug_name=drug, limit=limit)
    return {
        "drug": drug,
        "count": len(events),
        "results": events,
        "disclaimer": (
            "OpenFDA post-marketing adverse event reports represent spontaneous submissions. "
            "They do NOT establish causal drug relationships or incidence rates."
        )
    }

@router.post("/safety/analyze-regimen", response_model=RegimenAnalysisOut)
def analyze_medication_regimen(
    req: RegimenAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Exhaustively audits an arbitrary patient medication regimen for combinatorial
    drug-drug interactions, contraindications, and unmonitored drug pairs.
    """
    return MultiDrugSafetyService.analyze_regimen(
        db=db,
        medications=req.medications,
        patient_context=req.patient_context
    )

@router.get("/overview")
def get_clinical_overview(db: Session = Depends(get_db)):
    trial_count = db.query(ClinicalTrialRecord).count()
    ddi_count = db.query(DrugInteraction).count()
    drugs_count = db.query(Drug).count()
    
    return {
        "verified_medications": drugs_count,
        "monitored_ddi_signals": ddi_count,
        "registered_human_trials": trial_count,
        "last_monograph_update": "2026-10-22",
        "regulatory_boundary_notice": (
            "CLINICAL SAFETY NOTICE: The Doctor Portal provides curated pharmacovigilance data, verified monographs, "
            "and human clinical trial endpoints. Experimental computational repurposing hypotheses are strictly segregated "
            "and must NOT be utilized as autonomous prescribing directives."
        )
    }

