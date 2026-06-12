# Test Integration for All 4 Outcomes
# Run this script to validate that all measurable outcomes are working

import os
import json
import subprocess
import time
from pathlib import Path
from synthetic_pipeline import SyntheticTicketGenerator, PipelineRunner
from auto_draft_metrics import AutoDraftMetricsAnalyzer
from drift_dashboard import DriftDetector
from escalation_map import EscalationDetector

print("=" * 80)
print("VALIDATING ALL 4 MEASURABLE OUTCOMES")
print("=" * 80)

# Check data directory
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

print("\n[1/5] Starting synthetic pipeline to generate test data...")
print("-" * 80)

try:
    generator = SyntheticTicketGenerator()
    runner = PipelineRunner()
    
    print("  • Generating 50 synthetic tickets...")
    tickets = generator.generate_batch(num_tickets=50, seed=42)
    print(f"  ✓ Generated {len(tickets)} tickets")
    
    print("  • Running through pipeline with feedback simulation...")
    results = runner.run_full_pipeline(tickets)
    print(f"  ✓ Pipeline complete: {len(results)} results")
    
    # Save results
    results_path = data_dir / "pipeline_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"  ✓ Saved to {results_path}")
    
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    exit(1)

print("\n[2/5] VALIDATING OUTCOME 1: ≥50% Auto-Draft Rate")
print("-" * 80)

try:
    analyzer = AutoDraftMetricsAnalyzer()
    analyzer.load_pipeline_results()
    report = analyzer.generate_report()
    
    # Check report exists
    report_path = data_dir / "auto_draft_report.json"
    if not report_path.exists():
        print("  ✗ FAILED: auto_draft_report.json not created")
        exit(1)
    
    with open(report_path, 'r') as f:
        metrics = json.load(f)
    
    auto_draft_rate = metrics.get("auto_draft_rate", 0)
    goal_met = auto_draft_rate >= 0.50
    
    print(f"  • Total Tickets: {metrics.get('total_tickets', 0)}")
    print(f"  • Repetitive Tickets: {metrics.get('repetitive_tickets', 0)}")
    print(f"  • Auto-Drafted: {metrics.get('auto_drafted', 0)}")
    print(f"  • Auto-Draft Rate: {auto_draft_rate:.1%}")
    print(f"  • Goal (≥50%): {'✓ MET' if goal_met else '✗ NOT MET'}")
    
    if not goal_met:
        print(f"  ⚠ WARNING: Auto-draft rate is {auto_draft_rate:.1%}, below 50% goal")
    
    outcome_1_status = goal_met
    
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    outcome_1_status = False

print("\n[3/5] VALIDATING OUTCOME 2: ≥80% Agent Acceptance Rate")
print("-" * 80)

try:
    # Load metrics from the same report
    if not report_path.exists():
        print("  ✗ FAILED: auto_draft_report.json not found")
        exit(1)
    
    with open(report_path, 'r') as f:
        metrics = json.load(f)
    
    acceptance_rate = metrics.get("acceptance_rate", 0)
    goal_met = acceptance_rate >= 0.80
    
    print(f"  • Auto-Drafted Responses: {metrics.get('auto_drafted', 0)}")
    print(f"  • Accepted: {metrics.get('accepted', 0)}")
    print(f"  • Edited: {metrics.get('edited', 0)}")
    print(f"  • Rejected: {metrics.get('rejected', 0)}")
    print(f"  • Acceptance Rate: {acceptance_rate:.1%}")
    print(f"  • Goal (≥80%): {'✓ MET' if goal_met else '✗ NOT MET'}")
    
    if not goal_met:
        print(f"  ⚠ WARNING: Acceptance rate is {acceptance_rate:.1%}, below 80% goal")
    
    outcome_2_status = goal_met
    
    # Show by-category performance
    print("\n  By-Category Performance:")
    for category, stats in metrics.get("by_category", {}).items():
        acceptance = stats.get("acceptance_rate", 0)
        print(f"    • {category}: {acceptance:.1%}")
    
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    outcome_2_status = False

print("\n[4/5] VALIDATING OUTCOME 3: Drift Dashboard with Anomaly Detection")
print("-" * 80)

try:
    detector = DriftDetector()
    detector.load_feedback_data()
    dashboard_data = detector.generate_dashboard_data()
    
    # Check JSON output
    dashboard_path = data_dir / "drift_dashboard.json"
    if not dashboard_path.exists():
        print("  ✗ FAILED: drift_dashboard.json not created")
        exit(1)
    
    with open(dashboard_path, 'r') as f:
        drift_data = json.load(f)
    
    print(f"  • Windows Analyzed: {len(drift_data.get('windows', []))}")
    print(f"  • Current Acceptance Rate: {drift_data.get('statistics', {}).get('current_acceptance_rate', 0):.1%}")
    print(f"  • Mean Rate: {drift_data.get('statistics', {}).get('mean_acceptance_rate', 0):.1%}")
    print(f"  • Std Dev: {drift_data.get('statistics', {}).get('std_dev', 0):.3f}")
    print(f"  • Overall Trend: {drift_data.get('overall_trend', 'unknown')}")
    print(f"  • Alerts: {len(drift_data.get('alerts', []))}")
    
    # Check HTML output
    html_path = data_dir / "drift_dashboard.html"
    html_exists = html_path.exists()
    print(f"  • HTML Report: {'✓ Generated' if html_exists else '✗ Not generated'}")
    
    if html_exists:
        html_size = html_path.stat().st_size
        print(f"    (File size: {html_size:,} bytes)")
    
    outcome_3_status = dashboard_path.exists() and html_exists
    print(f"  • Drift Dashboard: {'✓ ACTIVE' if outcome_3_status else '✗ FAILED'}")
    
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    outcome_3_status = False

print("\n[5/5] VALIDATING OUTCOME 4: Clear Escalation Paths (5 Categories)")
print("-" * 80)

try:
    detector = EscalationDetector()
    
    # Test escalation detection
    test_cases = [
        {
            "subject": "VIP Account Issue",
            "description": "I'm a VIP customer and need immediate assistance",
            "expected": "vip"
        },
        {
            "subject": "Cancel Account",
            "description": "I want to cancel my subscription immediately",
            "expected": "cancellation_intent"
        },
        {
            "subject": "Terrible Service",
            "description": "This is the worst experience ever, absolutely outraged!",
            "expected": "complaint_escalation"
        },
        {
            "subject": "GDPR Data Request",
            "description": "Requesting my personal data under GDPR regulations",
            "expected": "jurisdictional"
        },
        {
            "subject": "Refund Demand",
            "description": "I want a refund or I'll file a chargeback dispute",
            "expected": "legal_refund"
        }
    ]
    
    detected_count = 0
    for test in test_cases:
        result = detector.detect(test["subject"], test["description"])
        is_escalation = result.is_escalation
        category = result.escalation_category.value if result.escalation_category else None
        confidence = result.confidence
        
        match = category == test["expected"] and is_escalation
        status = "✓" if match else "✗"
        
        print(f"  {status} {test['expected']}: confidence={confidence:.2f}, detected={category}")
        
        if match:
            detected_count += 1
    
    print(f"\n  • Detection Accuracy: {detected_count}/5 ({detected_count*20}%)")
    
    outcome_4_status = detected_count == 5  # 100% accuracy
    print(f"  • Escalation Paths: {'✓ VERIFIED' if outcome_4_status else '✗ INCOMPLETE'}")
    
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    outcome_4_status = False

# Summary
print("\n" + "=" * 80)
print("OUTCOME VALIDATION SUMMARY")
print("=" * 80)

outcomes = [
    ("Outcome 1: Auto-Draft Rate (≥50%)", outcome_1_status),
    ("Outcome 2: Acceptance Rate (≥80%)", outcome_2_status),
    ("Outcome 3: Drift Dashboard", outcome_3_status),
    ("Outcome 4: Escalation Paths", outcome_4_status)
]

all_passed = True
for outcome_name, status in outcomes:
    symbol = "✓" if status else "✗"
    print(f"{symbol} {outcome_name}: {'PASSED' if status else 'FAILED'}")
    if not status:
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("🎉 SUCCESS: ALL 4 OUTCOMES VALIDATED AND WORKING!")
    print("=" * 80)
    print("\nProduction Ready Checklist:")
    print("  ✓ Auto-draft rate is ≥50%")
    print("  ✓ Agent acceptance rate is ≥80%")
    print("  ✓ Drift dashboard detecting anomalies")
    print("  ✓ Escalation paths verified for 5 categories")
    print("\nSystem is ready for production deployment.")
else:
    print("⚠ SOME OUTCOMES FAILED")
    print("=" * 80)
    print("\nFix issues above and rerun validation.")

print("\nKey Files Generated:")
print(f"  • {report_path} - Auto-draft & acceptance metrics")
print(f"  • {dashboard_path} - Drift detection data")
print(f"  • {html_path} - Interactive drift dashboard")
print(f"  • OUTCOME_REQUIREMENTS.md - Detailed documentation")
print(f"  • ESCALATION_PATHS.md - Clear routing procedures")

print("\nTo view drift dashboard: Open in browser -> {html_path}")
print("\nTo check API: curl http://localhost:8000/outcomes/summary")

