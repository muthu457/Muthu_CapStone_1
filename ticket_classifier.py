"""
Enhanced Ticket Classifier with confidence levels and classification results
Returns detailed classification with confidence levels for HITL routing
"""
import os
from datetime import datetime
from models import ClassificationResult, TicketCategory, ConfidenceLevel


class TicketClassifier:
    """Classify support tickets with confidence levels for routing"""
    
    def __init__(self):
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        self.classifier = None
        self.classifier_version = "2.0"
        
        self.categories = [
            TicketCategory.BILLING,
            TicketCategory.PASSWORD_RESET,
            TicketCategory.PLAN_CHANGE,
            TicketCategory.OTHER
        ]
    
    def classify_ticket(self, ticket_id: str, subject: str, description: str) -> ClassificationResult:
        """
        Classify a ticket into a category with confidence score
        Returns: ClassificationResult with category, confidence, and routing level
        """
        text = f"{subject}. {description}".lower()
        category, confidence = self._rule_based_classify(text)
        
        # Map confidence to level
        confidence_level = self._confidence_to_level(confidence)
        
        return ClassificationResult(
            ticket_id=ticket_id,
            category=category,
            confidence=confidence,
            confidence_level=confidence_level,
            classifier_version=self.classifier_version,
            classification_timestamp=datetime.now()
        )
    
    def _confidence_to_level(self, confidence: float) -> ConfidenceLevel:
        """Map confidence score to confidence level"""
        if confidence >= 0.80:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.60:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _rule_based_classify(self, text: str) -> tuple:
        """Rule-based classifier with enhanced confidence scoring"""
        text = text.lower()
        
        # Billing keywords with weights
        billing_keywords = {
            "charge": 0.9, "billing": 0.95, "invoice": 0.9, "payment": 0.85, 
            "refund": 0.95, "billed": 0.9, "charged": 0.9, "bill": 0.85, 
            "subscription fee": 0.95, "duplicate charge": 0.98
        }
        
        # Password/Login keywords
        password_keywords = {
            "password": 0.95, "login": 0.90, "access": 0.80, "reset": 0.90,
            "forgot": 0.95, "account locked": 0.95, "signin": 0.90, "sign in": 0.90,
            "log in": 0.90, "locked out": 0.95, "can't login": 0.95
        }
        
        # Plan change keywords
        plan_keywords = {
            "upgrade": 0.85, "downgrade": 0.85, "plan": 0.75, "change": 0.70,
            "switch": 0.80, "tier": 0.85, "subscription": 0.70, "premium": 0.75,
            "basic": 0.70, "pro": 0.75
        }
        
        # Calculate scores for each category
        billing_score = max([v for k, v in billing_keywords.items() if k in text], default=0)
        password_score = max([v for k, v in password_keywords.items() if k in text], default=0)
        plan_score = max([v for k, v in plan_keywords.items() if k in text], default=0)
        
        # Determine category and confidence
        if billing_score > 0:
            category = TicketCategory.BILLING
            confidence = billing_score
        elif password_score > 0:
            category = TicketCategory.PASSWORD_RESET
            confidence = password_score
        elif plan_score > 0:
            category = TicketCategory.PLAN_CHANGE
            confidence = plan_score
        else:
            category = TicketCategory.OTHER
            confidence = 0.5  # Default low confidence for uncategorized
        
        return category, confidence


if __name__ == "__main__":
    classifier = TicketClassifier()
    
    # Test with sample tickets
    test_tickets = [
        ("Billing Issue", "Why was I charged twice this month?"),
        ("Account Access", "I forgot my password and can't log in"),
        ("Plan Upgrade", "I want to upgrade to the premium plan"),
        ("Technical Issue", "The dashboard is loading slowly")
    ]
    
    for subject, desc in test_tickets:
        result = classifier.classify_ticket(subject, desc)
        print(f"Ticket: {subject}")
        print(f"Category: {result['category']} (confidence: {result['confidence']:.2f})")
        print()
