## Support Triage Co-pilot - Advanced Architecture

### System Overview

This system is an advanced Support Triage Co-pilot designed to handle 12,000+ tickets/week with intelligent classification, response generation, and human-in-the-loop feedback loops. It implements enterprise-grade patterns for confidence routing, quality assurance, and failure analysis.

### Core Architecture

#### 1. Clean Separation of Concerns

The system is organized into distinct, modular components:

- **models.py** - Enhanced data models with confidence levels and quality tracking
- **ticket_classifier.py** - Rule-based ticket classification with confidence scoring
- **response_generator.py** - RAG-enhanced response generation with tone matching
- **knowledge_base.py** - Vector retrieval system for support knowledge
- **prompt_manager.py** - Tone-matched prompt engineering
- **quality_metrics.py** - RAGAS-inspired response quality evaluation
- **confidence_router.py** - Core HITL pattern with tunable thresholds
- **fmea_tracker.py** - Failure mode analysis for high-confidence errors
- **advanced_routes.py** - Advanced API endpoints for all features
- **api.py** - Main FastAPI application tying everything together

#### 2. Retrieval Augmented Generation (RAG)

**Purpose**: Ground responses in verified knowledge base articles rather than pure generation.

**Implementation** (`knowledge_base.py`):
- Bootstrap sample articles by category (billing, password_reset, plan_change)
- Keyword + TF-IDF matching for retrieval
- Relevance scoring (0-1) based on title/content overlap
- Access tracking to identify popular articles

**Usage Flow**:
1. Customer submits ticket
2. Query: "{subject} {description}"
3. Retrieve top-3 relevant articles by category
4. Include in response generation
5. Track source attribution

**API Endpoints**:
```
GET  /knowledge-base/articles?category=billing
POST /knowledge-base/articles  # Add new articles
GET  /knowledge-base/search?query=billing&top_k=3
GET  /knowledge-base/article/{id}
PUT  /knowledge-base/article/{id}
DELETE /knowledge-base/article/{id}
GET  /knowledge-base/stats
```

#### 3. Prompt Engineering for Tone-Matched Responses

**Purpose**: Tailor responses to customer sentiment and urgency.

**Implementation** (`prompt_manager.py`):
- Tone detection: frustrated, urgent, polite, neutral
- Tone-specific response templates
- System prompts with emotional context
- Confidence boost calculation based on tone

**Tone Detection**:
```python
ToneAnalyzer.detect_tone(description) -> str
# Looks for: frustrated_keywords, urgent_keywords, neutral_keywords
```

**Response Templates**:
```python
# Example: Billing category with frustrated tone
"We sincerely apologize for the billing issue you're experiencing. We're here to help resolve this quickly."

# vs. Urgent tone:
"We understand this needs immediate attention. Let me help you right away."
```

**Confidence Boost**:
- RAG context: +0.1 per article (max 0.3)
- Tone certainty: 0.05 (frustrated/urgent) to 0.15 (neutral)

#### 4. RAGAS: Response Quality Assessment

**Purpose**: Evaluate response quality on multiple dimensions.

**Implementation** (`quality_metrics.py`):
- **Faithfulness**: Does response align with RAG sources? (0-1)
- **Answer Relevance**: Does it answer the question? (0-1)
- **Context Precision**: How precise are retrieved sources? (0-1)
- **Context Recall**: Did we retrieve sufficient context? (0-1)

**Overall Score** (weighted):
```
Score = 0.25*faithfulness + 0.35*answer_relevance + 0.20*context_precision + 0.20*context_recall
```

**Quality Levels**:
- EXCELLENT: >= 0.85
- GOOD: 0.70-0.85
- ACCEPTABLE: 0.55-0.70
- POOR: < 0.55

**API Endpoint**:
```
POST /quality-metrics/evaluate
{
  "response": "Your response text",
  "question": "Customer's question",
  "category": "billing",
  "rag_context": ["article1", "article2"]
}
```

#### 5. Confidence Routing: Core HITL Pattern

**Purpose**: Route responses to automation, review, or escalation based on confidence + quality.

**Implementation** (`confidence_router.py`):
- Confidence mapping: HIGH (>0.8), MEDIUM (0.6-0.8), LOW (<0.6)
- Multi-gate routing logic
- Tunable decision thresholds

**Routing Decisions**:
```
Classification Confidence  Quality Gate  Staleness Gate  -> Decision    Priority
HIGH + Good + Fresh                                       AUTO_SEND     5
HIGH + Poor                                               REVIEW        2
HIGH + Stale                                              REVIEW        2
MEDIUM + Good                                             REVIEW        3
MEDIUM + Good + Override                                  AUTO_SEND     4
LOW                                                       ESCALATE      1
```

**Priority Levels** (1=highest):
1. Escalation (requires human handling immediately)
2. High-confidence anomalies (should be reviewed)
3. Medium confidence (standard review)
4. Auto-send medium confidence (quality override)
5. Auto-send high confidence (fully automated)

#### 6. FMEA: Failure Mode and Effects Analysis

**Purpose**: Track high-confidence failures to identify systemic issues.

**Implementation** (`fmea_tracker.py`):
- Detect: confidence >= 0.75 AND (rejected OR heavily edited)
- Categorize by: failure_mode, severity, confidence
- Track: root_cause, mitigation

**Failure Modes**:
- `high_confidence_wrong_response`: System was confident but wrong
- `misclassification`: Wrong category assigned
- `tone_mismatch`: Response tone didn't match customer
- (extensible)

**Severity Levels**:
- CRITICAL: confidence >= 0.90 with wrong response
- HIGH: confidence >= 0.75 with wrong response
- MEDIUM: confidence 0.6-0.75 with issues
- LOW: minor issues

**Analysis**:
```
GET /fmea/analysis?days=30
Returns: {
  total_failures,
  failure_modes_breakdown,
  severity_distribution,
  high_confidence_failures,
  avg_confidence_of_failures
}

GET /fmea/trends?mode=high_confidence_wrong_response
Returns: Daily failure trends with patterns

GET /fmea/high-risk-tickets?threshold=0.80
Returns: All high-confidence failures for risk analysis
```

#### 7. Trust Architecture: Tunable Configuration

**Purpose**: Centralize HITL policy decisions.

**Configuration** (`models.py` + `confidence_router.py`):
```json
{
  "high_confidence_threshold": 0.80,
  "medium_confidence_threshold": 0.60,
  "auto_send_high_confidence": true,
  "require_review_medium": true,
  "escalate_low_confidence": true,
  "min_quality_score_for_send": 0.70,
  "max_model_age_days": 30,
  "max_knowledge_base_age_days": 14
}
```

**API Endpoints**:
```
GET  /trust-config             # View current configuration
PUT  /trust-config             # Update any parameter

Example:
PUT /trust-config?high_confidence_threshold=0.85&auto_send_high_confidence=false
```

#### 8. Model Staleness Tracking

**Purpose**: Monitor model degradation and knowledge base freshness.

**Tracked Components**:
- `classifier`: Rule-based but versions important
- `response_generator`: Base version + RAG version
- `knowledge_base`: Latest article version

**Staleness Gates** (from trust config):
- If classifier > 30 days old → require review
- If KB > 14 days old → require review
- Automatically flags responses from stale components

#### 9. Feedback Loops: The Headliner

**Purpose**: Continuous learning from agent feedback.

**Feedback Types**:
1. **Accepted**: Response sent as-is (positive signal)
2. **Edited**: Agent improved response (refinement signal)
3. **Rejected**: Response not used (negative signal)

**Learning Pipeline**:
1. Agent provides feedback on response
2. System stores in feedback store with context
3. Quality assessment recorded
4. FMEA analysis if high-confidence failure
5. Future ticket retrieval uses this context
6. Routing thresholds adjusted based on patterns

**Metrics Tracked**:
- Acceptance rate: (accepted + edited) / total feedback
- Pure acceptance: accepted / total feedback
- FMEA severity distribution
- Time-to-resolution with feedback vs without

---

### Data Models

#### ClassificationResult
```python
ticket_id: str
category: TicketCategory
confidence: float (0-1)
confidence_level: ConfidenceLevel  # HIGH, MEDIUM, LOW
classifier_version: str
classification_timestamp: datetime
```

#### ProposedResponse
```python
ticket_id: str
proposed_response: str
confidence: float (0-1)
confidence_level: ConfidenceLevel
generated_at: datetime
tone: str                          # "frustrated", "urgent", etc.
template_used: str                 # Which template was used
retrieved_sources: List[RAGRetrievalResult]  # RAG context
ragas_score: float                 # Quality score 0-1
quality_level: ResponseQuality     # EXCELLENT, GOOD, ACCEPTABLE, POOR
knowledge_base_version: str
response_model_version: str
```

#### ResponseQualityMetrics
```python
ticket_id: str
proposed_response: str
faithfulness: float (0-1)
answer_relevance: float (0-1)
context_precision: float (0-1)
context_recall: float (0-1)
overall_score: float (0-1)
quality_level: ResponseQuality
evaluation_timestamp: datetime
```

#### FMEAEntry
```python
ticket_id: str
failure_mode: str                  # Type of failure
confidence_at_time: float          # Confidence when it occurred
agent_feedback: FeedbackType       # How agent responded
severity: str                      # critical, high, medium, low
root_cause: str                    # Analysis of why it failed
mitigation: str                    # How to prevent next time
detected_at: datetime
```

#### TrustArchitectureConfig
```python
high_confidence_threshold: float (default 0.80)
medium_confidence_threshold: float (default 0.60)
auto_send_high_confidence: bool (default True)
require_review_medium: bool (default True)
escalate_low_confidence: bool (default True)
min_quality_score_for_send: float (default 0.70)
max_model_age_days: int (default 30)
max_knowledge_base_age_days: int (default 14)
last_modified: datetime
```

---

### API Endpoints Summary

#### Ticket Ingestion & Management
```
POST   /tickets/ingest             # Create ticket & generate response
GET    /tickets/all                # List all tickets
GET    /tickets/{id}               # Get ticket details
POST   /feedback                   # Submit feedback (HITL learning)
GET    /stats                      # Basic statistics
GET    /health                     # Health check
```

#### Knowledge Base (RAG)
```
GET    /knowledge-base/articles
POST   /knowledge-base/articles
GET    /knowledge-base/search?query=...&top_k=3
GET    /knowledge-base/article/{id}
PUT    /knowledge-base/article/{id}
DELETE /knowledge-base/article/{id}
GET    /knowledge-base/stats
```

#### Confidence Routing & HITL
```
GET    /confidence-routing/stats
GET    /trust-config
PUT    /trust-config
```

#### FMEA & Failure Analysis
```
GET    /fmea/analysis?days=30
GET    /fmea/trends?mode=...
GET    /fmea/high-risk-tickets?threshold=0.80
POST   /fmea/log-failure
```

#### Quality Metrics
```
POST   /quality-metrics/evaluate
```

#### Prompt Engineering
```
GET    /prompt-templates/{category}?tone=...
POST   /prompt-engineering/construct
```

#### Advanced Statistics
```
GET    /advanced-stats             # Comprehensive view
```

---

### Example Workflow

1. **Ticket Arrives**:
   ```
   POST /tickets/ingest
   {
     "customer_id": "CUST_001",
     "subject": "Billing issue",
     "description": "Why was I charged twice this month?"
   }
   ```

2. **System Processes**:
   - Classification: "billing" (confidence 0.95)
   - Tone detection: "frustrated"
   - RAG retrieval: 3 billing articles
   - Prompt engineering: Generate frustrated-tone response
   - Quality evaluation: RAGAS score 0.82
   - Routing decision: MEDIUM confidence + good quality = REVIEW

3. **Response Returned**:
   ```json
   {
     "ticket_id": "abc123",
     "category": "billing",
     "category_confidence": 0.95,
     "confidence_level": "high",
     "proposed_response": "We sincerely apologize for the billing issue...",
     "response_confidence": 0.82,
     "quality_level": "good",
     "tone": "frustrated",
     "routing_decision": "review",
     "rag_sources_used": 3
   }
   ```

4. **Agent Reviews & Provides Feedback**:
   ```
   POST /feedback
   {
     "ticket_id": "abc123",
     "feedback_type": "edited",
     "final_response": "We sincerely apologize... [agent's improved version]"
   }
   ```

5. **System Learns**:
   - Stores edited response + original context
   - Records that high-confidence wasn't perfect
   - Updates confidence routing if pattern emerges
   - Logs to FMEA for analysis

6. **Analytics**:
   ```
   GET /fmea/analysis?days=30
   Returns: Failure patterns, high-risk tickets
   
   GET /advanced-stats
   Returns: Full system health, routing stats, KB metrics
   ```

---

### Key Design Decisions

1. **Rule-Based Classification**: Fast, explainable, no model staleness for core logic
2. **RAG Over Pure Generation**: Grounded responses reduce hallucination
3. **Quality Gates**: Multiple checks (RAGAS + staleness) before automation
4. **HITL as Core Pattern**: Confidence routing ensures humans stay in loop
5. **FMEA-Driven Improvement**: Systematic tracking of failures
6. **Tunable Thresholds**: Not one-size-fits-all for all orgs/categories
7. **Feedback as Core Asset**: Every agent decision improves future routing

---

### Deployment

```bash
# Start API
.venv/Scripts/python.exe run_api.py

# Start UI (optional)
.venv/Scripts/python.exe -m streamlit run app.py

# API runs on http://localhost:8000
# UI runs on http://localhost:8501
```

### Data Persistence

- **Tickets**: `./data/tickets.json`
- **Feedback**: `./data/feedback.json`
- **Knowledge Base**: `./data/knowledge_base.json`
- **FMEA Log**: `./data/fmea_log.json`

All data persists across restarts.

---

### Future Enhancements

1. **LLM Integration**: Replace template-based with fine-tuned models
2. **A/B Testing**: Compare routing policies
3. **Multi-language**: Tone detection + response in other languages
4. **Auto-escalation**: Escalate based on sentiment trend
5. **Performance Monitoring**: Dashboard for SLA tracking
6. **Batch Learning**: Re-train classifier on feedback corpus weekly

