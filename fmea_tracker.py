"""
FMEA (Failure Mode and Effects Analysis) Tracker
Logs high-confidence failures to identify failure modes and patterns
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from models import FMEAEntry, FeedbackType


class FMEATracker:
    """Track failure modes for high-confidence responses"""
    
    def __init__(self, storage_path: str = "./data/fmea_log.json"):
        self.storage_path = storage_path
        self.entries: List[FMEAEntry] = []
        self.load_from_disk()
    
    def log_failure(self,
                   ticket_id: str,
                   failure_mode: str,
                   confidence_at_time: float,
                   agent_feedback: FeedbackType,
                   severity: str,
                   root_cause: Optional[str] = None,
                   mitigation: Optional[str] = None) -> FMEAEntry:
        """Log a failure event"""
        
        entry = FMEAEntry(
            ticket_id=ticket_id,
            failure_mode=failure_mode,
            confidence_at_time=confidence_at_time,
            agent_feedback=agent_feedback,
            severity=severity,
            root_cause=root_cause,
            mitigation=mitigation,
            detected_at=datetime.now()
        )
        
        self.entries.append(entry)
        self.save_to_disk()
        return entry
    
    def detect_high_confidence_wrong_response(self,
                                             ticket_id: str,
                                             confidence: float,
                                             agent_feedback: FeedbackType) -> Optional[FMEAEntry]:
        """
        Detect when high-confidence response was wrong
        (agent rejected or significantly edited)
        """
        
        if confidence >= 0.75 and agent_feedback in [FeedbackType.REJECTED, FeedbackType.EDITED]:
            severity = "critical" if confidence >= 0.90 else "high"
            
            return self.log_failure(
                ticket_id=ticket_id,
                failure_mode="high_confidence_wrong_response",
                confidence_at_time=confidence,
                agent_feedback=agent_feedback,
                severity=severity,
                root_cause="Model overconfidence or misclassification"
            )
        
        return None
    
    def detect_misclassification(self,
                                ticket_id: str,
                                predicted_category: str,
                                actual_category: str,
                                confidence: float) -> Optional[FMEAEntry]:
        """Detect category misclassification"""
        
        if predicted_category != actual_category:
            return self.log_failure(
                ticket_id=ticket_id,
                failure_mode="misclassification",
                confidence_at_time=confidence,
                agent_feedback=FeedbackType.REJECTED,
                severity="high" if confidence > 0.7 else "medium",
                root_cause=f"Classified as {predicted_category} but was {actual_category}"
            )
        
        return None
    
    def get_failure_analysis(self, time_window_days: int = 30) -> Dict:
        """Analyze failures in a time window"""
        
        cutoff_time = datetime.now() - timedelta(days=time_window_days)
        recent_entries = [e for e in self.entries if e.detected_at >= cutoff_time]
        
        if not recent_entries:
            return {"no_data": True}
        
        # Group by failure mode
        failures_by_mode = {}
        for entry in recent_entries:
            mode = entry.failure_mode
            if mode not in failures_by_mode:
                failures_by_mode[mode] = []
            failures_by_mode[mode].append(entry)
        
        # Calculate statistics
        analysis = {
            "time_window_days": time_window_days,
            "total_failures": len(recent_entries),
            "failure_modes": {},
            "severity_distribution": {},
            "high_confidence_failures": 0,
            "avg_confidence_of_failures": 0
        }
        
        for mode, entries in failures_by_mode.items():
            analysis["failure_modes"][mode] = {
                "count": len(entries),
                "avg_confidence": sum(e.confidence_at_time for e in entries) / len(entries),
                "severity_breakdown": {
                    "critical": len([e for e in entries if e.severity == "critical"]),
                    "high": len([e for e in entries if e.severity == "high"]),
                    "medium": len([e for e in entries if e.severity == "medium"]),
                    "low": len([e for e in entries if e.severity == "low"])
                }
            }
        
        # Calculate severity distribution
        for entry in recent_entries:
            severity = entry.severity
            analysis["severity_distribution"][severity] = analysis["severity_distribution"].get(severity, 0) + 1
            
            if entry.confidence_at_time >= 0.75:
                analysis["high_confidence_failures"] += 1
        
        # Average confidence of failures
        analysis["avg_confidence_of_failures"] = (
            sum(e.confidence_at_time for e in recent_entries) / len(recent_entries)
        )
        
        return analysis
    
    def get_failure_trends(self, mode: Optional[str] = None) -> List[Dict]:
        """Get failure trends over time"""
        
        filtered_entries = self.entries
        if mode:
            filtered_entries = [e for e in self.entries if e.failure_mode == mode]
        
        # Group by day
        trends = {}
        for entry in filtered_entries:
            day = entry.detected_at.date()
            if day not in trends:
                trends[day] = {
                    "date": day.isoformat(),
                    "count": 0,
                    "avg_confidence": 0,
                    "critical_count": 0
                }
            
            trends[day]["count"] += 1
            trends[day]["avg_confidence"] = (
                (trends[day]["avg_confidence"] * (trends[day]["count"] - 1) + entry.confidence_at_time) / 
                trends[day]["count"]
            )
            
            if entry.severity == "critical":
                trends[day]["critical_count"] += 1
        
        return sorted(trends.values(), key=lambda x: x["date"])
    
    def get_high_risk_tickets(self, confidence_threshold: float = 0.80) -> List[Dict]:
        """Get tickets with high-confidence failures (risk analysis)"""
        
        high_risk = []
        for entry in self.entries:
            if entry.confidence_at_time >= confidence_threshold:
                high_risk.append({
                    "ticket_id": entry.ticket_id,
                    "failure_mode": entry.failure_mode,
                    "confidence": entry.confidence_at_time,
                    "severity": entry.severity,
                    "feedback": entry.agent_feedback.value,
                    "detected_at": entry.detected_at.isoformat()
                })
        
        return sorted(high_risk, key=lambda x: x["confidence"], reverse=True)
    
    def save_to_disk(self):
        """Persist FMEA log to disk"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        data = [
            {
                "ticket_id": e.ticket_id,
                "failure_mode": e.failure_mode,
                "confidence_at_time": e.confidence_at_time,
                "agent_feedback": e.agent_feedback.value,
                "severity": e.severity,
                "root_cause": e.root_cause,
                "mitigation": e.mitigation,
                "detected_at": e.detected_at.isoformat()
            }
            for e in self.entries
        ]
        
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def load_from_disk(self):
        """Load FMEA log from disk"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    self.entries = [
                        FMEAEntry(
                            ticket_id=e["ticket_id"],
                            failure_mode=e["failure_mode"],
                            confidence_at_time=e["confidence_at_time"],
                            agent_feedback=FeedbackType(e["agent_feedback"]),
                            severity=e["severity"],
                            root_cause=e.get("root_cause"),
                            mitigation=e.get("mitigation"),
                            detected_at=datetime.fromisoformat(e["detected_at"])
                        )
                        for e in data
                    ]
            except Exception as e:
                print(f"Error loading FMEA log: {e}")


# Global instance
_tracker = None


def get_fmea_tracker() -> FMEATracker:
    """Get or create the global FMEA tracker instance"""
    global _tracker
    if _tracker is None:
        _tracker = FMEATracker()
    return _tracker
