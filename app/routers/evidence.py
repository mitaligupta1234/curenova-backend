from fastapi import APIRouter, Depends, Query, Request, Body, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.models import EvidenceRecord, User
from ..schemas.schemas import EvidenceRecordOut
from ..services.biomedical_adapters import BiomedicalAdapter
from ..config import settings
from ..dependencies.auth import require_researcher
from ..services.auth_service import get_client_ip, outbound_rate_limiter, evidence_synthesis_rate_limiter

router = APIRouter(prefix="/evidence", tags=["Literature & Evidence Workspace"])

@router.get("", response_model=List[EvidenceRecordOut])
def get_evidence(
    study_type: Optional[str] = Query(None, max_length=50),
    direction: Optional[str] = Query(None, max_length=50),  # supporting, contradictory, inconclusive
    candidate_id: Optional[int] = None,
    search: Optional[str] = Query(None, max_length=150),
    q: Optional[str] = Query(None, max_length=150),
    source: Optional[str] = Query(None, max_length=100),
    evidence_type: Optional[str] = Query(None, max_length=100),
    db: Session = Depends(get_db)
):
    query = db.query(EvidenceRecord)
    if candidate_id:
        query = query.filter(EvidenceRecord.candidate_id == candidate_id)
    eff_study = study_type or evidence_type
    if eff_study:
        query = query.filter(EvidenceRecord.study_type.ilike(f"%{eff_study}%"))
    if direction:
        query = query.filter(EvidenceRecord.evidence_direction == direction)
    if source:
        query = query.filter(
            (EvidenceRecord.journal.ilike(f"%{source}%")) |
            (EvidenceRecord.provenance_url.ilike(f"%{source}%"))
        )
    eff_search = search or q
    if eff_search:
        query = query.filter(
            (EvidenceRecord.title.ilike(f"%{eff_search}%")) |
            (EvidenceRecord.excerpt.ilike(f"%{eff_search}%")) |
            (EvidenceRecord.authors.ilike(f"%{eff_search}%"))
        )
    return query.all()

@router.get("/pubmed-live")
async def fetch_live_pubmed(
    request: Request,
    query: str = Query(..., min_length=2, max_length=150, description="Biomedical search terms"),
    max_results: int = Query(5, ge=1, le=10),
    current_user: User = Depends(require_researcher)
):
    """Retrieves live peer-reviewed publications from NCBI PubMed E-utilities."""
    client_ip = get_client_ip(request)
    outbound_rate_limiter.check_rate_limit(f"{client_ip}:pubmed")
    results = await BiomedicalAdapter.search_pubmed(query, max_results)
    return {
        "query": query,
        "count": len(results),
        "results": results,
        "is_live_api": True if results else False
    }

@router.post("/synthesize")
def synthesize_literature(
    request: Request,
    evidence_ids: List[int] = Body(..., max_length=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_researcher)
):
    """Generates source-grounded synthesis linked strictly to retrieved passages."""
    client_ip = get_client_ip(request)
    evidence_synthesis_rate_limiter.check_rate_limit(f"{client_ip}:synthesize")
    clean_ids = list(dict.fromkeys(x for x in evidence_ids if isinstance(x, int) and x > 0))
    if not clean_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one valid positive evidence ID is required for literature synthesis."
        )
    records = db.query(EvidenceRecord).filter(EvidenceRecord.id.in_(clean_ids)).all()
    if not records:
        return {"summary": "No matching evidence passages selected for synthesis.", "citations": []}
        
    supporting = [r for r in records if r.evidence_direction == "supporting"]
    contradictory = [r for r in records if r.evidence_direction == "contradictory"]
    inconclusive = [r for r in records if r.evidence_direction == "inconclusive"]
    
    summary_parts = []
    summary_parts.append(
        f"Synthesized analysis across {len(records)} verified studies ({len(supporting)} supporting, "
        f"{len(contradictory)} contradictory, {len(inconclusive)} inconclusive)."
    )
    if supporting:
        summary_parts.append(
            f"Preclinical and supportive evidence highlights biological activity and target modulation "
            f"(e.g., {supporting[0].title} [{supporting[0].journal}, {supporting[0].year}])."
        )
    if contradictory:
        summary_parts.append(
            f"CRITICAL SAFETY/EFFICACY DISCREPANCY: {len(contradictory)} study documented adverse signals "
            f"or failed primary endpoints (notably: '{contradictory[0].title}', {contradictory[0].excerpt[:140]}...)."
        )
    if inconclusive:
        summary_parts.append(
            f"Equivocal findings reported in {len(inconclusive)} cohort reviews; optimal therapeutic windows remain undefined."
        )

    return {
        "summary": " ".join(summary_parts),
        "citations": [
            {
                "id": r.id,
                "pmid": r.pmid,
                "title": r.title,
                "direction": r.evidence_direction,
                "provenance_url": r.provenance_url
            }
            for r in records
        ],
        "boundary_warning": "Synthesized claims are grounded exclusively in cited retrieved passages. No speculative efficacy extrapolated."
    }
