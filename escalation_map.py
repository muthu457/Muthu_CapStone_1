"""
Escalation Map for 'Never Auto-Respond' Categories

These 5 critical categories ALWAYS escalate to human agents regardless of confidence:
1. VIP (high-value customers, premium support)
2. Cancellation Intent (retention-critical situations)
3. Complaint Escalation (customer expressing dissatisfaction)
4. Jurisdictional (multi-country, compliance, legal zone concerns)
5. Legal/Refund (financial liability, legal implications)
"""

from enum import Enum
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime


class EscalationCategory(str, Enum):
    """Critical escalation categories that bypass normal routing"""
    VIP = "vip"
    CANCELLATION_INTENT = "cancellation_intent"
    COMPLAINT_ESCALATION = "complaint_escalation"
    JURISDICTIONAL = "jurisdictional"
    LEGAL_REFUND = "legal_refund"


@dataclass
class EscalationDetection:
    """Result of escalation category detection"""
    escalation_category: EscalationCategory = None
    is_escalation: bool = False
    confidence: float = 0.0
    reason: str = ""
    severity: str = "normal"  # "critical", "high", "normal"
    agent_notes: str = ""


class EscalationDetector:
    """Detects if a ticket matches critical escalation categories"""
    
    def __init__(self):
        self.vip_keywords = {
            "vip": 0.95, "premium support": 0.95, "priority": 0.80,
            "executive": 0.90, "c-level": 0.95, "account manager": 0.85,
            "enterprise": 0.75, "strategic": 0.80, "valued customer": 0.85
        }
        
        self.cancellation_keywords = {
            "cancel": 0.90, "unsubscribe": 0.95, "stop": 0.80,
            "don't want": 0.85, "remove me": 0.90, "quit": 0.85,
            "leave": 0.75, "discontinue": 0.95, "termination": 0.95,
            "close account": 0.95, "delete account": 0.90
        }
        
        self.complaint_keywords = {
            "terrible": 0.95, "horrible": 0.95, "worst": 0.90,
            "disgusted": 0.95, "outraged": 0.95, "livid": 0.95,
            "complaint": 0.85, "poor quality": 0.80, "never again": 0.90,
            "disappointed": 0.75, "let down": 0.75, "fail": 0.70,
            "unacceptable": 0.90, "pathetic": 0.95, "trash": 0.90
        }
        
        self.jurisdictional_keywords = {
            "gdpr": 0.95, "ccpa": 0.95, "pci dss": 0.95,
            "europe": 0.60, "uk": 0.50, "eu": 0.60,
            "compliance": 0.80, "regulatory": 0.85, "jurisdiction": 0.90,
            "legal": 0.80, "counsel": 0.95, "attorney": 0.95,
            "data protection": 0.85, "privacy": 0.75, "california": 0.70,
            "regulation": 0.80, "multi-country": 0.90, "international": 0.70
        }
        
        self.legal_refund_keywords = {
            "refund": 0.90, "money back": 0.95, "reimbursement": 0.90,
            "chargeback": 0.95, "dispute": 0.90, "lawsuit": 0.95,
            "legal action": 0.95, "sue": 0.95, "attorney": 0.95,
            "breach": 0.95, "violation": 0.85, "liable": 0.95,
            "damage": 0.85, "loss": 0.70, "claim": 0.75,
            "financial": 0.60, "money": 0.60, "payment": 0.50
        }
    
    def detect(self, subject: str, description: str, customer_id: str = None) -> EscalationDetection:
        """
        Detect if ticket matches any escalation category
        Returns first match found (in priority order)
        """
        text = f"{subject} {description}".lower()
        
        # Check in priority order
        escalations = [
            (EscalationCategory.LEGAL_REFUND, self._check_legal_refund(text)),
            (EscalationCategory.JURISDICTIONAL, self._check_jurisdictional(text)),
            (EscalationCategory.COMPLAINT_ESCALATION, self._check_complaint(text)),
            (EscalationCategory.CANCELLATION_INTENT, self._check_cancellation(text)),
            (EscalationCategory.VIP, self._check_vip(text, customer_id)),
        ]
        
        for category, (is_match, confidence, reason) in escalations:
            if is_match:
                severity = self._determine_severity(category, confidence)
                return EscalationDetection(
                    escalation_category=category,
                    is_escalation=True,
                    confidence=confidence,
                    reason=reason,
                    severity=severity,
                    agent_notes=self._get_agent_notes(category, confidence)
                )
        
        return EscalationDetection(is_escalation=False)
    
    def _check_vip(self, text: str, customer_id: str = None) -> Tuple[bool, float, str]:
        """Check for VIP indicators"""
        score = max([v for k, v in self.vip_keywords.items() if k in text], default=0)
        if score > 0.70:
            return True, score, f"VIP customer detected (confidence: {score:.2f})"
        return False, 0, ""
    
    def _check_cancellation(self, text: str) -> Tuple[bool, float, str]:
        """Check for cancellation intent"""
        score = max([v for k, v in self.cancellation_keywords.items() if k in text], default=0)
        if score > 0.75:
            return True, score, f"Cancellation intent detected (confidence: {score:.2f})"
        return False, 0, ""
    
    def _check_complaint(self, text: str) -> Tuple[bool, float, str]:
        """Check for complaint escalation (strong negative sentiment)"""
        score = max([v for k, v in self.complaint_keywords.items() if k in text], default=0)
        if score > 0.85:
            return True, score, f"Complaint escalation detected (confidence: {score:.2f})"
        return False, 0, ""
    
    def _check_jurisdictional(self, text: str) -> Tuple[bool, float, str]:
        """Check for jurisdictional/compliance concerns"""
        score = max([v for k, v in self.jurisdictional_keywords.items() if k in text], default=0)
        if score > 0.75:
            return True, score, f"Jurisdictional concern detected (confidence: {score:.2f})"
        return False, 0, ""
    
    def _check_legal_refund(self, text: str) -> Tuple[bool, float, str]:
        """Check for legal/refund implications"""
        score = max([v for k, v in self.legal_refund_keywords.items() if k in text], default=0)
        if score > 0.80:
            return True, score, f"Legal/Refund case detected (confidence: {score:.2f})"
        return False, 0, ""
    
    def _determine_severity(self, category: EscalationCategory, confidence: float) -> str:
        """Determine severity level for routing"""
        if category == EscalationCategory.LEGAL_REFUND:
            return "critical"
        elif category == EscalationCategory.COMPLAINT_ESCALATION and confidence > 0.90:
            return "critical"
        elif category == EscalationCategory.JURISDICTIONAL and confidence > 0.85:
            return "high"
        else:
            return "high" if confidence > 0.85 else "normal"
    
    def _get_agent_notes(self, category: EscalationCategory, confidence: float) -> str:
        """Generate helpful notes for the agent"""
        notes = {
            EscalationCategory.VIP: "VIP Customer - Provide premium support. Offer immediate resolution options.",
            EscalationCategory.CANCELLATION_INTENT: "RETENTION CRITICAL - Customer considering cancellation. Assess retention strategies. Offer retention discounts if applicable.",
            EscalationCategory.COMPLAINT_ESCALATION: "UPSET CUSTOMER - Handle with empathy. Acknowledge frustration. Provide immediate remediation. Consider goodwill gestures.",
            EscalationCategory.JURISDICTIONAL: "COMPLIANCE SENSITIVE - Verify applicable regulations. Consult legal team if needed. Document compliance steps.",
            EscalationCategory.LEGAL_REFUND: "CRITICAL: LEGAL/FINANCIAL - Escalate to legal/finance immediately. Do not make unilateral refund decisions. Document thoroughly.",
        }
        base_note = notes.get(category, "")
        return f"{base_note} [Escalation confidence: {confidence:.2%}]"


class EscalationRouter:
    """Routes escalation cases to appropriate teams"""
    
    def __init__(self):
        self.detector = EscalationDetector()
        self.routing_map = {
            EscalationCategory.VIP: "vip_support_team",
            EscalationCategory.CANCELLATION_INTENT: "retention_specialists",
            EscalationCategory.COMPLAINT_ESCALATION: "complaint_management_team",
            EscalationCategory.JURISDICTIONAL: "legal_compliance_team",
            EscalationCategory.LEGAL_REFUND: "legal_finance_team",
        }
    
    def route_escalation(self, subject: str, description: str, 
                        customer_id: str = None) -> Dict:
        """Route an escalation to appropriate team"""
        detection = self.detector.detect(subject, description, customer_id)
        
        if not detection.is_escalation:
            return {
                "is_escalation": False,
                "requires_human_review": False,
                "routing_priority": "normal"
            }
        
        team = self.routing_map.get(detection.escalation_category, "default_support")
        
        return {
            "is_escalation": True,
            "requires_human_review": True,
            "escalation_category": detection.escalation_category.value,
            "severity": detection.severity,
            "target_team": team,
            "confidence": detection.confidence,
            "reason": detection.reason,
            "agent_notes": detection.agent_notes,
            "routing_priority": 1,  # Highest priority
            "sla_minutes": self._get_sla(detection.escalation_category, detection.severity),
        }
    
    def _get_sla(self, category: EscalationCategory, severity: str) -> int:
        """Get SLA in minutes for escalation"""
        slas = {
            (EscalationCategory.LEGAL_REFUND, "critical"): 15,
            (EscalationCategory.LEGAL_REFUND, "high"): 30,
            (EscalationCategory.COMPLAINT_ESCALATION, "critical"): 15,
            (EscalationCategory.COMPLAINT_ESCALATION, "high"): 30,
            (EscalationCategory.JURISDICTIONAL, "high"): 30,
            (EscalationCategory.JURISDICTIONAL, "normal"): 60,
            (EscalationCategory.CANCELLATION_INTENT, "high"): 15,
            (EscalationCategory.CANCELLATION_INTENT, "normal"): 30,
            (EscalationCategory.VIP, "normal"): 30,
        }
        return slas.get((category, severity), 120)


# Example usage
if __name__ == "__main__":
    router = EscalationRouter()
    
    test_cases = [
        ("Account Deletion", "I'm a VIP customer and want my entire account deleted immediately", "CUST_VIP_001"),
        ("Billing Complaint", "This is absolutely outrageous! I'm being charged for services I don't use!", None),
        ("Cancellation", "I want to cancel my subscription and get my money back", None),
        ("GDPR Request", "I'm requesting my data under GDPR Article 15", None),
        ("Legal Action", "I'm disputing this charge and considering legal action", None),
    ]
    
    for subject, desc, cust_id in test_cases:
        result = router.route_escalation(subject, desc, cust_id)
        print(f"\nTicket: {subject}")
        print(f"Escalation: {result['is_escalation']}")
        if result['is_escalation']:
            print(f"Category: {result['escalation_category']}")
            print(f"Team: {result['target_team']}")
            print(f"SLA: {result['sla_minutes']} minutes")
            print(f"Reason: {result['reason']}")
