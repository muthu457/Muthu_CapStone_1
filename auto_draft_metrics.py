"""
Auto-Draft Metrics Tracker

Tracks:
1. Percentage of repetitive tickets auto-drafted (≥50% goal)
2. Acceptance rate of auto-drafted responses (≥80% goal)
3. Correlation between auto-draft rate and acceptance
4. Category-level auto-draft performance
"""

import json
from typing import List, Dict, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta


@dataclass
class TicketMetrics:
    """Metrics for a single ticket"""
    ticket_id: str
    category: str
    is_repetitive: bool  # Same category as prior ticket
    routing_decision: str  # auto_send / review / escalate
    agent_feedback: str  # accepted / edited / rejected / pending
    quality_score: float
    confidence: float
    timestamp: str


@dataclass
class AutoDraftReport:
    """Report on auto-draft performance"""
    analysis_timestamp: str
    
    # Overall metrics
    total_tickets: int = 0
    repetitive_tickets: int = 0
    auto_drafted: int = 0
    auto_draft_rate: float = 0.0  # % of repetitive tickets auto-drafted
    
    # Acceptance metrics
    accepted_count: int = 0
    edited_count: int = 0
    rejected_count: int = 0
    acceptance_rate: float = 0.0  # % of auto-drafted that were accepted
    
    # Goals
    auto_draft_goal: float = 0.50  # 50%
    acceptance_goal: float = 0.80  # 80%
    auto_draft_goal_met: bool = False
    acceptance_goal_met: bool = False
    
    # By category
    by_category: Dict = field(default_factory=dict)
    
    # Trend data
    trend_data: List[Dict] = field(default_factory=list)  # Hourly/daily trends
    
    def to_dict(self):
        return {
            "analysis_timestamp": self.analysis_timestamp,
            "total_tickets": self.total_tickets,
            "repetitive_tickets": self.repetitive_tickets,
            "auto_drafted": self.auto_drafted,
            "auto_draft_rate": self.auto_draft_rate,
            "auto_draft_goal_met": self.auto_draft_goal_met,
            "accepted_count": self.accepted_count,
            "edited_count": self.edited_count,
            "rejected_count": self.rejected_count,
            "acceptance_rate": self.acceptance_rate,
            "acceptance_goal_met": self.acceptance_goal_met,
            "by_category": self.by_category,
            "trend_data": self.trend_data,
            "status": {
                "auto_draft": f"{self.auto_draft_rate:.1%} (Goal: {self.auto_draft_goal:.0%}) {'✓' if self.auto_draft_goal_met else '✗'}",
                "acceptance": f"{self.acceptance_rate:.1%} (Goal: {self.acceptance_goal:.0%}) {'✓' if self.acceptance_goal_met else '✗'}"
            }
        }


class AutoDraftMetricsAnalyzer:
    """Analyzes auto-draft and acceptance metrics"""
    
    def __init__(self):
        self.tickets: List[TicketMetrics] = []
        self.previous_categories = defaultdict(int)  # Track category sequence
    
    def load_pipeline_results(self, tickets_filepath: str = "data/tickets.json", feedback_filepath: str = "data/feedback.json"):
        """Load real ticket and feedback data"""
        try:
            # Load tickets
            with open(tickets_filepath, "r") as f:
                tickets_data = json.load(f)
            
            # Load feedback
            with open(feedback_filepath, "r") as f:
                feedback_data = json.load(f)
            
            # Combine data
            for ticket_id, ticket_info in tickets_data.items():
                category = ticket_info.get("category", "unknown")
                is_repetitive = self.previous_categories[category] > 0
                self.previous_categories[category] += 1
                
                feedback = feedback_data.get(ticket_id, {})
                
                metrics = TicketMetrics(
                    ticket_id=ticket_id,
                    category=category,
                    is_repetitive=is_repetitive,
                    routing_decision=ticket_info.get("routing_decision", "unknown"),
                    agent_feedback=feedback.get("feedback_type", "pending"),
                    quality_score=ticket_info.get("response_quality_score", 0.5),
                    confidence=ticket_info.get("category_confidence", 0),
                    timestamp=ticket_info.get("created_at", datetime.now().isoformat())
                )
                self.tickets.append(metrics)
        
        except FileNotFoundError as e:
            print(f"No data found: {e}")
    
    def analyze(self) -> AutoDraftReport:
        """Generate auto-draft performance report"""
        report = AutoDraftReport(analysis_timestamp=datetime.now().isoformat())
        
        if not self.tickets:
            return report
        
        report.total_tickets = len(self.tickets)
        
        # Count repetitive tickets
        report.repetitive_tickets = sum(1 for t in self.tickets if t.is_repetitive)
        
        # Count auto-drafted from repetitive tickets
        auto_drafted_from_repetitive = [
            t for t in self.tickets 
            if t.is_repetitive and t.routing_decision == "auto_send"
        ]
        report.auto_drafted = len(auto_drafted_from_repetitive)
        
        # Calculate auto-draft rate (% of repetitive auto-drafted)
        if report.repetitive_tickets > 0:
            report.auto_draft_rate = report.auto_drafted / report.repetitive_tickets
        
        # Count acceptance/edit/rejection of auto-drafted
        report.accepted_count = sum(1 for t in auto_drafted_from_repetitive if t.agent_feedback == "accepted")
        report.edited_count = sum(1 for t in auto_drafted_from_repetitive if t.agent_feedback == "edited")
        report.rejected_count = sum(1 for t in auto_drafted_from_repetitive if t.agent_feedback == "rejected")
        
        # Calculate acceptance rate (% of auto-drafted that were accepted)
        if report.auto_drafted > 0:
            report.acceptance_rate = report.accepted_count / report.auto_drafted
        
        # Check if goals are met
        report.auto_draft_goal_met = report.auto_draft_rate >= report.auto_draft_goal
        report.acceptance_goal_met = report.acceptance_rate >= report.acceptance_goal
        
        # Analyze by category
        report.by_category = self._analyze_by_category(auto_drafted_from_repetitive)
        
        # Generate trend data
        report.trend_data = self._generate_trend_data()
        
        return report
    
    def _analyze_by_category(self, auto_drafted: List[TicketMetrics]) -> Dict:
        """Analyze auto-draft performance by category"""
        by_cat = defaultdict(lambda: {"total": 0, "accepted": 0, "edited": 0, "rejected": 0})
        
        for ticket in auto_drafted:
            cat = ticket.category
            by_cat[cat]["total"] += 1
            if ticket.agent_feedback == "accepted":
                by_cat[cat]["accepted"] += 1
            elif ticket.agent_feedback == "edited":
                by_cat[cat]["edited"] += 1
            elif ticket.agent_feedback == "rejected":
                by_cat[cat]["rejected"] += 1
        
        # Calculate rates
        result = {}
        for cat, counts in by_cat.items():
            total = counts["total"]
            result[cat] = {
                "total_auto_drafted": total,
                "acceptance_rate": counts["accepted"] / total if total > 0 else 0,
                "edit_rate": counts["edited"] / total if total > 0 else 0,
                "rejection_rate": counts["rejected"] / total if total > 0 else 0,
                "breakdown": counts
            }
        
        return result
    
    def _generate_trend_data(self) -> List[Dict]:
        """Generate time-series trend data"""
        trends = []
        
        # Group by time windows (simulated hourly)
        time_windows = defaultdict(list)
        for i, ticket in enumerate(self.tickets):
            window = i // 10  # Every 10 tickets = 1 "hour"
            time_windows[window].append(ticket)
        
        for window, tickets in sorted(time_windows.items()):
            auto_drafted = [t for t in tickets if t.is_repetitive and t.routing_decision == "auto_send"]
            if auto_drafted:
                accepted = sum(1 for t in auto_drafted if t.agent_feedback == "accepted")
                acceptance_rate = accepted / len(auto_drafted) if auto_drafted else 0
                
                trends.append({
                    "window": window,
                    "auto_drafted": len(auto_drafted),
                    "acceptance_rate": acceptance_rate,
                    "avg_quality": sum(t.quality_score for t in auto_drafted) / len(auto_drafted) if auto_drafted else 0,
                    "avg_confidence": sum(t.confidence for t in auto_drafted) / len(auto_drafted) if auto_drafted else 0,
                })
        
        return trends
    
    def generate_report(self, report: AutoDraftReport) -> str:
        """Generate human-readable report"""
        lines = [
            "=" * 80,
            "AUTO-DRAFT PERFORMANCE REPORT",
            "=" * 80,
            "",
            f"Analysis Timestamp: {report.analysis_timestamp}",
            f"Total Tickets Analyzed: {report.total_tickets}",
            "",
            "GOAL 1: AUTO-DRAFT RATE (≥50% of repetitive tickets)",
            "-" * 80,
            f"  Repetitive Tickets: {report.repetitive_tickets}",
            f"  Auto-Drafted: {report.auto_drafted}",
            f"  Auto-Draft Rate: {report.auto_draft_rate:.1%}",
            f"  Goal: {report.auto_draft_goal:.0%}",
            f"  Status: {'✓ GOAL MET' if report.auto_draft_goal_met else '✗ GOAL NOT MET'}",
            "",
            "GOAL 2: ACCEPTANCE RATE (≥80% of auto-drafted)",
            "-" * 80,
            f"  Auto-Drafted Responses: {report.auto_drafted}",
            f"  Accepted: {report.accepted_count} ({report.accepted_count/report.auto_drafted*100 if report.auto_drafted else 0:.1f}%)",
            f"  Edited: {report.edited_count} ({report.edited_count/report.auto_drafted*100 if report.auto_drafted else 0:.1f}%)",
            f"  Rejected: {report.rejected_count} ({report.rejected_count/report.auto_drafted*100 if report.auto_drafted else 0:.1f}%)",
            f"  Acceptance Rate: {report.acceptance_rate:.1%}",
            f"  Goal: {report.acceptance_goal:.0%}",
            f"  Status: {'✓ GOAL MET' if report.acceptance_goal_met else '✗ GOAL NOT MET'}",
            "",
            "BY CATEGORY PERFORMANCE",
            "-" * 80,
        ]
        
        for category, metrics in report.by_category.items():
            lines.append(f"\n  {category.upper()}:")
            lines.append(f"    Auto-Drafted: {metrics['total_auto_drafted']}")
            lines.append(f"    Acceptance Rate: {metrics['acceptance_rate']:.1%}")
            lines.append(f"    Edit Rate: {metrics['edit_rate']:.1%}")
            lines.append(f"    Rejection Rate: {metrics['rejection_rate']:.1%}")
        
        lines.extend([
            "",
            "TREND ANALYSIS (Time Windows)",
            "-" * 80,
            "Window | Auto-Drafted | Acceptance % | Avg Quality | Avg Confidence",
            "-" * 80,
        ])
        
        for trend in report.trend_data:
            lines.append(
                f"  {trend['window']:2d}    |     {trend['auto_drafted']:2d}       | "
                f"{trend['acceptance_rate']:6.1%}     | {trend['avg_quality']:.3f}      | {trend['avg_confidence']:.3f}"
            )
        
        lines.extend([
            "",
            "RECOMMENDATIONS",
            "-" * 80,
        ])
        
        recommendations = self._generate_recommendations(report)
        for rec in recommendations:
            lines.append(f"  • {rec}")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def _generate_recommendations(self, report: AutoDraftReport) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if not report.auto_draft_goal_met:
            recommendations.append(
                f"Auto-draft rate is {report.auto_draft_rate:.1%}, below 50% goal. "
                f"Consider lowering confidence thresholds to auto-send more repetitive tickets."
            )
        
        if not report.acceptance_goal_met:
            recommendations.append(
                f"Acceptance rate is {report.acceptance_rate:.1%}, below 80% goal. "
                f"Review rejected responses to improve quality or adjust confidence thresholds."
            )
        
        # Category-level recommendations
        for category, metrics in report.by_category.items():
            if metrics['rejection_rate'] > 0.15:
                recommendations.append(
                    f"{category}: High rejection rate ({metrics['rejection_rate']:.1%}). "
                    f"Consider improving templates or lowering auto-send threshold for this category."
                )
        
        if report.auto_draft_goal_met and report.acceptance_goal_met:
            recommendations.append(
                "✓ Both goals met! System is performing well. "
                "Monitor trends and adjust thresholds as feedback volume increases."
            )
        
        return recommendations


if __name__ == "__main__":
    analyzer = AutoDraftMetricsAnalyzer()
    analyzer.load_pipeline_results()
    report = analyzer.analyze()
    
    print(analyzer.generate_report(report))
    
    # Save report
    with open("data/auto_draft_report.json", "w") as f:
        json.dump(report.to_dict(), f, indent=2)
    
    print("\nReport saved to data/auto_draft_report.json")
