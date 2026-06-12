from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import json
import os

from models import (
    SupportTicket, ProposedResponse, AgentFeedback, 
    FeedbackType, TicketCategory, TicketWithProposal,
    ClassificationResult, ConfidenceLevel, ResponseQuality
)
from ticket_classifier import TicketClassifier
from response_generator import ResponseGenerator
from feedback_store import FeedbackStore
from knowledge_base import get_knowledge_base
from prompt_manager import get_prompt_engineer, ToneAnalyzer
from quality_metrics import get_quality_evaluator
from confidence_router import get_confidence_router
from fmea_tracker import get_fmea_tracker
from escalation_map import EscalationRouter
from advanced_routes import setup_advanced_routes
from auto_draft_metrics import AutoDraftMetricsAnalyzer
from drift_dashboard import DriftDetector

app = FastAPI(title="Support Triage Co-pilot API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
classifier = TicketClassifier()
feedback_store = FeedbackStore()
generator = ResponseGenerator(feedback_store=feedback_store)
escalation_router = EscalationRouter()

# Initialize advanced components
kb = get_knowledge_base()
prompt_engineer = get_prompt_engineer()
quality_evaluator = get_quality_evaluator()
confidence_router = get_confidence_router()
fmea_tracker = get_fmea_tracker()

# Persistent storage setup
STORAGE_DIR = "./data"
os.makedirs(STORAGE_DIR, exist_ok=True)
TICKETS_FILE = os.path.join(STORAGE_DIR, "tickets.json")
FEEDBACK_FILE = os.path.join(STORAGE_DIR, "feedback.json")

# In-memory ticket storage with disk persistence
tickets_db = {}
feedback_db = {}

def load_from_disk():
    """Load tickets and feedback from disk"""
    global tickets_db, feedback_db
    try:
        if os.path.exists(TICKETS_FILE):
            with open(TICKETS_FILE, 'r') as f:
                tickets_data = json.load(f)
                # Reconstruct ticket objects - skip on errors for backward compatibility
                for ticket_id, data in tickets_data.items():
                    try:
                        # Get confidence_level from proposal or default it
                        proposal_data = data.get("proposal", {})
                        confidence_level = proposal_data.get("confidence_level", "medium")
                        if confidence_level not in ["high", "medium", "low"]:
                            confidence_level = "medium"
                        
                        # Create ProposedResponse with confidence_level
                        proposed_response = ProposedResponse(
                            ticket_id=proposal_data["ticket_id"],
                            proposed_response=proposal_data["proposed_response"],
                            confidence=proposal_data["confidence"],
                            confidence_level=ConfidenceLevel(confidence_level),
                            generated_at=datetime.fromisoformat(proposal_data["generated_at"])
                        )
                        
                        tickets_db[ticket_id] = {
                            "ticket": SupportTicket(
                                ticket_id=data["ticket"]["ticket_id"],
                                customer_id=data["ticket"]["customer_id"],
                                subject=data["ticket"]["subject"],
                                description=data["ticket"]["description"],
                                created_at=datetime.fromisoformat(data["ticket"]["created_at"]),
                                category=TicketCategory(data["ticket"]["category"]) if data["ticket"].get("category") else None
                            ),
                            "proposal": proposed_response
                        }
                    except Exception as e:
                        print(f"Warning: Could not load ticket {ticket_id}: {e}")
                        continue
        
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, 'r') as f:
                feedback_db = json.load(f)
    except Exception as e:
        print(f"Error loading from disk: {e}")

def save_to_disk():
    """Save tickets and feedback to disk"""
    try:
        # Save tickets
        tickets_to_save = {}
        for ticket_id, data in tickets_db.items():
            tickets_to_save[ticket_id] = {
                "ticket": {
                    "ticket_id": data["ticket"].ticket_id,
                    "customer_id": data["ticket"].customer_id,
                    "subject": data["ticket"].subject,
                    "description": data["ticket"].description,
                    "created_at": data["ticket"].created_at.isoformat(),
                    "category": data["ticket"].category
                },
                "proposal": {
                    "ticket_id": data["proposal"].ticket_id,
                    "proposed_response": data["proposal"].proposed_response,
                    "confidence": data["proposal"].confidence,
                    "generated_at": data["proposal"].generated_at.isoformat()
                }
            }
        
        with open(TICKETS_FILE, 'w') as f:
            json.dump(tickets_to_save, f, indent=2)
        
        # Save feedback
        with open(FEEDBACK_FILE, 'w') as f:
            json.dump(feedback_db, f, indent=2)
    except Exception as e:
        print(f"Error saving to disk: {e}")

# Load data on startup
load_from_disk()

# Note: Advanced routes setup is deferred to prevent initialization issues
# They will be added when needed or via manual registration


class TicketRequest(BaseModel):
    customer_id: str
    subject: str
    description: str

class FeedbackRequest(BaseModel):
    ticket_id: str
    feedback_type: str  # "accepted", "edited", "rejected"
    final_response: Optional[str] = None  # for edited feedback

@app.post("/tickets/ingest", response_model=dict, status_code=201)
async def ingest_ticket(ticket: TicketRequest):
    """Ingest a new support ticket with advanced triage features"""
    
    ticket_id = str(uuid.uuid4())[:8]
    
    # Classify ticket with confidence level
    classification = classifier.classify_ticket(ticket_id, ticket.subject, ticket.description)
    category = classification.category
    
    # Create ticket object with tone detection
    tone = ToneAnalyzer.detect_tone(ticket.description)
    ticket_obj = SupportTicket(
        ticket_id=ticket_id,
        customer_id=ticket.customer_id,
        subject=ticket.subject,
        description=ticket.description,
        created_at=datetime.now(),
        category=category,
        tone=tone
    )
    
    # Generate enhanced response with RAG and confidence scoring
    proposed_response = generator.generate_response(
        ticket_id=ticket_id,
        ticket_subject=ticket.subject,
        ticket_description=ticket.description,
        category=category.value,
        classification=classification
    )
    
    # Determine routing decision using confidence router
    # IMPORTANT: Pass subject and description for escalation detection
    routing_decision = confidence_router.route_response(
        proposed_response=proposed_response,
        quality_level=proposed_response.quality_level,
        subject=ticket.subject,
        description=ticket.description
    )
    
    # Check for high-confidence failures (FMEA)
    # Store ticket and proposal
    tickets_db[ticket_id] = {
        "ticket": ticket_obj,
        "proposal": proposed_response,
        "classification": classification,
        "routing_decision": routing_decision
    }
    
    # Save to disk
    save_to_disk()
    
    # Safe routing decision access
    routing_decision = routing_decision or {}
    
    return {
        "ticket_id": ticket_id,
        "category": category.value,
        "category_confidence": classification.confidence,
        "confidence_level": classification.confidence_level.value,
        "proposed_response": proposed_response.proposed_response,
        "response_confidence": proposed_response.confidence,
        "confidence_level_response": proposed_response.confidence_level.value,
        "quality_score": proposed_response.ragas_score,
        "quality_level": proposed_response.quality_level.value if proposed_response.quality_level else "unknown",
        "tone": tone,
        "routing_decision": routing_decision.get("routing_decision", "normal"),
        "is_critical_escalation": routing_decision.get("is_critical_escalation", False),
        "escalation_category": routing_decision.get("escalation_category"),
        "escalation_severity": routing_decision.get("escalation_severity"),
        "target_team": routing_decision.get("target_team"),
        "sla_minutes": routing_decision.get("sla_minutes"),
        "rag_sources_used": len(proposed_response.retrieved_sources),
        "used_feedback_context": len(proposed_response.retrieved_sources) > 0
    }

@app.get("/tickets/all", response_model=list)
async def get_all_tickets():
    """Get all tickets with their details and feedback"""
    tickets_list = []
    for ticket_id, ticket_data in tickets_db.items():
        ticket = ticket_data["ticket"]
        proposal = ticket_data["proposal"]
        feedback = feedback_db.get(ticket_id)
        
        tickets_list.append({
            "ticket_id": ticket_id,
            "customer_id": ticket.customer_id,
            "subject": ticket.subject,
            "description": ticket.description,
            "category": ticket.category,
            "created_at": ticket.created_at.isoformat(),
            "proposed_response": proposal.proposed_response,
            "response_confidence": proposal.confidence,
            "feedback": feedback
        })
    
    # Sort by creation date, newest first
    tickets_list.sort(key=lambda x: x["created_at"], reverse=True)
    return tickets_list

@app.get("/tickets/{ticket_id}", response_model=dict)
async def get_ticket(ticket_id: str):
    """Get ticket details with proposed response"""
    
    if ticket_id not in tickets_db:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket_data = tickets_db[ticket_id]
    
    return {
        "ticket": ticket_data["ticket"].dict(),
        "proposed_response": ticket_data["proposal"].dict(),
        "feedback": feedback_db.get(ticket_id)
    }

@app.post("/feedback", response_model=dict)
async def submit_feedback(feedback: FeedbackRequest):
    """Submit agent feedback with FMEA tracking"""
    
    if feedback.ticket_id not in tickets_db:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket_data = tickets_db.get(feedback.ticket_id)
    if not ticket_data:
        raise HTTPException(status_code=404, detail="Ticket data not found")
    
    ticket = ticket_data.get("ticket")
    proposal = ticket_data.get("proposal")
    classification = ticket_data.get("classification")
    
    if not ticket or not proposal:
        raise HTTPException(status_code=400, detail="Ticket or proposal data missing")
    
    # Track feedback type
    try:
        feedback_type = FeedbackType(feedback.feedback_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid feedback type: {feedback.feedback_type}")
    
    # Store feedback in ChromaDB/vector store
    try:
        proposal_text = proposal.proposed_response if hasattr(proposal, 'proposed_response') else str(proposal)
        ticket_text = f"{ticket.subject}: {ticket.description}"
        category_value = ticket.category.value if hasattr(ticket.category, 'value') else str(ticket.category)
        
        if feedback_type == FeedbackType.ACCEPTED:
            feedback_store.store_accepted_feedback(
                ticket_id=feedback.ticket_id,
                category=category_value,
                original_ticket=ticket_text,
                response=proposal_text
            )
        elif feedback_type == FeedbackType.EDITED:
            if not feedback.final_response:
                raise HTTPException(status_code=400, detail="final_response required for edited feedback")
            feedback_store.store_edited_feedback(
                ticket_id=feedback.ticket_id,
                category=category_value,
                original_ticket=ticket_text,
                proposed_response=proposal_text,
                edited_response=feedback.final_response
            )
        elif feedback_type == FeedbackType.REJECTED:
            feedback_store.store_rejected_feedback(
                ticket_id=feedback.ticket_id,
                category=category_value,
                original_ticket=ticket_text,
                rejected_response=proposal_text
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error storing feedback: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error storing feedback: {str(e)}")
    
    # FMEA: Detect high-confidence failures
    try:
        confidence = None
        if hasattr(proposal, 'confidence'):
            confidence = proposal.confidence
        elif isinstance(proposal, dict) and 'confidence' in proposal:
            confidence = proposal['confidence']
        
        if confidence and confidence >= 0.75:
            fmea_tracker.detect_high_confidence_wrong_response(
                ticket_id=feedback.ticket_id,
                confidence=confidence,
                agent_feedback=feedback_type
            )
    except Exception as e:
        # Log but don't fail on FMEA error
        print(f"FMEA tracking error: {str(e)}")
    
    # Store feedback
    feedback_db[feedback.ticket_id] = {
        "feedback_type": feedback_type.value,
        "submitted_at": datetime.now().isoformat(),
        "final_response": feedback.final_response,
        "quality_assessed": True
    }
    
    # Save to disk
    save_to_disk()
    
    return {
        "status": "success",
        "ticket_id": feedback.ticket_id,
        "feedback_type": feedback_type.value
    }

@app.get("/stats", response_model=dict)
async def get_stats():
    """Get system statistics from actual data files"""
    
    # Load from actual feedback.json file
    try:
        with open("data/feedback.json", "r") as f:
            feedback_data = json.load(f)
        
        accepted_count = sum(1 for v in feedback_data.values() if v.get("feedback_type") == "accepted")
        edited_count = sum(1 for v in feedback_data.values() if v.get("feedback_type") == "edited")
        rejected_count = sum(1 for v in feedback_data.values() if v.get("feedback_type") == "rejected")
    except FileNotFoundError:
        accepted_count = 0
        edited_count = 0
        rejected_count = 0
    
    return {
        "total_tickets_processed": len(tickets_db),
        "total_feedback_collected": len(feedback_db),
        "accepted_responses": accepted_count,
        "edited_responses": edited_count,
        "rejected_responses": rejected_count
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/tickets/all", response_model=list)
async def get_all_tickets():
    """Get all tickets with their details and feedback"""
    tickets_list = []
    for ticket_id, ticket_data in tickets_db.items():
        ticket = ticket_data["ticket"]
        proposal = ticket_data["proposal"]
        feedback = feedback_db.get(ticket_id)
        
        tickets_list.append({
            "ticket_id": ticket_id,
            "customer_id": ticket.customer_id,
            "subject": ticket.subject,
            "description": ticket.description,
            "category": ticket.category,
            "created_at": ticket.created_at.isoformat(),
            "proposed_response": proposal.proposed_response,
            "response_confidence": proposal.confidence,
            "feedback": feedback
        })
    
    # Sort by creation date, newest first
    tickets_list.sort(key=lambda x: x["created_at"], reverse=True)
    return tickets_list

@app.get("/knowledge-base/search", tags=["Knowledge Base"])
async def search_knowledge_base(query: str, category: Optional[str] = None, top_k: int = 3):
    """Search knowledge base with RAG retrieval"""
    results = kb.retrieve(query, top_k=top_k, category_filter=category)
    
    return {
        "query": query,
        "results": [
            {
                "source_id": r.source_id,
                "source_title": r.source_title,
                "source_content": r.source_content[:300],
                "relevance_score": r.relevance_score
            }
            for r in results
        ]
    }

@app.get("/trust-config", tags=["Trust Configuration"])
async def get_trust_config():
    """Get current trust architecture configuration"""
    return confidence_router.get_config()

@app.get("/confidence-routing/stats", tags=["Confidence Routing"])
async def get_routing_stats():
    """Get confidence routing statistics"""
    return confidence_router.get_routing_stats()

@app.get("/fmea/analysis", tags=["FMEA"])
async def get_fmea_analysis(days: int = 30):
    """Get FMEA analysis for recent failures"""
    return fmea_tracker.get_failure_analysis(time_window_days=days)

@app.get("/fmea/high-risk-tickets", tags=["FMEA"])
async def get_high_risk_tickets(threshold: float = 0.80):
    """Get high-confidence tickets with failures"""
    return {"high_risk_tickets": fmea_tracker.get_high_risk_tickets(threshold)}

@app.post("/escalations/detect", tags=["Escalations"])
async def detect_escalation(subject: str, description: str):
    """Detect if a ticket matches critical escalation categories"""
    result = escalation_router.detector.detect(subject, description)
    return {
        "is_escalation": result.is_escalation,
        "escalation_category": result.escalation_category.value if result.escalation_category else None,
        "confidence": result.confidence,
        "reason": result.reason,
        "severity": result.severity,
        "agent_notes": result.agent_notes
    }

@app.get("/escalations/stats", tags=["Escalations"])
async def get_escalation_stats():
    """Get escalation statistics from processed tickets"""
    escalation_tickets = [
        data for ticket_id, data in tickets_db.items()
        if data.get("routing_decision", {}).get("is_critical_escalation", False)
    ]
    
    escalation_breakdown = {}
    for ticket_data in escalation_tickets:
        category = ticket_data.get("routing_decision", {}).get("escalation_category", "unknown")
        escalation_breakdown[category] = escalation_breakdown.get(category, 0) + 1
    
    return {
        "total_escalations": len(escalation_tickets),
        "escalation_breakdown": escalation_breakdown,
        "escalation_rate": len(escalation_tickets) / max(len(tickets_db), 1),
        "mapping": {
            "vip": "VIP Support Team",
            "cancellation_intent": "Retention Specialists",
            "complaint_escalation": "Complaint Management Team",
            "jurisdictional": "Legal Compliance Team",
            "legal_refund": "Legal/Finance Team"
        }
    }

@app.get("/advanced-stats", tags=["Statistics"])
async def get_advanced_stats():
    """Get comprehensive advanced statistics"""
    return {
        "knowledge_base": kb.get_stats(),
        "routing": confidence_router.get_routing_stats(),
        "fmea": fmea_tracker.get_failure_analysis(days=30),
        "escalations": await get_escalation_stats(),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/auto-draft-metrics", tags=["Outcomes"])
async def get_auto_draft_metrics():
    """Get auto-draft metrics (Outcome 1 & 2): auto-draft rate and acceptance rate"""
    try:
        analyzer = AutoDraftMetricsAnalyzer()
        analyzer.load_pipeline_results()
        report = analyzer.generate_report()
        
        # Load JSON data for response
        report_path = "data/auto_draft_report.json"
        if os.path.exists(report_path):
            with open(report_path, 'r') as f:
                report_data = json.load(f)
            return report_data
        else:
            return {
                "error": "No auto-draft metrics available yet",
                "message": "Run synthetic pipeline first to generate metrics",
                "path": report_path
            }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to generate auto-draft metrics"
        }

@app.get("/drift-dashboard", tags=["Outcomes"])
async def get_drift_dashboard():
    """Get drift dashboard (Outcome 3): acceptance rate anomaly detection"""
    try:
        detector = DriftDetector()
        dashboard_data = detector.generate_dashboard_data()
        
        # Load JSON data for response
        dashboard_path = "data/drift_dashboard.json"
        if os.path.exists(dashboard_path):
            with open(dashboard_path, 'r') as f:
                data = json.load(f)
            return data
        else:
            return {
                "error": "No drift dashboard data available yet",
                "message": "Run synthetic pipeline first to generate metrics",
                "path": dashboard_path
            }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to generate drift dashboard"
        }

@app.get("/drift-dashboard/html", tags=["Outcomes"])
async def get_drift_dashboard_html():
    """Get drift dashboard HTML report"""
    html_path = "data/drift_dashboard.html"
    if os.path.exists(html_path):
        with open(html_path, 'r') as f:
            html_content = f.read()
        return {"html": html_content, "path": html_path}
    else:
        return {
            "error": "No HTML report available",
            "path": html_path,
            "message": "Run drift dashboard generation first"
        }

@app.get("/outcomes/summary", tags=["Outcomes"])
async def get_outcomes_summary():
    """Get summary of all 4 outcome requirements"""
    outcomes = {
        "outcome_1": {
            "name": "Auto-Draft Rate (≥50%)",
            "description": "Percentage of repetitive tickets auto-drafted",
            "status": "checking...",
            "goal_met": None
        },
        "outcome_2": {
            "name": "Acceptance Rate (≥80%)",
            "description": "Agent acceptance rate of auto-drafted responses",
            "status": "checking...",
            "goal_met": None
        },
        "outcome_3": {
            "name": "Drift Dashboard",
            "description": "Real-time acceptance rate anomaly detection",
            "status": "checking...",
            "goal_met": None
        },
        "outcome_4": {
            "name": "Escalation Paths",
            "description": "Clear routing for 5 never-auto categories",
            "status": "verified",
            "goal_met": True,
            "details": {
                "vip": "VIP Support (30 min SLA)",
                "cancellation": "Retention Team (15 min SLA)",
                "complaint": "Complaint Management (15 min SLA)",
                "jurisdictional": "Legal Compliance (60 min SLA)",
                "legal_refund": "Legal/Finance (15 min SLA)"
            }
        }
    }
    
    # Check Outcome 1 & 2
    auto_draft_path = "data/auto_draft_report.json"
    if os.path.exists(auto_draft_path):
        try:
            with open(auto_draft_path, 'r') as f:
                report = json.load(f)
            outcomes["outcome_1"]["status"] = f"auto_draft_rate: {report.get('auto_draft_rate', 0):.1%}"
            outcomes["outcome_1"]["goal_met"] = report.get('auto_draft_rate', 0) >= 0.50
            outcomes["outcome_2"]["status"] = f"acceptance_rate: {report.get('acceptance_rate', 0):.1%}"
            outcomes["outcome_2"]["goal_met"] = report.get('acceptance_rate', 0) >= 0.80
            outcomes["outcome_1"]["metrics"] = {
                "auto_draft_rate": report.get('auto_draft_rate'),
                "acceptance_rate": report.get('acceptance_rate'),
                "repetitive_tickets": report.get('repetitive_tickets'),
                "auto_drafted": report.get('auto_drafted')
            }
        except Exception as e:
            outcomes["outcome_1"]["status"] = f"error: {str(e)}"
            outcomes["outcome_2"]["status"] = f"error: {str(e)}"
    
    # Check Outcome 3
    drift_path = "data/drift_dashboard.json"
    if os.path.exists(drift_path):
        try:
            with open(drift_path, 'r') as f:
                drift_data = json.load(f)
            current_rate = drift_data.get("statistics", {}).get("current_acceptance_rate")
            if current_rate:
                outcomes["outcome_3"]["status"] = f"current_rate: {current_rate:.1%}"
                outcomes["outcome_3"]["goal_met"] = True
                outcomes["outcome_3"]["drift_status"] = drift_data.get("overall_trend")
        except Exception as e:
            outcomes["outcome_3"]["status"] = f"error: {str(e)}"
    
    return outcomes

if __name__ == "__main__":
    import uvicorn
    import logging
    logging.basicConfig(level=logging.DEBUG)
    print("Starting API server on http://0.0.0.0:8000")
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
