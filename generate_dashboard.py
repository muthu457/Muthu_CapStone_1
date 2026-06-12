#!/usr/bin/env python3
"""Generate dashboard files from real data"""

import json
from drift_dashboard import AcceptanceRateDashboard
from auto_draft_metrics import AutoDraftMetricsAnalyzer

print("Generating drift dashboard from real data...")
dashboard = AcceptanceRateDashboard()
dashboard.load_feedback_data()
data = dashboard.generate_dashboard_data()
dashboard.generate_html_report(data)
print("✓ Drift dashboard generated!")

print("\nGenerating auto-draft metrics from real data...")
a = AutoDraftMetricsAnalyzer()
a.load_pipeline_results()
report = a.analyze()
print("✓ Auto-draft metrics generated!")

print("\nAll dashboards ready with real data!")
print("- Drift: data/drift_dashboard.html")
print("- Metrics: data/auto_draft_report.json")
