from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.models import PatientMedicineGuide, PatientMedication, User
from ..schemas.schemas import MedicineGuideOut, LaymanStudyExplanationRequest, LaymanStudyExplanationOut, RegimenAnalysisOut
from ..services.auth_service import get_client_ip, patient_explain_rate_limiter
from ..services.safety_service import MultiDrugSafetyService
from ..dependencies.auth import get_current_active_user


class PatientMedicationCreate(BaseModel):
    drug_name: str = Field(..., min_length=1, max_length=255)
    dosage: Optional[str] = "As prescribed"
    frequency: Optional[str] = "Daily"
    time_of_day: Optional[str] = "Morning (8:00 AM)"
    notes: Optional[str] = None

router = APIRouter(prefix="/patient", tags=["Patient Portal — Plain Language Health Education"])

@router.get("/medicines", response_model=List[MedicineGuideOut])
def get_patient_medicines(
    search: Optional[str] = Query(None, max_length=100),
    db: Session = Depends(get_db)
):
    query = db.query(PatientMedicineGuide)
    if search:
        query = query.filter(PatientMedicineGuide.drug_name.ilike(f"%{search}%"))
    return query.all()

@router.get("/medicines/{drug_name}", response_model=MedicineGuideOut)
def get_single_medicine(
    drug_name: str,
    db: Session = Depends(get_db)
):
    guide = db.query(PatientMedicineGuide).filter(
        PatientMedicineGuide.drug_name.ilike(f"%{drug_name}%")
    ).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Plain language guide for this medicine is not found in database.")
    return guide

@router.post("/explain-research", response_model=LaymanStudyExplanationOut)
def explain_study_in_plain_language(
    req: LaymanStudyExplanationRequest,
    request: Request
):
    """
    Translates complex biomedical scientific research abstracts into safe,
    accessible, clear plain-language summaries for patients and families.
    """
    client_ip = get_client_ip(request)
    patient_explain_rate_limiter.check_rate_limit(f"{client_ip}:patient_explain")
    title_lower = req.study_title.lower()
    abstract_lower = req.abstract_text.lower()
    
    # Detect model type
    if "phase 3" in title_lower or "phase 3" in abstract_lower or "randomized" in abstract_lower:
        study_model = "Human Clinical Trial (Phase 3 or Randomized)"
    elif "phase 1" in title_lower or "phase 2" in title_lower:
        study_model = "Human Clinical Trial (Early Phase 1/2)"
    elif "mice" in abstract_lower or "mouse" in abstract_lower or "in vivo" in abstract_lower or "animal" in abstract_lower:
        study_model = "Animal Laboratory Study (Rodent / In Vivo)"
    else:
        study_model = "Laboratory Cell Culture Study (In Vitro)"

    investigated = f"Researchers studied whether this medication could influence key cellular processes related to the condition in '{req.study_title}'."
    findings = (
        "The scientific study observed measurable biochemical changes or improvements in primary test measurements. "
        "However, results in laboratory settings or early-stage trials do not guarantee that the medicine is effective or safe for general use in everyday patients."
    )
    limitations = (
        f"This was an {study_model}. It cannot prove that the medicine will work safely for other health conditions. "
        "Side effects, dosage differences, and interactions with other medicines require dedicated clinical evaluation."
    )
    unresolved = (
        "Long-term health outcomes, ideal dosages, and whether the treatment helps diverse patient populations remain unknown."
    )
    disclaimer = (
        "DO NOT start, stop, or change any medication based on research reports or AI summaries. "
        "Always talk directly with your doctor or healthcare professional."
    )

    return LaymanStudyExplanationOut(
        investigated=investigated,
        findings=findings,
        study_model=study_model,
        limitations=limitations,
        unresolved_questions=unresolved,
        disclaimer=disclaimer
    )

@router.get("/overview")
def get_patient_overview(db: Session = Depends(get_db)):
    guides_count = db.query(PatientMedicineGuide).count()
    return {
        "available_guides": guides_count,
        "educational_topics": [
            {"id": 1, "title": "Understanding What 'Drug Repurposing' Really Means", "read_time": "3 min"},
            {"id": 2, "title": "Why Laboratory Studies Are Different from Human Clinical Trials", "read_time": "4 min"},
            {"id": 3, "title": "How to Ask Your Healthcare Team About New Research Findings", "read_time": "3 min"}
        ],
        "safe_health_notice": "CureNova Patient Portal provides plain-language educational material. No speculative research candidate is presented as a medical recommendation."
    }

@router.get("/regimen")
def get_patient_regimen(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieves authenticated patient's persistent medication regimen."""
    meds = db.query(PatientMedication).filter(PatientMedication.user_id == current_user.id).order_by(PatientMedication.created_at.asc()).all()
    return [
        {
            "id": m.id,
            "drug_name": m.drug_name,
            "dosage": m.dosage,
            "frequency": m.frequency,
            "time_of_day": m.time_of_day,
            "taken": m.taken,
            "notes": m.notes,
            "created_at": m.created_at.isoformat() if hasattr(m.created_at, "isoformat") else str(m.created_at)
        }
        for m in meds
    ]

@router.post("/regimen")
def add_patient_medication(
    med: PatientMedicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Adds a medication to authenticated patient's persistent regimen."""
    clean_name = med.drug_name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Drug name cannot be empty.")
    
    existing = db.query(PatientMedication).filter(
        PatientMedication.user_id == current_user.id,
        PatientMedication.drug_name.ilike(clean_name)
    ).first()
    if existing:
        return {
            "id": existing.id,
            "drug_name": existing.drug_name,
            "dosage": existing.dosage,
            "frequency": existing.frequency,
            "time_of_day": existing.time_of_day,
            "taken": existing.taken,
            "message": "Medication already present in regimen."
        }
    
    new_med = PatientMedication(
        user_id=current_user.id,
        drug_name=clean_name,
        dosage=med.dosage or "As prescribed",
        frequency=med.frequency or "Daily",
        time_of_day=med.time_of_day or "Morning (8:00 AM)",
        taken=False,
        notes=med.notes
    )
    db.add(new_med)
    db.commit()
    db.refresh(new_med)
    return {
        "id": new_med.id,
        "drug_name": new_med.drug_name,
        "dosage": new_med.dosage,
        "frequency": new_med.frequency,
        "time_of_day": new_med.time_of_day,
        "taken": new_med.taken,
        "message": "Medication added to persistent regimen."
    }

@router.delete("/regimen/{med_id}")
def remove_patient_medication(
    med_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Removes a medication from authenticated patient's persistent regimen."""
    med = db.query(PatientMedication).filter(
        PatientMedication.id == med_id,
        PatientMedication.user_id == current_user.id
    ).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found in regimen.")
    db.delete(med)
    db.commit()
    return {"status": "success", "message": "Medication removed."}

@router.post("/regimen/{med_id}/toggle")
def toggle_patient_dose(
    med_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Toggles daily dose taken status."""
    med = db.query(PatientMedication).filter(
        PatientMedication.id == med_id,
        PatientMedication.user_id == current_user.id
    ).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found in regimen.")
    med.taken = not med.taken
    db.commit()
    db.refresh(med)
    return {"id": med.id, "drug_name": med.drug_name, "taken": med.taken}

@router.post("/regimen/safety-check", response_model=RegimenAnalysisOut)
def check_patient_regimen_safety(
    medications: Optional[List[str]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Evaluates authenticated patient's active medication regimen for dangerous
    polypharmacy interactions and contraindications.
    If no explicit list is provided, automatically evaluates the user's stored medications.
    """
    if medications and len(medications) > 0:
        eval_list = medications
    else:
        user_meds = db.query(PatientMedication).filter(
            PatientMedication.user_id == current_user.id
        ).all()
        eval_list = [m.drug_name for m in user_meds]

    return MultiDrugSafetyService.analyze_regimen(
        db=db,
        medications=eval_list,
        patient_context={"patient_id": current_user.id, "patient_name": current_user.full_name}
    )


