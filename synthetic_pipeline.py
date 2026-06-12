"""
Synthetic Ticket Generator + Pipeline Runner
Generates realistic support tickets using Faker + Gemini Flash
Processes through full triage pipeline and simulates agent feedback
Stores all data for confidence calibration analysis
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import random
from faker import Faker
import requests

# Configure Google Gemini
import google.generativeai as genai

fake = Faker()


@dataclass
class SyntheticTicket:
    """Synthetic ticket with metadata for analysis"""
    ticket_id: str
    customer_id: str
    customer_type: str  # "vip", "regular", "new"
    subject: str
    description: str
    category: str  # intended category
    tone: str  # "frustrated", "neutral", "urgent"
    created_at: str
    template: str  # which template was used


@dataclass
class PipelineResult:
    """Result from processing ticket through pipeline"""
    ticket_id: str
    classification_confidence: float
    classification_category: str
    routing_decision: str
    is_escalation: bool
    response_quality_score: float = 0.0
    agent_feedback: str = "pending"  # "accepted", "edited", "rejected"
    feedback_timestamp: str = None


class SyntheticTicketGenerator:
    """Generates realistic support tickets"""
    
    def __init__(self):
        # Initialize Gemini if API key is available
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.use_gemini = True
        else:
            self.use_gemini = False
        
        self.fake = Faker()
        self.templates = self._build_templates()
    
    def _build_templates(self) -> Dict[str, List[Dict]]:
        """Build ticket templates by category and tone"""
        return {
            "billing": {
                "neutral": [
                    {"subject": "Billing Question", "body_template": "I was charged ${amount} on my account. Can you explain this charge?"},
                    {"subject": "Invoice Inquiry", "body_template": "I don't recognize a charge for ${service}. Can you clarify?"},
                    {"subject": "Payment Question", "body_template": "When will my payment for ${service} be processed?"},
                ],
                "frustrated": [
                    {"subject": "Why am I being double-charged?!", "body_template": "This is ridiculous! I was charged twice for ${service}. Fix this NOW!"},
                    {"subject": "STOP billing me!", "body_template": "I'm being charged for services I cancelled! This is unacceptable!"},
                    {"subject": "Wrong charge on my account", "body_template": "There's an unauthorized charge for ${amount}. I want a refund immediately!"},
                ],
                "urgent": [
                    {"subject": "URGENT: Billing Issue", "body_template": "I need immediate help with this charge of ${amount}. My card is being charged continuously!"},
                    {"subject": "Billing crisis", "body_template": "Multiple incorrect charges on my account. This is critical - I need help today."},
                ]
            },
            "password_reset": {
                "neutral": [
                    {"subject": "Reset Password", "body_template": "I'd like to reset my password. Can you walk me through the process?"},
                    {"subject": "Forgot Password", "body_template": "I can't remember my password. How do I reset it?"},
                    {"subject": "Account Access Question", "body_template": "I'm having trouble accessing my account. Can you help?"},
                ],
                "frustrated": [
                    {"subject": "CAN'T ACCESS MY ACCOUNT!", "body_template": "I'm locked out of my account and this is infuriating! Reset my password NOW!"},
                    {"subject": "LOCKED OUT - HELP!", "body_template": "I keep getting error messages when trying to log in. This is terrible!"},
                    {"subject": "Password reset not working", "body_template": "The password reset link isn't working! What's wrong with your system?!"},
                ],
                "urgent": [
                    {"subject": "URGENT: Account locked - business impact", "body_template": "I cannot access my account and it's impacting my work. I need immediate access."},
                ]
            },
            "plan_change": {
                "neutral": [
                    {"subject": "Plan Upgrade", "body_template": "I'd like to upgrade my ${current_plan} plan to ${new_plan}. What's the process?"},
                    {"subject": "Plan Downgrade", "body_template": "I want to downgrade to a lower tier. How do I do this?"},
                    {"subject": "Plan Options", "body_template": "Can you tell me about your available plans?"},
                ],
                "frustrated": [
                    {"subject": "I need to cancel NOW", "body_template": "This service is useless for me. I want to downgrade or cancel immediately!"},
                    {"subject": "Your plans are too expensive", "body_template": "I can't afford this plan anymore. I'm switching to a competitor!"},
                ],
                "urgent": [
                    {"subject": "URGENT: Need plan change immediately", "body_template": "I need to change my plan within the hour. Can this be expedited?"},
                ]
            },
            "cancellation": {
                "frustrated": [
                    {"subject": "CANCEL MY ACCOUNT", "body_template": "I'm done with this service. Cancel my subscription immediately!"},
                    {"subject": "Want to leave", "body_template": "I've decided to unsubscribe. This service doesn't meet my needs."},
                ]
            },
            "complaint": {
                "frustrated": [
                    {"subject": "Your service is terrible", "body_template": "This is the worst experience ever. Your ${category} support is absolutely pathetic!"},
                    {"subject": "COMPLAINT: Outrageous service", "body_template": "I'm disgusted with how you've treated me. This is completely unacceptable!"},
                    {"subject": "Never again", "body_template": "I will NEVER use your service again. You're the worst company I've dealt with!"},
                ]
            }
        }
    
    def generate_ticket(self, category: str, tone: str = "neutral", 
                       customer_type: str = "regular") -> SyntheticTicket:
        """Generate a single synthetic ticket"""
        
        if category not in self.templates:
            category = "billing"
        
        if tone not in self.templates[category]:
            tone = "neutral"
        
        templates = self.templates[category][tone]
        template = random.choice(templates)
        
        # Generate subject
        subject = template["subject"]
        
        # Generate body with variable substitution
        body = template["body_template"]
        body = body.replace("${amount}", f"${random.randint(50, 500)}")
        body = body.replace("${service}", random.choice(["Premium Plan", "Storage Upgrade", "API Credits", "Support Package"]))
        body = body.replace("${current_plan}", random.choice(["Basic", "Standard", "Pro"]))
        body = body.replace("${new_plan}", random.choice(["Premium", "Enterprise", "Basic"]))
        body = body.replace("${category}", random.choice(["billing", "technical", "general"]))
        
        # Use Gemini to add natural variations if available
        if self.use_gemini:
            try:
                body = self._enhance_with_gemini(body, tone)
            except Exception as e:
                print(f"Gemini enhancement failed: {e}")
        
        return SyntheticTicket(
            ticket_id=f"SYN_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
            customer_id=self._generate_customer_id(customer_type),
            customer_type=customer_type,
            subject=subject,
            description=body,
            category=category,
            tone=tone,
            created_at=datetime.now().isoformat(),
            template=f"{category}_{tone}"
        )
    
    def _enhance_with_gemini(self, text: str, tone: str) -> str:
        """Use Gemini Flash to add natural variations to ticket text"""
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            prompt = f"""Rewrite this support ticket in a natural, varied way while keeping the same tone ({tone}). 
Keep it concise and realistic. Don't change the meaning, just the wording.

Original: {text}

Rewritten:"""
            
            response = model.generate_content(prompt, generation_config={
                "max_output_tokens": 150,
                "temperature": 0.7,
            })
            return response.text.strip()
        except Exception as e:
            print(f"Gemini enhancement error: {e}")
            return text
    
    def _generate_customer_id(self, customer_type: str) -> str:
        """Generate realistic customer IDs"""
        if customer_type == "vip":
            return f"VIP_{self.fake.bothify('###')}"
        elif customer_type == "new":
            return f"NEW_{self.fake.bothify('###')}"
        else:
            return f"CUST_{self.fake.bothify('######')}"
    
    def generate_batch(self, count: int = 50, distribution: Dict = None) -> List[SyntheticTicket]:
        """Generate a batch of tickets with specified distribution"""
        if distribution is None:
            distribution = {
                "billing": {"neutral": 0.3, "frustrated": 0.4, "urgent": 0.3},
                "password_reset": {"neutral": 0.4, "frustrated": 0.4, "urgent": 0.2},
                "plan_change": {"neutral": 0.5, "frustrated": 0.3, "urgent": 0.2},
                "cancellation": {"frustrated": 1.0},
                "complaint": {"frustrated": 1.0}
            }
        
        tickets = []
        customer_types = ["vip", "regular", "new"]
        
        for _ in range(count):
            # Pick category
            category = random.choices(
                list(distribution.keys()),
                weights=[0.35, 0.35, 0.15, 0.10, 0.05]  # billing, pwd, plan, cancel, complaint
            )[0]
            
            # Pick tone based on category distribution
            tone = random.choices(
                list(distribution[category].keys()),
                weights=list(distribution[category].values())
            )[0]
            
            # Pick customer type
            customer_type = random.choices(
                customer_types,
                weights=[0.10, 0.80, 0.10]  # 10% VIP, 80% regular, 10% new
            )[0]
            
            ticket = self.generate_ticket(category, tone, customer_type)
            tickets.append(ticket)
        
        return tickets


class PipelineRunner:
    """Runs tickets through the triage pipeline and simulates agent feedback"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base = api_base_url.rstrip("/")
        self.results: List[PipelineResult] = []
        self.feedback_data: List[Dict] = []
    
    def process_ticket(self, ticket: SyntheticTicket) -> PipelineResult:
        """Process ticket through API pipeline"""
        try:
            # Send to API
            response = requests.post(
                f"{self.api_base}/tickets/ingest",
                json={
                    "customer_id": ticket.customer_id,
                    "subject": ticket.subject,
                    "description": ticket.description
                },
                timeout=10
            )
            
            if response.status_code != 201:
                print(f"API error for {ticket.ticket_id}: {response.status_code}")
                return None
            
            data = response.json()
            
            result = PipelineResult(
                ticket_id=ticket.ticket_id,
                classification_confidence=data.get("category_confidence", 0),
                classification_category=data.get("category", "unknown"),
                routing_decision=data.get("routing_decision", "unknown"),
                is_escalation=data.get("routing_decision") == "escalate",
                response_quality_score=data.get("ragas_score", 0),
            )
            
            return result
        
        except Exception as e:
            print(f"Error processing {ticket.ticket_id}: {e}")
            return None
    
    def simulate_feedback(self, result: PipelineResult, actual_category: str) -> None:
        """Simulate agent feedback based on quality and category match"""
        
        # Feedback logic based on confidence and correctness
        if result.response_quality_score > 0.85 and result.classification_category == actual_category:
            # High quality + correct category → likely accepted
            feedback = random.choices(
                ["accepted", "edited"],
                weights=[0.85, 0.15]
            )[0]
        elif result.response_quality_score > 0.70:
            # Medium quality → likely edited
            feedback = random.choices(
                ["edited", "accepted", "rejected"],
                weights=[0.60, 0.25, 0.15]
            )[0]
        else:
            # Low quality → likely rejected
            feedback = random.choices(
                ["rejected", "edited"],
                weights=[0.70, 0.30]
            )[0]
        
        result.agent_feedback = feedback
        result.feedback_timestamp = datetime.now().isoformat()
        
        # Store for later analysis
        self.feedback_data.append({
            "ticket_id": result.ticket_id,
            "confidence": result.classification_confidence,
            "quality": result.response_quality_score,
            "category_correct": result.classification_category == actual_category,
            "feedback": feedback,
            "timestamp": result.feedback_timestamp
        })
    
    def run_pipeline(self, tickets: List[SyntheticTicket]) -> List[PipelineResult]:
        """Run full pipeline: ingest → process → feedback"""
        print(f"\n[PIPELINE] Processing {len(tickets)} tickets...")
        
        for i, ticket in enumerate(tickets):
            print(f"  [{i+1}/{len(tickets)}] Processing {ticket.ticket_id}...")
            
            result = self.process_ticket(ticket)
            if result:
                self.simulate_feedback(result, ticket.category)
                self.results.append(result)
            
            time.sleep(0.1)  # Rate limiting
        
        print(f"[PIPELINE] Completed. {len(self.results)} tickets processed.")
        return self.results
    
    def save_results(self, filename: str = "pipeline_results.json"):
        """Save pipeline results and feedback data"""
        output = {
            "execution_timestamp": datetime.now().isoformat(),
            "total_tickets_processed": len(self.results),
            "results": [
                {
                    "ticket_id": r.ticket_id,
                    "classification_confidence": r.classification_confidence,
                    "classification_category": r.classification_category,
                    "routing_decision": r.routing_decision,
                    "is_escalation": r.is_escalation,
                    "response_quality_score": r.response_quality_score,
                    "agent_feedback": r.agent_feedback,
                    "feedback_timestamp": r.feedback_timestamp,
                }
                for r in self.results
            ],
            "feedback_summary": {
                "total_feedback_entries": len(self.feedback_data),
                "acceptance_rate": sum(1 for f in self.feedback_data if f["feedback"] == "accepted") / len(self.feedback_data) if self.feedback_data else 0,
                "edit_rate": sum(1 for f in self.feedback_data if f["feedback"] == "edited") / len(self.feedback_data) if self.feedback_data else 0,
                "rejection_rate": sum(1 for f in self.feedback_data if f["feedback"] == "rejected") / len(self.feedback_data) if self.feedback_data else 0,
            }
        }
        
        with open(filename, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"[SAVE] Results saved to {filename}")


if __name__ == "__main__":
    print("="*60)
    print("SYNTHETIC TICKET GENERATOR + PIPELINE RUNNER")
    print("="*60)
    
    # Generate synthetic tickets
    print("\n[GENERATION] Creating synthetic tickets...")
    generator = SyntheticTicketGenerator()
    tickets = generator.generate_batch(count=50)
    
    print(f"[GENERATION] Generated {len(tickets)} tickets")
    print(f"  Sample categories: {', '.join(set(t.category for t in tickets[:5]))}")
    print(f"  Sample tones: {', '.join(set(t.tone for t in tickets[:5]))}")
    
    # Run through pipeline
    print("\n[PIPELINE] Starting triage pipeline...")
    runner = PipelineRunner()
    results = runner.run_pipeline(tickets)
    
    # Save results
    runner.save_results("data/pipeline_results.json")
    
    # Print summary
    print("\n[SUMMARY]")
    print(f"  Acceptance rate: {runner.feedback_data.count({'feedback': 'accepted'}) if runner.feedback_data else 0 / len(runner.feedback_data) if runner.feedback_data else 'N/A':.1%}")
    print(f"  Escalation rate: {sum(1 for r in results if r.is_escalation) / len(results):.1%}")
    print(f"  Avg confidence: {sum(r.classification_confidence for r in results) / len(results):.2f}")
    print(f"  Avg quality: {sum(r.response_quality_score for r in results) / len(results):.2f}")
