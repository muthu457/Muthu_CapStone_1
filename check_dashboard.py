#!/usr/bin/env python3
import json

data = json.load(open('data/drift_dashboard.json'))
metrics = data['current_metrics']

print(f"Total tickets: {metrics['total_tickets']}")
print(f"Acceptance rate: {metrics['acceptance_rate']:.1%}")
print(f"Rejection rate: {metrics['rejection_rate']:.1%}")
print(f"Edit rate: {metrics['edit_rate']:.1%}")
