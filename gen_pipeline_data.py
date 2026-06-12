#!/usr/bin/env python3
"""Generate synthetic pipeline results"""

import json
import random
from datetime import datetime, timedelta

# Generate synthetic pipeline results
results = []
base_date = datetime.now() - timedelta(days=30)

# Simulate 60 tickets with varying acceptance rates
for i in range(60):
    ticket_date = base_date + timedelta(hours=i*8)
    
    # Vary acceptance rate to create some drift
    if i < 20:
        feedback = random.choices(['accepted', 'edited', 'rejected'], weights=[0.75, 0.15, 0.10])[0]
    elif i < 40:
        feedback = random.choices(['accepted', 'edited', 'rejected'], weights=[0.65, 0.20, 0.15])[0]
    else:
        feedback = random.choices(['accepted', 'edited', 'rejected'], weights=[0.70, 0.18, 0.12])[0]
    
    results.append({
        "ticket_id": f"TICKET_{i+1:03d}",
        "created_at": ticket_date.isoformat(),
        "category": random.choice(['billing', 'password_reset', 'account_issue', 'cancellation', 'plan_change']),
        "is_repetitive": random.choice([True, False]),
        "routing_decision": "auto_send" if random.random() > 0.3 else "escalate",
        "classification_confidence": round(random.uniform(0.65, 0.99), 3),
        "response_quality_score": round(random.uniform(0.60, 0.98), 3),
        "agent_feedback": feedback,
    })

# Save to file
output = {"results": results, "generated_at": datetime.now().isoformat()}
with open("data/pipeline_results.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print(f"✓ Generated {len(results)} pipeline results")
print(f"  - Acceptance rate: {sum(1 for r in results if r['agent_feedback'] == 'accepted') / len(results):.1%}")
print(f"  - Auto-drafted: {sum(1 for r in results if r['routing_decision'] == 'auto_send') / len(results):.1%}")
