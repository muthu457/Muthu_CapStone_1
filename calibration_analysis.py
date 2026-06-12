"""
Confidence Calibration Analysis Tool

Analyzes the relationship between model confidence and actual accept/reject rates
Identifies systematic over-confidence and under-confidence
Generates calibration curves and recommendations
"""

import json
import statistics
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import math


@dataclass
class ConfidenceCalibrationBucket:
    """Data for a confidence range bucket"""
    confidence_range: str  # e.g., "0.80-0.90"
    min_confidence: float
    max_confidence: float
    count: int = 0
    accepted_count: int = 0
    edited_count: int = 0
    rejected_count: int = 0
    avg_quality: float = 0.0
    
    @property
    def acceptance_rate(self) -> float:
        if self.count == 0:
            return 0
        return self.accepted_count / self.count
    
    @property
    def rejection_rate(self) -> float:
        if self.count == 0:
            return 0
        return self.rejected_count / self.count
    
    @property
    def edit_rate(self) -> float:
        if self.count == 0:
            return 0
        return self.edited_count / self.count
    
    def to_dict(self) -> Dict:
        return {
            "confidence_range": self.confidence_range,
            "min_confidence": self.min_confidence,
            "max_confidence": self.max_confidence,
            "count": self.count,
            "acceptance_rate": self.acceptance_rate,
            "edit_rate": self.edit_rate,
            "rejection_rate": self.rejection_rate,
            "avg_quality": self.avg_quality,
        }


@dataclass
class CalibrationAnalysis:
    """Comprehensive calibration analysis results"""
    analysis_timestamp: str
    total_samples: int
    confidence_buckets: List[ConfidenceCalibrationBucket] = field(default_factory=list)
    
    # Statistics
    overall_acceptance_rate: float = 0.0
    overall_rejection_rate: float = 0.0
    overall_edit_rate: float = 0.0
    
    # Quality metrics
    quality_acceptance_correlation: float = 0.0
    confidence_acceptance_correlation: float = 0.0
    
    # Calibration issues
    over_confident_ranges: List[str] = field(default_factory=list)
    under_confident_ranges: List[str] = field(default_factory=list)
    well_calibrated_ranges: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "analysis_timestamp": self.analysis_timestamp,
            "total_samples": self.total_samples,
            "overall_acceptance_rate": self.overall_acceptance_rate,
            "overall_rejection_rate": self.overall_rejection_rate,
            "overall_edit_rate": self.overall_edit_rate,
            "quality_acceptance_correlation": self.quality_acceptance_correlation,
            "confidence_acceptance_correlation": self.confidence_acceptance_correlation,
            "confidence_buckets": [b.to_dict() for b in self.confidence_buckets],
            "over_confident_ranges": self.over_confident_ranges,
            "under_confident_ranges": self.under_confident_ranges,
            "well_calibrated_ranges": self.well_calibrated_ranges,
            "recommendations": self.recommendations,
        }


class ConfidenceCalibrationAnalyzer:
    """Analyzes model confidence calibration"""
    
    def __init__(self, bucket_size: float = 0.10):
        """
        Initialize analyzer
        bucket_size: Width of confidence ranges (0.10 = 10% buckets)
        """
        self.bucket_size = bucket_size
        self.buckets: Dict[str, ConfidenceCalibrationBucket] = {}
        self._initialize_buckets()
    
    def _initialize_buckets(self):
        """Create confidence buckets"""
        num_buckets = int(1.0 / self.bucket_size)
        for i in range(num_buckets):
            min_conf = i * self.bucket_size
            max_conf = (i + 1) * self.bucket_size
            range_label = f"{min_conf:.2f}-{max_conf:.2f}"
            self.buckets[range_label] = ConfidenceCalibrationBucket(
                confidence_range=range_label,
                min_confidence=min_conf,
                max_confidence=max_conf
            )
    
    def load_feedback_data(self, feedback_data: List[Dict]) -> None:
        """Load feedback data from pipeline results"""
        for entry in feedback_data:
            confidence = entry.get("confidence", 0)
            quality = entry.get("quality", 0)
            feedback = entry.get("feedback", "unknown")
            
            # Find bucket
            bucket_key = None
            for key, bucket in self.buckets.items():
                if bucket.min_confidence <= confidence < bucket.max_confidence:
                    bucket_key = key
                    break
            
            if bucket_key is None:
                continue
            
            bucket = self.buckets[bucket_key]
            bucket.count += 1
            
            if feedback == "accepted":
                bucket.accepted_count += 1
            elif feedback == "edited":
                bucket.edited_count += 1
            elif feedback == "rejected":
                bucket.rejected_count += 1
            
            bucket.avg_quality = (bucket.avg_quality * (bucket.count - 1) + quality) / bucket.count
    
    def analyze(self) -> CalibrationAnalysis:
        """Run full calibration analysis"""
        analysis = CalibrationAnalysis(
            analysis_timestamp=datetime.now().isoformat(),
            total_samples=sum(b.count for b in self.buckets.values())
        )
        
        # Populate buckets
        analysis.confidence_buckets = list(self.buckets.values())
        
        # Calculate overall rates
        total_count = analysis.total_samples
        if total_count > 0:
            analysis.overall_acceptance_rate = sum(b.accepted_count for b in self.buckets.values()) / total_count
            analysis.overall_rejection_rate = sum(b.rejected_count for b in self.buckets.values()) / total_count
            analysis.overall_edit_rate = sum(b.edited_count for b in self.buckets.values()) / total_count
        
        # Identify calibration issues
        self._identify_calibration_issues(analysis)
        
        # Generate recommendations
        self._generate_recommendations(analysis)
        
        return analysis
    
    def _identify_calibration_issues(self, analysis: CalibrationAnalysis) -> None:
        """Identify over-confident and under-confident ranges"""
        
        for bucket in analysis.confidence_buckets:
            if bucket.count == 0:
                continue
            
            # Expected acceptance rate at this confidence level should be close to the confidence itself
            expected_acceptance = (bucket.min_confidence + bucket.max_confidence) / 2
            actual_acceptance = bucket.acceptance_rate
            
            # Calculate deviation
            deviation = actual_acceptance - expected_acceptance
            
            # Classify
            if abs(deviation) < 0.10:  # Within 10% is well-calibrated
                analysis.well_calibrated_ranges.append(bucket.confidence_range)
            elif deviation < -0.15:  # Actual < Expected (over-confident)
                analysis.over_confident_ranges.append(
                    f"{bucket.confidence_range} (expected {expected_acceptance:.1%}, actual {actual_acceptance:.1%})"
                )
            elif deviation > 0.15:  # Actual > Expected (under-confident)
                analysis.under_confident_ranges.append(
                    f"{bucket.confidence_range} (expected {expected_acceptance:.1%}, actual {actual_acceptance:.1%})"
                )
    
    def _generate_recommendations(self, analysis: CalibrationAnalysis) -> None:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Over-confidence recommendations
        if analysis.over_confident_ranges:
            recommendations.append(
                f"OVER-CONFIDENCE DETECTED: {len(analysis.over_confident_ranges)} range(s) show higher rejection rates than expected. "
                f"Ranges: {', '.join(analysis.over_confident_ranges)}. "
                f"Action: Reduce confidence thresholds in these ranges or improve classifier accuracy."
            )
        
        # Under-confidence recommendations
        if analysis.under_confident_ranges:
            recommendations.append(
                f"UNDER-CONFIDENCE DETECTED: {len(analysis.under_confident_ranges)} range(s) show lower rejection rates than expected. "
                f"Ranges: {', '.join(analysis.under_confident_ranges)}. "
                f"Action: Consider raising routing thresholds to auto-send more responses in these ranges."
            )
        
        # High rejection rate
        if analysis.overall_rejection_rate > 0.20:
            recommendations.append(
                f"HIGH REJECTION RATE: {analysis.overall_rejection_rate:.1%} of responses rejected overall. "
                f"Action: Review classifier accuracy or knowledge base quality."
            )
        
        # High edit rate
        if analysis.overall_edit_rate > 0.40:
            recommendations.append(
                f"HIGH EDIT RATE: {analysis.overall_edit_rate:.1%} of responses edited by agents. "
                f"Action: Review prompt engineering, quality gate thresholds, or response template coverage."
            )
        
        # Low acceptance rate
        if analysis.overall_acceptance_rate < 0.50:
            recommendations.append(
                f"LOW ACCEPTANCE RATE: Only {analysis.overall_acceptance_rate:.1%} auto-accepted. "
                f"Action: Review RAGAS quality metrics, confidence calibration, and tone matching."
            )
        
        # Well-calibrated ranges
        if analysis.well_calibrated_ranges:
            recommendations.append(
                f"WELL-CALIBRATED: Confidence ranges {', '.join(analysis.well_calibrated_ranges)} are properly calibrated. "
                f"Use as baselines for comparison."
            )
        
        analysis.recommendations = recommendations
    
    def generate_report(self, analysis: CalibrationAnalysis) -> str:
        """Generate human-readable report"""
        lines = [
            "="*70,
            "CONFIDENCE CALIBRATION ANALYSIS REPORT",
            "="*70,
            "",
            f"Analysis Timestamp: {analysis.analysis_timestamp}",
            f"Total Samples: {analysis.total_samples}",
            "",
            "OVERALL METRICS",
            "-"*70,
            f"  Acceptance Rate: {analysis.overall_acceptance_rate:.1%}",
            f"  Edit Rate: {analysis.overall_edit_rate:.1%}",
            f"  Rejection Rate: {analysis.overall_rejection_rate:.1%}",
            "",
            "CONFIDENCE BUCKET ANALYSIS",
            "-"*70,
            "Range      | Count | Accept% | Edit%  | Reject% | Avg Quality",
            "-"*70,
        ]
        
        for bucket in analysis.confidence_buckets:
            if bucket.count > 0:
                lines.append(
                    f"{bucket.confidence_range} | {bucket.count:5d} | "
                    f"{bucket.acceptance_rate:6.1%} | {bucket.edit_rate:6.1%} | "
                    f"{bucket.rejection_rate:6.1%} | {bucket.avg_quality:.3f}"
                )
        
        lines.extend([
            "",
            "CALIBRATION ISSUES",
            "-"*70,
        ])
        
        if analysis.over_confident_ranges:
            lines.append("Over-Confident Ranges:")
            for r in analysis.over_confident_ranges:
                lines.append(f"  - {r}")
        
        if analysis.under_confident_ranges:
            lines.append("Under-Confident Ranges:")
            for r in analysis.under_confident_ranges:
                lines.append(f"  - {r}")
        
        if analysis.well_calibrated_ranges:
            lines.append("Well-Calibrated Ranges:")
            for r in analysis.well_calibrated_ranges:
                lines.append(f"  - {r}")
        
        lines.extend([
            "",
            "RECOMMENDATIONS",
            "-"*70,
        ])
        
        for i, rec in enumerate(analysis.recommendations, 1):
            lines.append(f"{i}. {rec}")
        
        lines.append("="*70)
        
        return "\n".join(lines)


if __name__ == "__main__":
    # Load pipeline results
    try:
        with open("data/pipeline_results.json", "r") as f:
            results = json.load(f)
    except FileNotFoundError:
        print("No pipeline results found. Run synthetic_pipeline.py first.")
        exit(1)
    
    # Extract feedback data
    feedback_data = []
    for r in results.get("results", []):
        feedback_data.append({
            "confidence": r.get("classification_confidence", 0),
            "quality": r.get("response_quality_score", 0),
            "feedback": r.get("agent_feedback", "pending")
        })
    
    # Run analysis
    analyzer = ConfidenceCalibrationAnalyzer(bucket_size=0.10)
    analyzer.load_feedback_data(feedback_data)
    analysis = analyzer.analyze()
    
    # Print report
    print(analyzer.generate_report(analysis))
    
    # Save detailed results
    with open("data/calibration_analysis.json", "w") as f:
        json.dump(analysis.to_dict(), f, indent=2)
    
    print(f"\nDetailed results saved to data/calibration_analysis.json")
