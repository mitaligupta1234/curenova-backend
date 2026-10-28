from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict

# User & Auth
class UserBase(BaseModel):
    email: str
    full_name: str
    role: str = "patient"

class UserSignup(BaseModel):
    email: str
    full_name: str
    password: str = Field(..., min_length=8)
    role: str = "patient"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool = True
    is_verified: bool = False
    approval_status: str = "approved"
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut

class TokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None

class UserApprovalRequest(BaseModel):
    approval_status: Literal["approved", "rejected", "pending"] = "approved"


# Evidence & Candidates
class EvidenceRecordOut(BaseModel):
    id: int
    candidate_id: int
    title: str
    pmid: Optional[str] = None
    doi: Optional[str] = None
    authors: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    study_type: str
    evidence_direction: str  # supporting, contradictory, inconclusive
    excerpt: str
    sample_size: Optional[str] = None
    provenance_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ResearchNoteCreate(BaseModel):
    content: str

class ResearchNoteOut(BaseModel):
    id: int
    candidate_id: int
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CandidateSummaryOut(BaseModel):
    id: int
    drug_name: str
    chembl_id: Optional[str] = None
    disease_name: str
    model_name: str
    model_version: str
    prediction_score: float
    confidence_interval_low: Optional[float] = None
    confidence_interval_high: Optional[float] = None
    calibration_status: str
    epistemic_uncertainty: Optional[float] = None
    aleatoric_uncertainty: Optional[float] = None
    rank: int
    rationale: Optional[str] = None
    status: str
    approval_status: str
    evidence_count: int
    is_bookmarked: bool
    last_updated: datetime
    score_type: Optional[str] = "ranking_score"
    stress_score: Optional[float] = None
    stress_interpretation: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_type: Optional[str] = None
    candidate_label: Optional[str] = None
    ml_score_available: Optional[bool] = True
    biological_mechanism: Optional[str] = None
    provenance: Optional[str] = "precomputed_feature_store"
    model_config = ConfigDict(from_attributes=True)

class CandidateDetailOut(CandidateSummaryOut):
    biological_mechanism: Optional[str] = None
    evidence_records: List[EvidenceRecordOut] = []
    notes: List[ResearchNoteOut] = []
    model_config = ConfigDict(from_attributes=True)

# Stress Testing
class StressTestConfig(BaseModel):
    title: str
    model_name: str = "CureNova GraphEnsemble v2.4"
    dataset_version: str = "CureNova-BioKG v2.1"
    split_type: str = "Target-Held-Out (5-Fold)"  # Target-Held-Out, Temporal-Cutoff, Data-Perturbation
    temporal_cutoff_year: Optional[int] = 2020
    perturbation_rate: float = 0.20  # 20% link removal
    candidate_ids: Optional[List[int]] = None

class StressTestResultOut(BaseModel):
    id: int
    title: str
    model_name: str
    dataset_version: str
    split_type: str
    temporal_cutoff_year: Optional[int]
    perturbation_rate: float
    status: str
    metrics: Dict[str, Any]
    failure_analysis: List[Dict[str, Any]]
    rank_stability: Dict[str, Any]
    logs: List[Dict[str, Any]]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Knowledge Graph
class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # drug, disease, gene, protein, pathway, publication, trial
    metadata: Dict[str, Any] = {}

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship_type: str
    is_inferred: bool = False
    confidence: float = 1.0
    source_provenance: str
    pmid: Optional[str] = None

class KnowledgeGraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

# Doctor Portal
class DDIQuery(BaseModel):
    drug_names: List[str]

class DDIAlert(BaseModel):
    id: int
    drug_a: str
    drug_b: str
    severity: str  # contraindicated, major, moderate, minor
    mechanism: str
    recommendation: str
    verified_source: str
    source_url: Optional[str] = None

class RegimenAnalysisRequest(BaseModel):
    medications: List[str] = Field(..., min_length=1, description="List of medication names to evaluate")
    patient_context: Optional[Dict[str, Any]] = None

class PairwiseInteractionOut(BaseModel):
    drug_a: str
    drug_b: str
    matched_monograph_a: Optional[str] = None
    matched_monograph_b: Optional[str] = None
    severity: str
    mechanism: str
    clinical_recommendation: str
    verified_source: str
    source_url: Optional[str] = None
    is_documented_interaction: bool = True

class RegimenAnalysisOut(BaseModel):
    analysis_id: str
    overall_risk_category: str
    overall_risk_score: float
    summary_headline: str
    total_medications: int
    evaluated_medications: List[str]
    total_pairs_evaluated: int
    pairwise_interactions: List[PairwiseInteractionOut] = []
    unmonitored_pairs: List[Dict[str, Any]] = []
    contraindications_count: int = 0
    major_interactions_count: int = 0
    moderate_interactions_count: int = 0
    minor_interactions_count: int = 0
    patient_context: Optional[Dict[str, Any]] = None
    safety_disclaimer: str
    created_at: str


class ClinicalTrialOut(BaseModel):
    id: int
    nct_id: str
    title: str
    phase: str
    status: str
    condition: str
    interventions: str
    primary_endpoints: Optional[str] = None
    source_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# Patient Portal
class MedicineGuideOut(BaseModel):
    id: int
    drug_name: str
    common_uses_plain: str
    safety_warnings_plain: str
    food_interactions: Optional[str] = None
    what_to_ask_doctor: str
    synthetic_disclaimer: str
    model_config = ConfigDict(from_attributes=True)

class LaymanStudyExplanationRequest(BaseModel):
    study_title: str = Field(..., min_length=2, max_length=300, description="Title of scientific research paper")
    abstract_text: str = Field(..., min_length=10, max_length=10000, description="Abstract text to explain in plain language")

class LaymanStudyExplanationOut(BaseModel):
    investigated: str
    findings: str
    study_model: str  # Laboratory, Animal, Human Trial
    limitations: str
    unresolved_questions: str
    disclaimer: str

# Research Project
class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    disease_focus: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)

class ProjectOut(ProjectCreate):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Agent Workflow Trace
class AgentWorkflowStep(BaseModel):
    step_id: int
    name: str
    agent_role: str
    status: str  # completed, in_progress, flagged
    tool_called: str
    execution_time_ms: int
    provenance: str
    findings_summary: str
    uncertainties_detected: List[str] = []

class StructuredSynthesisOut(BaseModel):
    candidate_drug: str
    target_disease: str
    research_rationale: str
    proposed_mechanism: str
    supporting_evidence_ids: List[int] = []
    conflicting_evidence_ids: List[int] = []
    safety_concerns: List[str] = []
    missing_information: List[str] = []
    evidence_strength: str = "Preliminary Preclinical"
    epistemic_uncertainty: float = 0.15
    validated_citations: List[Dict[str, Any]] = []
    rejected_unsupported_ids: List[int] = []
    research_limitations: str
    non_clinical_disclaimer: str

class AgentWorkflowResponse(BaseModel):
    workflow_id: str
    query_entity: str
    entity_type: str
    search_type: Optional[str] = "drug_to_disease"
    query_type: Optional[str] = "drug"
    queried_entity: Optional[Dict[str, Any]] = None
    completed_steps: List[AgentWorkflowStep]
    candidate_hypotheses: List[CandidateSummaryOut]
    candidates: List[CandidateSummaryOut] = []
    synthesis_report: str
    limitations_and_boundary_warning: str
    provenance_mode: Literal["llm", "deterministic_fallback"] = "deterministic_fallback"
    llm_provider: Optional[str] = "none"
    model_version: Optional[str] = "2.5.0"
    structured_synthesis: Optional[StructuredSynthesisOut] = None
    mechanisms: List[Dict[str, Any]] = []
    safety_findings: List[Dict[str, Any]] = []
    contradictions: List[str] = []
    ml_prediction_metadata: Dict[str, Any] = {}
    transcriptomic_connectivity: Optional[Dict[str, Any]] = None
    clinical_trial_challenge: Optional[Dict[str, Any]] = None


# Research Feedback & Offline Evaluation
class FeedbackCreate(BaseModel):
    workflow_id: Optional[str] = Field(None, max_length=100)
    candidate_id: Optional[int] = None
    rating: int = Field(..., ge=1, le=5, description="1 (Poor/Incorrect) to 5 (Rigorous/Accurate)")
    feedback_category: Literal[
        "hallucination",
        "mechanism_accuracy",
        "safety_omission",
        "citation_validity",
        "general"
    ]
    comment: Optional[str] = Field(None, max_length=2000)
    prompt_version: Optional[str] = Field("v2.5.0", max_length=50)
    model_name: Optional[str] = Field(None, max_length=100)

class FeedbackOut(BaseModel):
    id: int
    workflow_id: Optional[str] = None
    candidate_id: Optional[int] = None
    user_id: int
    user_email: str
    user_role: str
    rating: int
    feedback_category: str
    comment: Optional[str] = None
    prompt_version: str
    model_name: str
    provenance_mode: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class FeedbackEvaluationSummary(BaseModel):
    total_feedback_count: int
    average_rating: float
    category_counts: Dict[str, int]
    hallucination_report_frequency: float
    safety_discrepancy_frequency: float
    prompt_version_breakdown: Dict[str, Any]
    recurring_failure_patterns: List[Dict[str, Any]]
    policy_evaluation_status: str
