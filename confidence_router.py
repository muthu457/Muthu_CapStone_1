"""
Confidence Routing Engine - Core HITL (Human-In-The-Loop) Pattern
Routes responses based on confidence scores and quality metrics
Integrates escalation detection for critical categories
"""
from typing import Optional, Dict, List
from datetime import datetime
from models import (
    ProposedResponse, 
    ConfidenceLevel, 
    ResponseQuality,
    TrustArchitectureConfig
)

# Import escalation detection
try:
    from escalation_map import EscalationRouter, EscalationCategory
    HAS_ESCALATION = True
except ImportError:
    HAS_ESCALATION = False


class ConfidenceRouter:
    """
    Routes responses to customers, reviewers, or escalation based on:
    - Confidence scores
    - Quality metrics
    - Trust architecture configuration
    - Staleness tracking
    """
    
    def __init__(self, config: Optional[TrustArchitectureConfig] = None):
        """Initialize with trust configuration"""
        self.config = config or TrustArchitectureConfig(last_modified=datetime.now())
        self.routing_log = []
        self.escalation_router = EscalationRouter() if HAS_ESCALATION else None
    
    def route_response(self,
                      proposed_response: ProposedResponse,
                      quality_level: Optional[ResponseQuality] = None,
                      model_staleness_days: int = 0,
                      kb_staleness_days: int = 0,
                      subject: str = "",
                      description: str = "") -> Dict:
        """
        Route a response based on confidence, quality, and staleness
        ALSO checks for critical escalation categories (VIP, cancellation, complaint, jurisdictional, legal/refund)
        
        Returns:
            {
                "routing_decision": "auto_send" | "review" | "escalate",
                "confidence_level": ConfidenceLevel,
                "quality_level": ResponseQuality,
                "is_critical_escalation": bool,
                "escalation_category": str or None,
                "escalation_reason": str or None,
                "reasons": [str],
                "priority": int,  # 1 (highest) to 5 (lowest)
                "timestamp": datetime
            }
        """
        
        reasons = []
        priority = 3  # Default medium priority
        confidence_level = proposed_response.confidence_level
        
        # FIRST: Check for critical escalation categories
        is_critical_escalation = False
        escalation_category = None
        escalation_reason = None
        
        if self.escalation_router and (subject or description):
            escalation_result = self.escalation_router.route_escalation(subject, description)
            if escalation_result.get("is_escalation"):
                is_critical_escalation = True
                escalation_category = escalation_result.get("escalation_category")
                escalation_reason = escalation_result.get("reason")
                reasons.append(f"CRITICAL ESCALATION: {escalation_reason}")
                reasons.append(f"Target Team: {escalation_result.get('target_team')}")
                reasons.append(f"SLA: {escalation_result.get('sla_minutes')} minutes")
                
                return {
                    "routing_decision": "escalate",
                    "confidence_level": confidence_level.value,
                    "quality_level": quality_level.value if quality_level else None,
                    "is_critical_escalation": True,
                    "escalation_category": escalation_category,
                    "escalation_reason": escalation_reason,
                    "escalation_severity": escalation_result.get("severity"),
                    "target_team": escalation_result.get("target_team"),
                    "sla_minutes": escalation_result.get("sla_minutes"),
                    "agent_notes": escalation_result.get("agent_notes"),
                    "reasons": reasons,
                    "priority": 1,  # Highest priority for escalations
                    "timestamp": datetime.now()
                }
        
        # Check staleness gates
        staleness_issues = []
        if model_staleness_days > self.config.max_model_age_days:
            staleness_issues.append(f"Classification model is {model_staleness_days} days old (limit: {self.config.max_model_age_days})")
        
        if kb_staleness_days > self.config.max_knowledge_base_age_days:
            staleness_issues.append(f"Knowledge base is {kb_staleness_days} days old (limit: {self.config.max_knowledge_base_age_days})")
        
        if staleness_issues:
            reasons.extend(staleness_issues)
        
        # Check quality gate
        quality_gate_passed = True
        if quality_level:
            quality_score = self._quality_to_score(quality_level)
            if quality_score < self.config.min_quality_score_for_send:
                quality_gate_passed = False
                reasons.append(f"Quality score {quality_score:.2f} below threshold {self.config.min_quality_score_for_send}")
        
        # Determine routing decision
        routing_decision = "review"  # Default
        
        if confidence_level == ConfidenceLevel.HIGH:
            if self.config.auto_send_high_confidence and quality_gate_passed and not staleness_issues:
                routing_decision = "auto_send"
                priority = 5  # Low priority - automated
                reasons.append("High confidence, good quality, models fresh")
            else:
                routing_decision = "review"
                priority = 2  # Higher priority for high-confidence anomalies
                reasons.append("High confidence but failed quality/staleness gate")
        
        elif confidence_level == ConfidenceLevel.MEDIUM:
            if self.config.require_review_medium:
                routing_decision = "review"
                priority = 3  # Medium priority
                reasons.append("Medium confidence requires agent review")
            elif quality_gate_passed:
                routing_decision = "auto_send"
                priority = 4
                reasons.append("Medium confidence but good quality, auto-sending")
            else:
                routing_decision = "review"
                priority = 3
                reasons.append("Medium confidence with quality concerns")
        
        else:  # LOW confidence
            if self.config.escalate_low_confidence:
                routing_decision = "escalate"
                priority = 1  # Highest priority - escalation
                reasons.append("Low confidence - escalating for human handling")
            else:
                routing_decision = "review"
                priority = 2
                reasons.append("Low confidence - requires review")
        
        decision = {
            "routing_decision": routing_decision,
            "confidence_level": confidence_level.value,
            "quality_level": quality_level.value if quality_level else "unknown",
            "reasons": reasons,
            "priority": priority,
            "timestamp": datetime.now(),
            "confidence_score": proposed_response.confidence,
            "quality_score": self._quality_to_score(quality_level) if quality_level else None
        }
        
        self.routing_log.append(decision)
        return decision
    
    def _quality_to_score(self, quality_level: Optional[ResponseQuality]) -> float:
        """Convert quality level to numeric score"""
        if not quality_level:
            return 0.5
        
        mapping = {
            ResponseQuality.EXCELLENT: 0.90,
            ResponseQuality.GOOD: 0.75,
            ResponseQuality.ACCEPTABLE: 0.62,
            ResponseQuality.POOR: 0.40
        }
        return mapping.get(quality_level, 0.5)
    
    def get_routing_stats(self) -> Dict:
        """Get statistics on routing decisions"""
        if not self.routing_log:
            return {"no_data": True}
        
        auto_send = len([r for r in self.routing_log if r["routing_decision"] == "auto_send"])
        review = len([r for r in self.routing_log if r["routing_decision"] == "review"])
        escalate = len([r for r in self.routing_log if r["routing_decision"] == "escalate"])
        total = len(self.routing_log)
        
        return {
            "total_routed": total,
            "auto_send": auto_send,
            "auto_send_rate": auto_send / total if total > 0 else 0,
            "review": review,
            "review_rate": review / total if total > 0 else 0,
            "escalate": escalate,
            "escalate_rate": escalate / total if total > 0 else 0,
            "avg_confidence": sum(r["confidence_score"] for r in self.routing_log) / total if total > 0 else 0
        }
    
    def update_config(self, **updates) -> TrustArchitectureConfig:
        """Update trust configuration"""
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        self.config.last_modified = datetime.now()
        return self.config
    
    def get_config(self) -> Dict:
        """Get current trust configuration"""
        return {
            "high_confidence_threshold": self.config.high_confidence_threshold,
            "medium_confidence_threshold": self.config.medium_confidence_threshold,
            "auto_send_high_confidence": self.config.auto_send_high_confidence,
            "require_review_medium": self.config.require_review_medium,
            "escalate_low_confidence": self.config.escalate_low_confidence,
            "min_quality_score_for_send": self.config.min_quality_score_for_send,
            "max_model_age_days": self.config.max_model_age_days,
            "max_knowledge_base_age_days": self.config.max_knowledge_base_age_days,
            "last_modified": self.config.last_modified.isoformat()
        }


# Global instance
_router = None


def get_confidence_router(config: Optional[TrustArchitectureConfig] = None) -> ConfidenceRouter:
    """Get or create the global confidence router instance"""
    global _router
    if _router is None:
        _router = ConfidenceRouter(config)
    return _router
