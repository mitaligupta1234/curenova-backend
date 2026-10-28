import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

def utc_now() -> datetime:
    """Returns the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="researcher")  # researcher, doctor, patient, admin
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    approval_status = Column(String(50), default="approved")  # approved, pending, rejected
    created_at = Column(DateTime, default=utc_now)

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)  # SHA-256 of raw refresh token
    jti = Column(String(100), unique=True, index=True, nullable=False)
    family_id = Column(String(100), index=True, nullable=False)
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="refresh_tokens")


class ResearchProject(Base):
    __tablename__ = "research_projects"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    disease_focus = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active")  # active, archived, completed
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

class Drug(Base):
    __tablename__ = "drugs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    chembl_id = Column(String(50), index=True, nullable=True)
    pubchem_cid = Column(String(50), nullable=True)
    formula = Column(String(100), nullable=True)
    molecular_weight = Column(Float, nullable=True)
    approval_status = Column(String(100), default="Approved")  # Approved, Investigational, Withdrawn
    description = Column(Text, nullable=True)
    targets_json = Column(Text, default="[]")  # List of target symbols
    indications_json = Column(Text, default="[]")  # List of established indications

class Disease(Base):
    __tablename__ = "diseases"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    mesh_id = Column(String(50), index=True, nullable=True)
    icd10 = Column(String(50), nullable=True)
    category = Column(String(100), default="General")
    description = Column(Text, nullable=True)
    associated_genes_json = Column(Text, default="[]")

class Target(Base):
    __tablename__ = "targets"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    gene_id = Column(String(50), nullable=True)
    uniprot_id = Column(String(50), nullable=True)
    target_type = Column(String(100), default="Kinase")

class CandidatePrediction(Base):
    __tablename__ = "candidate_predictions"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("research_projects.id"), nullable=True)
    drug_id = Column(Integer, ForeignKey("drugs.id"), nullable=True)
    drug_name = Column(String(255), index=True, nullable=False)
    chembl_id = Column(String(50), nullable=True)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=True)
    disease_name = Column(String(255), index=True, nullable=False)

    # Model prediction details
    model_name = Column(String(100), default="CureNova GraphEnsemble v2.4")
    model_version = Column(String(50), default="2.4.0")
    prediction_score = Column(Float, nullable=False)  # 0.0 - 1.0 (raw model score)
    confidence_interval_low = Column(Float, nullable=False)
    confidence_interval_high = Column(Float, nullable=False)
    calibration_status = Column(String(100), default="Platt-Calibrated (Brier Score: 0.12)")
    epistemic_uncertainty = Column(Float, default=0.15)  # Knowledge gap uncertainty
    aleatoric_uncertainty = Column(Float, default=0.10)  # Biological noise
    rank = Column(Integer, nullable=False)
    rationale = Column(Text, nullable=True)
    biological_mechanism = Column(Text, nullable=True)

    status = Column(String(50), default="Hypothesis")  # Hypothesis, Validated, Disproven, In-Review
    approval_status = Column(String(100), default="Approved (Other Indication)")
    evidence_count = Column(Integer, default=0)
    is_bookmarked = Column(Boolean, default=False)
    last_updated = Column(DateTime, default=utc_now)

    evidence_records = relationship("EvidenceRecord", back_populates="candidate", cascade="all, delete-orphan")
    notes = relationship("ResearchNote", back_populates="candidate", cascade="all, delete-orphan")

class EvidenceRecord(Base):
    __tablename__ = "evidence_records"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_predictions.id"), nullable=False)
    title = Column(String(500), nullable=False)
    pmid = Column(String(50), nullable=True, index=True)
    doi = Column(String(100), nullable=True)
    authors = Column(String(255), nullable=True)
    journal = Column(String(255), nullable=True)
    year = Column(Integer, nullable=True)
    study_type = Column(String(100), default="In Vitro")  # In Vitro, In Vivo Animal, Clinical Trial Phase 1/2/3, Observational, Systematic Review
    evidence_direction = Column(String(50), default="supporting")  # supporting, contradictory, inconclusive
    excerpt = Column(Text, nullable=False)
    sample_size = Column(String(100), nullable=True)
    provenance_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    candidate = relationship("CandidatePrediction", back_populates="evidence_records")

class ResearchNote(Base):
    __tablename__ = "research_notes"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_predictions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    candidate = relationship("CandidatePrediction", back_populates="notes")

class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(100), unique=True, index=True, nullable=False)
    label = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # drug, disease, gene, protein, pathway, publication, trial
    metadata_json = Column(Text, default="{}")

class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String(100), index=True, nullable=False)
    target_id = Column(String(100), index=True, nullable=False)
    relationship_type = Column(String(100), nullable=False)  # inhibits, activates, treats, associated_with, targets, participant_in, validates
    is_inferred = Column(Boolean, default=False)
    confidence = Column(Float, default=1.0)
    source_provenance = Column(String(255), default="ChEMBL 33")
    pmid = Column(String(50), nullable=True)

class StressTestRun(Base):
    __tablename__ = "stress_test_runs"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=True)
    title = Column(String(255), nullable=False)
    model_name = Column(String(100), nullable=False)
    dataset_version = Column(String(50), default="CureNova-BioKG v2.1")
    split_type = Column(String(100), default="Target-Held-Out (5-Fold)")  # Target-Held-Out, Disease-Held-Out, Temporal-Cutoff, Random-Link-Drop
    temporal_cutoff_year = Column(Integer, nullable=True)  # e.g. 2020
    perturbation_rate = Column(Float, default=0.20)  # e.g. 0.20 for 20% edge removal
    status = Column(String(50), default="completed")  # running, completed, failed

    # JSON-encoded metrics and evaluations
    metrics_json = Column(Text, default="{}")  # auroc, auprc, recall_k, precision_k, brier_score, kendall_tau
    failure_analysis_json = Column(Text, default="[]")  # list of collapsed candidates
    rank_stability_json = Column(Text, default="{}")  # top-10 turnover, rank correlation
    logs_json = Column(Text, default="[]")  # execution steps and logs
    created_at = Column(DateTime, default=utc_now)

class DrugInteraction(Base):
    __tablename__ = "drug_interactions"
    id = Column(Integer, primary_key=True, index=True)
    drug_a_name = Column(String(255), index=True, nullable=False)
    drug_b_name = Column(String(255), index=True, nullable=False)
    severity = Column(String(50), nullable=False)  # contraindicated, major, moderate, minor
    mechanism = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    verified_source = Column(String(255), default="OpenFDA & DrugBank Monograph")
    source_url = Column(String(500), nullable=True)

class ClinicalTrialRecord(Base):
    __tablename__ = "clinical_trials"
    id = Column(Integer, primary_key=True, index=True)
    nct_id = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    phase = Column(String(50), nullable=False)  # Phase 1, Phase 2, Phase 3, Phase 4
    status = Column(String(100), nullable=False)  # Completed, Recruiting, Active, Terminated
    condition = Column(String(255), nullable=False)
    interventions = Column(String(255), nullable=False)
    primary_endpoints = Column(Text, nullable=True)
    source_url = Column(String(500), nullable=True)

class PatientMedicineGuide(Base):
    __tablename__ = "patient_medicine_guides"
    id = Column(Integer, primary_key=True, index=True)
    drug_name = Column(String(255), unique=True, index=True, nullable=False)
    common_uses_plain = Column(Text, nullable=False)
    safety_warnings_plain = Column(Text, nullable=False)
    food_interactions = Column(Text, nullable=True)
    what_to_ask_doctor = Column(Text, nullable=False)
    synthetic_disclaimer = Column(String(255), default="For educational demonstration only. Consult your licensed healthcare provider.")

class ResearchFeedback(Base):
    __tablename__ = "research_feedback"
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(100), nullable=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_predictions.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_role = Column(String(50), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 to 5
    feedback_category = Column(String(50), nullable=False)  # hallucination, mechanism_accuracy, safety_omission, citation_validity, general
    comment = Column(Text, nullable=True)
    prompt_version = Column(String(50), default="v2.5.0")
    model_name = Column(String(100), default="deterministic")
    provenance_mode = Column(String(50), default="deterministic_fallback")  # llm, deterministic_fallback
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User")
    candidate = relationship("CandidatePrediction")

class InvestigationRun(Base):
    __tablename__ = "investigation_runs"
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(100), unique=True, index=True, nullable=False)
    query = Column(String(255), index=True, nullable=False)
    entity_resolved_name = Column(String(255), nullable=False)
    entity_type = Column(String(50), default="Disease")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_role = Column(String(50), default="researcher")
    provenance_mode = Column(String(50), default="deterministic_fallback")
    candidate_count = Column(Integer, default=0)
    top_candidate_name = Column(String(255), nullable=True)
    top_candidate_score = Column(Float, nullable=True)
    results_json = Column(Text, nullable=False)  # JSON payload of AgentWorkflowResponse
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User")

class PatientMedication(Base):
    __tablename__ = "patient_medications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    drug_name = Column(String(255), nullable=False)
    dosage = Column(String(100), default="As prescribed")
    frequency = Column(String(100), default="Daily")
    time_of_day = Column(String(50), default="Morning (8:00 AM)")
    taken = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User")

