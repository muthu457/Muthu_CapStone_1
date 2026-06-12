# Triage System - Quick Start Guide

## Installation & Setup

```bash
# Navigate to project
cd Muthu_Capstone_1

# Activate environment
.venv/Scripts/activate

# Optional: Set Gemini API key for enhanced synthetic data
set GOOGLE_API_KEY=your_key_here

# Start both API and Streamlit
.venv/Scripts/python.exe run_api.py  # Terminal 1
.venv/Scripts/streamlit.exe run app.py  # Terminal 2
```

## Accessing the System

| Component | URL | Purpose |
|-----------|-----|---------|
| API Documentation | http://localhost:8000/docs | Explore all endpoints |
| Streamlit Dashboard | http://localhost:8501 | Visual interface |
| Health Check | http://localhost:8000/health | System status |

## Testing the 4 Deliverables

### 1. Working Pipeline with Feedback

```bash
# Generate 30 synthetic tickets and process through pipeline
python synthetic_pipeline.py

# Results stored in: data/pipeline_results.json
# Shows: confidence scores, routing decisions, feedback simulation
```

### 2. Causal Loop Diagram

```bash
# View the comprehensive feedback loop documentation
cat CAUSAL_LOOP_DIAGRAM.md

# Key insight: One agent rejection → 15 min to threshold adjustment → 
# Improved routing for similar tickets in next batch
```

### 3. Confidence Calibration Analysis

```bash
# Analyze pipeline results and generate calibration curve
python calibration_analysis.py

# Results: data/calibration_analysis.json
# Shows: Over/under-confident ranges, recommendations, system health
```

### 4. Escalation Map (5 Critical Categories)

```bash
# Query escalation detection
curl -X POST http://localhost:8000/escalations/detect \
  -d "subject=Cancel+my+account&description=I+want+to+leave"

# See escalation stats
curl http://localhost:8000/escalations/stats

# Categories: VIP, Cancellation, Complaint, Jurisdictional, Legal/Refund
```

## Key Files Created

| File | Purpose |
|------|---------|
| `synthetic_pipeline.py` | Generate tickets + simulate feedback |
| `calibration_analysis.py` | Analyze confidence vs acceptance rates |
| `escalation_map.py` | Detect and route 5 critical categories |
| `CAUSAL_LOOP_DIAGRAM.md` | Feedback loop documentation |
| `DELIVERABLES.md` | Comprehensive delivery documentation |
| `test_integration.py` | Integration test script |

## Example Workflows

### Scenario 1: Submit a Billing Ticket

```bash
curl -X POST http://localhost:8000/tickets/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST_001",
    "subject": "Double billing issue",
    "description": "I was charged twice this month. Please fix it!"
  }'
```

**Response includes**:
- Classification confidence (0.95 for billing keywords)
- Routing decision (auto_send / review / escalate)
- RAGAS quality score
- Tone analysis (frustrated)

### Scenario 2: Detect Escalation

```bash
curl -X POST http://localhost:8000/escalations/detect \
  -d "subject=GDPR+Data+Request&description=I+want+my+data+under+GDPR"
```

**Response**:
- `escalation_category`: "jurisdictional"
- `confidence`: 0.95
- `target_team`: "legal_compliance_team"
- `sla_minutes`: 60

### Scenario 3: Check System Health

```bash
curl http://localhost:8000/advanced-stats | python -m json.tool

# Shows:
# - Knowledge base statistics
# - Confidence routing stats
# - FMEA failure analysis
# - Escalation breakdown
```

## API Endpoints Summary

### Ticket Processing
- `POST /tickets/ingest` - Process new ticket
- `GET /tickets/all` - View all tickets
- `POST /feedback` - Submit agent feedback

### Escalations (NEW)
- `POST /escalations/detect` - Detect critical categories
- `GET /escalations/stats` - View escalation statistics

### Analysis
- `GET /advanced-stats` - Comprehensive health dashboard
- `GET /confidence-routing/stats` - Routing statistics
- `GET /fmea/analysis` - Failure mode analysis
- `GET /fmea/high-risk-tickets` - High-risk identifications

### Knowledge Base & Trust
- `GET /knowledge-base/search` - RAG retrieval
- `GET /trust-config` - Current trust thresholds
- `PUT /trust-config` - Update thresholds

## Understanding the Metrics

### Confidence Levels
- **HIGH** (>0.80): Can be auto-sent with good quality
- **MEDIUM** (0.60-0.80): Requires agent review
- **LOW** (<0.60): Escalate or seek clarification

### Routing Decisions
- **auto_send**: Send directly to customer (high confidence + good quality)
- **review**: Human agent reviews before sending
- **escalate**: Send to specialized team (VIP, legal, etc.)

### Quality Metrics (RAGAS)
- **Faithfulness** (0-1): Does response match knowledge base?
- **Answer Relevance** (0-1): Does it answer the question?
- **Context Precision** (0-1): Quality of retrieved sources
- **Context Recall** (0-1): Completeness of context

## Troubleshooting

### API won't start
```bash
# Kill any lingering processes
taskkill /FI "IMAGENAME eq python.exe" /F

# Restart
.venv/Scripts/python.exe run_api.py
```

### Escalations not detected
- Ensure `escalation_map.py` is in the project directory
- Check that keywords match expected patterns (see DELIVERABLES.md)
- Verify minimum confidence thresholds aren't too high

### Calibration analysis errors
- Run synthetic pipeline first to generate `pipeline_results.json`
- Ensure `data/` directory exists
- Check file permissions

## Production Readiness

✅ **Implemented**:
- Clean architecture (10 modular files)
- Complete HITL pattern (confidence routing)
- RAGAS quality metrics
- Feedback loops (3 types)
- FMEA failure tracking
- RAG knowledge base
- Prompt engineering (tone-matched)
- Escalation handling (5 critical categories)
- Calibration analysis
- Trust architecture (tunable)

✅ **Tested**:
- All modules compile without errors
- API runs stably on port 8000
- Streamlit UI on port 8501
- Full pipeline end-to-end
- Escalation detection
- Calibration analysis

✅ **Documented**:
- DELIVERABLES.md (4 deliverables)
- CAUSAL_LOOP_DIAGRAM.md (feedback loops)
- ADVANCED_ARCHITECTURE.md (system design)
- IMPLEMENTATION_SUMMARY.md (changes log)
- README_ENTERPRISE.md (deployment)

## Next Steps

1. **Load Real Data**: Replace synthetic data with actual support tickets
2. **Tune Thresholds**: Use calibration analysis to optimize confidence levels
3. **Add Domain Knowledge**: Expand knowledge base with company-specific articles
4. **Monitor Performance**: Track escalation rates, acceptance rates, response times
5. **Iterate**: Weekly calibration reviews to improve routing decisions

## Support

All code is well-documented. Key entry points:

- **API**: `api.py` (main FastAPI application)
- **UI**: `app.py` (Streamlit dashboard)
- **Pipeline**: `synthetic_pipeline.py` (testing/validation)
- **Analysis**: `calibration_analysis.py` (quality tracking)
- **Escalations**: `escalation_map.py` (critical case handling)

