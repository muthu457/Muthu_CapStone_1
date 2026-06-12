"""
Minimal FastAPI server without version conflicts
Provides basic endpoints for the Streamlit UI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import json
import os
import uvicorn

# Simple data models
class TicketRequest(BaseModel):
    customer_id: str
    subject: str
    description: str

class FeedbackRequest(BaseModel):
    ticket_id: str
    feedback_type: str  # "accepted", "edited", "rejected"
    final_response: Optional[str] = None

# Initialize FastAPI app
app = FastAPI(title="Support Triage Co-pilot API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage setup
STORAGE_DIR = "./data"
os.makedirs(STORAGE_DIR, exist_ok=True)
TICKETS_FILE = os.path.join(STORAGE_DIR, "tickets.json")
FEEDBACK_FILE = os.path.join(STORAGE_DIR, "feedback.json")

def load_json(filepath):
    """Load JSON file safely"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json(filepath, data):
    """Save JSON file safely"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        print(f"Error saving {filepath}: {e}")

# ==================== ENDPOINTS ====================

@app.get("/")
def root():
    """Health check"""
    return {"status": "ok", "api": "Support Triage Co-pilot"}

@app.post("/tickets/ingest")
def ingest_ticket(ticket: TicketRequest):
    """Ingest a new support ticket"""
    try:
        ticket_id = str(uuid.uuid4())[:8]
        
        # Determine category based on keywords
        text = (ticket.subject + " " + ticket.description).lower()
        category = "general"
        
        if any(word in text for word in ["billing", "invoice", "charge", "payment"]):
            category = "billing"
        elif any(word in text for word in ["password", "login", "access", "account"]):
            category = "account"
        elif any(word in text for word in ["bug", "error", "crash", "fail"]):
            category = "technical"
        elif any(word in text for word in ["feature", "request", "add", "improve"]):
            category = "feature_request"
        
        # Calculate confidence (mock)
        confidence = 0.72
        if category != "general":
            confidence = 0.78
        
        # Load existing tickets
        tickets = load_json(TICKETS_FILE)
        
        # Create ticket record
        ticket_data = {
            "ticket_id": ticket_id,
            "customer_id": ticket.customer_id,
            "subject": ticket.subject,
            "description": ticket.description,
            "created_at": datetime.now().isoformat(),
            "category": category
        }
        
        # Generate a mock response
        proposed_response = f"Thank you for contacting us about '{ticket.subject}'. We've categorized this as a {category} issue. Our team will review this shortly."
        
        proposal_data = {
            "ticket_id": ticket_id,
            "proposed_response": proposed_response,
            "confidence": confidence,
            "confidence_level": "high" if confidence > 0.75 else "medium" if confidence > 0.5 else "low",
            "generated_at": datetime.now().isoformat()
        }
        
        tickets[ticket_id] = {
            "ticket": ticket_data,
            "proposal": proposal_data
        }
        
        # Save tickets
        save_json(TICKETS_FILE, tickets)
        
        return {
            "ticket_id": ticket_id,
            "category": category,
            "category_confidence": confidence,
            "proposed_response": proposed_response,
            "confidence_level": proposal_data["confidence_level"],
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}, 400

@app.post("/feedback")
def submit_feedback(feedback: FeedbackRequest):
    """Submit feedback on a ticket"""
    try:
        # Load existing feedback
        feedback_data = load_json(FEEDBACK_FILE)
        
        feedback_record = {
            "ticket_id": feedback.ticket_id,
            "feedback_type": feedback.feedback_type,
            "final_response": feedback.final_response,
            "timestamp": datetime.now().isoformat()
        }
        
        if "feedback" not in feedback_data:
            feedback_data["feedback"] = []
        
        feedback_data["feedback"].append(feedback_record)
        
        # Save feedback
        save_json(FEEDBACK_FILE, feedback_data)
        
        return {
            "status": "success",
            "ticket_id": feedback.ticket_id,
            "feedback_type": feedback.feedback_type
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}, 400

@app.get("/stats")
def get_stats():
    """Get feedback statistics"""
    try:
        feedback_data = load_json(FEEDBACK_FILE)
        feedback_list = feedback_data.get("feedback", [])
        
        accepted = sum(1 for f in feedback_list if f.get("feedback_type") == "accepted")
        edited = sum(1 for f in feedback_list if f.get("feedback_type") == "edited")
        rejected = sum(1 for f in feedback_list if f.get("feedback_type") == "rejected")
        
        return {
            "accepted_responses": accepted,
            "edited_responses": edited,
            "rejected_responses": rejected,
            "total_feedback": len(feedback_list)
        }
    except Exception as e:
        return {"error": str(e)}, 400

@app.get("/tickets")
def list_tickets(skip: int = 0, limit: int = 50):
    """List all tickets"""
    try:
        tickets = load_json(TICKETS_FILE)
        ticket_list = list(tickets.values())
        return {
            "total": len(ticket_list),
            "tickets": ticket_list[skip:skip+limit]
        }
    except Exception as e:
        return {"error": str(e)}, 400

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    print("Starting Minimal API server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
