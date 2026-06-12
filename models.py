"""
Enhanced data models with confidence routing, staleness tracking, and FMEA support
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal, List, Dict, Any
from enum import Enum


class TicketCategory(str, Enum):
    BILLING = "billing"
    PASSWORD_RESET = "password_reset"
    PLAN_CHANGE = "plan_change"
    OTHER = "other"


class FeedbackType(str, Enum):
    ACCEPTED = "accepted"
    EDITED = "edited"
    REJECTED = "rejected"


class ConfidenceLevel(str, Enum):
    HIGH = "high"         # > 0.8, auto-route to customer
    MEDIUM = "medium"     # 0.6-0.8, review recommended
    LOW = "low"          # < 0.6, escalate or require human review


class ResponseQuality(str, Enum):
    EXCELLENT = "excellent"    # RAGAS score > 0.85
    GOOD = "good"              # 0.70-0.85
    ACCEPTABLE = "acceptable"  # 0.55-0.70
    POOR = "poor"              # < 0.55


class SupportTicket(BaseModel):
    ticket_id: str
    customer_id: str
    subject: str
    description: str
    created_at: datetime
    category: Optional[TicketCategory] = None
    tone: Optional[str] = None  # e.g., "frustrated", "neutral", "happy"


class ClassificationResult(BaseModel):
    ticket_id: str
    category: TicketCategory
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    classifier_version: str = "1.0"
    classification_timestamp: datetime


class RAGRetrievalResult(BaseModel):
    source_id: str  # knowledge base article ID
    source_title: str
    source_content: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    chunk_index: Optional[int] = None


class ProposedResponse(BaseModel):
    ticket_id: str
    proposed_response: str
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    generated_at: datetime
    
    # Prompt engineering details
    tone: Optional[str] = None
    template_used: Optional[str] = None
    
    # RAG context
    retrieved_sources: List[RAGRetrievalResult] = []
    
    # Quality metrics
    ragas_score: Optional[float] = None  # 0-1, retrieval-augmented quality
    quality_level: Optional[ResponseQuality] = None
    
    # Staleness tracking
    knowledge_base_version: str = "1.0"
    response_model_version: str = "1.0"


class ResponseQualityMetrics(BaseModel):
    ticket_id: str
    proposed_response: str
    
    # RAGAS metrics
    faithfulness: float = Field(ge=0.0, le=1.0)  # Does it match retrieved context?
    answer_relevance: float = Field(ge=0.0, le=1.0)  # Is it relevant to the question?
    context_precision: float = Field(ge=0.0, le=1.0)  # How precise is the retrieved context?
    context_recall: float = Field(ge=0.0, le=1.0)  # Did we retrieve all needed context?
    
    # Overall quality score (weighted average)
    overall_score: float = Field(ge=0.0, le=1.0)
    quality_level: ResponseQuality
    
    evaluation_timestamp: datetime


class FMEAEntry(BaseModel):
    """Failure Mode and Effects Analysis - track high-confidence failures"""
    ticket_id: str
    failure_mode: str  # "high_confidence_wrong_response", "misclassification", etc.
    confidence_at_time: float
    agent_feedback: FeedbackType  # What the agent actually did
    severity: Literal["critical", "high", "medium", "low"]
    root_cause: Optional[str] = None
    mitigation: Optional[str] = None
    detected_at: datetime


class ModelStalenessTracker(BaseModel):
    """Track model/response staleness over time"""
    component: str  # "classifier", "response_generator", "knowledge_base"
    version: str
    last_updated: datetime
    total_tickets_seen: int = 0
    accuracy_over_time: List[Dict[str, Any]] = []  # [{timestamp, accuracy}, ...]
    drift_detected: bool = False
    drift_severity: Optional[Literal["none", "minor", "moderate", "severe"]] = None


class TrustArchitectureConfig(BaseModel):
    """Tunable confidence routing configuration"""
    high_confidence_threshold: float = Field(default=0.80, ge=0.0, le=1.0)
    medium_confidence_threshold: float = Field(default=0.60, ge=0.0, le=1.0)
    
    # HITL routing decisions
    auto_send_high_confidence: bool = True
    require_review_medium: bool = True
    escalate_low_confidence: bool = True
    
    # Quality gate
    min_quality_score_for_send: float = Field(default=0.70, ge=0.0, le=1.0)
    
    # Staleness gates
    max_model_age_days: int = 30
    max_knowledge_base_age_days: int = 14
    
    last_modified: datetime


class AgentFeedback(BaseModel):
    ticket_id: str
    feedback_type: FeedbackType
    proposed_response: str
    final_response: Optional[str] = None  # agent's edit if applicable
    agent_id: str
    feedback_at: datetime
    notes: Optional[str] = None
    
    # Quality feedback
    quality_assessment: Optional[ResponseQuality] = None
    
    # Tone assessment
    tone_match: Optional[bool] = None  # Did the tone match customer sentiment?


class TicketWithProposal(BaseModel):
    ticket: SupportTicket
    classification: Optional[ClassificationResult] = None
    proposed_response: ProposedResponse
    quality_metrics: Optional[ResponseQualityMetrics] = None
    fmea_flags: List[FMEAEntry] = []
    feedback: Optional[AgentFeedback] = None
    confidence_routing_decision: Optional[str] = None  # "auto_send", "review", "escalate"
