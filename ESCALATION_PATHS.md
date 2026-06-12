# Clear Escalation Paths for Five Never-Auto Categories

## Overview

This document provides clear, step-by-step escalation paths for the 5 critical categories that **NEVER auto-respond**. Each has a dedicated team, SLA, and escalation process.

---

## Category 1: VIP (High-Value Customers)

### Detection
**Keywords**: vip, premium support, executive, c-level, account manager, enterprise, strategic  
**Confidence Threshold**: ≥0.70

### Escalation Path
```
Ticket Received
    ↓
[VIP Detection]
    ├─ Keywords matched in subject/description
    ├─ Confidence score calculated
    └─ Category: VIP
         ↓
[IMMEDIATE ESCALATION]
    ├─ Routing Decision: ESCALATE
    ├─ Priority: 1 (Highest)
    └─ Flag: CRITICAL - VIP CUSTOMER
         ↓
[ROUTE TO VIP SUPPORT TEAM]
    ├─ Team: Premium Support Team
    ├─ SLA: 30 minutes
    ├─ Response Type: Phone/Email (immediate)
    └─ Escalation Path: VIP Manager
         ↓
[AGENT ACTIONS]
    ├─ 1. Verify VIP status in database
    ├─ 2. Access premium support resources
    ├─ 3. Provide white-glove service
    ├─ 4. Offer premium support options
    ├─ 5. Document interaction in VIP history
    └─ 6. Schedule follow-up if needed
         ↓
[RESOLUTION]
    ├─ Direct resolution with VIP
    ├─ Priority handling of any issues
    └─ Executive follow-up if critical
```

### API Response
```json
{
  "is_critical_escalation": true,
  "escalation_category": "vip",
  "severity": "high",
  "target_team": "vip_support_team",
  "sla_minutes": 30,
  "routing_priority": 1,
  "agent_notes": "VIP Customer - Provide premium support. Offer immediate resolution options."
}
```

### Example Trigger
```
Subject: Account Issue
Description: "I'm a VIP customer and need immediate help with my premium subscription"
→ Confidence: 0.95
→ Team: VIP Support
→ SLA: 30 minutes
```

---

## Category 2: Cancellation Intent

### Detection
**Keywords**: cancel, unsubscribe, stop, don't want, remove me, quit, leave, discontinue, close account, delete account  
**Confidence Threshold**: ≥0.75

### Escalation Path
```
Ticket Received
    ↓
[CANCELLATION DETECTION]
    ├─ Keywords matched for cancellation language
    ├─ Sentiment analyzed (urgency level)
    └─ Category: CANCELLATION_INTENT
         ↓
[IMMEDIATE ESCALATION - RETENTION CRITICAL]
    ├─ Routing Decision: ESCALATE
    ├─ Priority: 1 (Highest)
    └─ Flag: RETENTION CRITICAL
         ↓
[ROUTE TO RETENTION SPECIALISTS]
    ├─ Team: Retention Specialists / Account Managers
    ├─ SLA: 15 minutes (immediate)
    ├─ Response Type: Phone call preferred
    └─ Escalation Path: Retention Manager
         ↓
[RETENTION SPECIALIST ACTIONS]
    ├─ 1. IMMEDIATELY contact customer (phone if possible)
    ├─ 2. Verify cancellation request (may be emotional)
    ├─ 3. Understand pain point (price, features, support)
    ├─ 4. Offer retention options:
    │   ├─ Plan downgrade to lower cost
    │   ├─ Temporary pause/freeze
    │   ├─ Loyalty discounts
    │   ├─ Feature upgrades
    │   └─ Executive support access
    ├─ 5. Escalate to VP/Executive if high-value
    ├─ 6. Document retention strategy
    └─ 7. Schedule follow-up call
         ↓
[RESOLUTION OUTCOMES]
    ├─ SUCCESS: Customer stays (document in CRM)
    ├─ PARTIAL: Downgraded or paused
    ├─ FAILED: Process cancellation professionally
    └─ FOLLOW-UP: Personal outreach in 30 days
```

### API Response
```json
{
  "is_critical_escalation": true,
  "escalation_category": "cancellation_intent",
  "severity": "high",
  "target_team": "retention_specialists",
  "sla_minutes": 15,
  "routing_priority": 1,
  "agent_notes": "RETENTION CRITICAL - Customer considering cancellation. Assess retention strategies immediately. Offer retention discounts if applicable."
}
```

### Example Trigger
```
Subject: Cancel My Account
Description: "I'm done with this service. Cancel immediately!"
→ Confidence: 0.95
→ Team: Retention Specialists
→ SLA: 15 minutes (PHONE CALL)
```

---

## Category 3: Complaint Escalation

### Detection
**Keywords**: terrible, horrible, worst, disgusted, outraged, livid, complaint, poor quality, never again, disappointed, unacceptable, pathetic, trash  
**Confidence Threshold**: ≥0.85

### Escalation Path
```
Ticket Received
    ↓
[COMPLAINT DETECTION]
    ├─ Strong negative sentiment detected
    ├─ Customer expressing high dissatisfaction
    └─ Category: COMPLAINT_ESCALATION
         ↓
[IMMEDIATE ESCALATION - HANDLE WITH CARE]
    ├─ Routing Decision: ESCALATE
    ├─ Priority: 1 (Highest)
    ├─ Severity: CRITICAL if confidence > 0.90
    └─ Flag: UPSET CUSTOMER - EMPATHY REQUIRED
         ↓
[ROUTE TO COMPLAINT MANAGEMENT TEAM]
    ├─ Team: Complaint Management / Support Lead
    ├─ SLA: 15-30 minutes
    ├─ Response Type: Phone/Video call recommended
    └─ Escalation Path: Support Manager → Director
         ↓
[SUPPORT TEAM ACTIONS]
    ├─ 1. IMMEDIATE empathetic response
    ├─ 2. Acknowledge customer's frustration
    ├─ 3. Apologize sincerely for negative experience
    ├─ 4. Listen without interrupting
    ├─ 5. Identify root cause of dissatisfaction
    ├─ 6. Offer immediate remediation:
    │   ├─ Service credits/refund
    │   ├─ Free upgrade/extension
    │   ├─ Direct access to specialist
    │   └─ Executive attention if needed
    ├─ 7. Document complaint in system
    ├─ 8. Create action plan for resolution
    └─ 9. Schedule follow-up (24-48 hours)
         ↓
[RESOLUTION]
    ├─ Implement promised remediation
    ├─ Personal follow-up by manager
    ├─ Verify customer satisfaction
    └─ Convert to promoter if possible
```

### API Response
```json
{
  "is_critical_escalation": true,
  "escalation_category": "complaint_escalation",
  "severity": "critical",
  "target_team": "complaint_management_team",
  "sla_minutes": 15,
  "routing_priority": 1,
  "agent_notes": "UPSET CUSTOMER - Handle with empathy. Acknowledge frustration. Provide immediate remediation. Consider goodwill gestures."
}
```

### Example Trigger
```
Subject: Your service is terrible
Description: "This is the worst experience ever! I'm absolutely disgusted!"
→ Confidence: 0.95
→ Severity: CRITICAL
→ Team: Complaint Management
→ SLA: 15 minutes (CALL)
```

---

## Category 4: Jurisdictional (Compliance/Legal Zones)

### Detection
**Keywords**: GDPR, CCPA, PCI-DSS, Europe, UK, EU, compliance, regulatory, jurisdiction, legal, counsel, attorney, data protection, privacy, California, regulation, multi-country, international  
**Confidence Threshold**: ≥0.75

### Escalation Path
```
Ticket Received
    ↓
[COMPLIANCE DETECTION]
    ├─ Regulatory/legal zone keywords detected
    ├─ Multi-jurisdiction implications identified
    └─ Category: JURISDICTIONAL
         ↓
[IMMEDIATE ESCALATION - LEGAL SENSITIVE]
    ├─ Routing Decision: ESCALATE
    ├─ Priority: 1 (Highest)
    └─ Flag: COMPLIANCE SENSITIVE - LEGAL REVIEW REQUIRED
         ↓
[ROUTE TO LEGAL COMPLIANCE TEAM]
    ├─ Team: Legal Compliance / Privacy Officer
    ├─ SLA: 30-60 minutes
    ├─ Response Type: Email (documented)
    └─ Escalation Path: Privacy Officer → General Counsel
         ↓
[LEGAL COMPLIANCE ACTIONS]
    ├─ 1. Review request for regulatory requirements
    ├─ 2. Verify applicable jurisdiction(s)
    ├─ 3. Check compliance obligations:
    │   ├─ GDPR (EU) - Art. 15 access rights
    │   ├─ CCPA (California) - disclosure obligations
    │   ├─ PIPEDA (Canada) - privacy protection
    │   ├─ PDPA (Singapore) - data protection
    │   └─ Other regional laws
    ├─ 4. Verify customer identity
    ├─ 5. Prepare compliant response
    ├─ 6. Document legal basis for actions
    ├─ 7. Set internal compliance deadline
    └─ 8. Send documented response
         ↓
[RESOLUTION]
    ├─ Provide legally compliant response
    ├─ Meet regulatory timeline (e.g., 30 days for GDPR)
    ├─ Document all compliance steps
    └─ Archive for audit purposes
```

### API Response
```json
{
  "is_critical_escalation": true,
  "escalation_category": "jurisdictional",
  "severity": "high",
  "target_team": "legal_compliance_team",
  "sla_minutes": 60,
  "routing_priority": 1,
  "agent_notes": "COMPLIANCE SENSITIVE - Verify applicable regulations. Consult legal team if needed. Document compliance steps carefully."
}
```

### Example Trigger
```
Subject: GDPR Data Request
Description: "I'm requesting my personal data under GDPR Article 15"
→ Confidence: 0.95
→ Team: Legal Compliance
→ SLA: 60 minutes (then 30-day response deadline)
```

---

## Category 5: Legal/Refund (Financial Liability)

### Detection
**Keywords**: refund, money back, reimbursement, chargeback, dispute, lawsuit, legal action, sue, attorney, breach, violation, liable, damage, loss, claim, financial  
**Confidence Threshold**: ≥0.80

### Escalation Path
```
Ticket Received
    ↓
[LEGAL/FINANCIAL DETECTION]
    ├─ Legal threat or refund demand detected
    ├─ Financial liability implications
    └─ Category: LEGAL_REFUND
         ↓
[IMMEDIATE ESCALATION - CRITICAL LEGAL]
    ├─ Routing Decision: ESCALATE
    ├─ Priority: 1 (Highest - IMMEDIATE)
    ├─ Severity: CRITICAL
    └─ Flag: DO NOT MAKE UNILATERAL DECISIONS
         ↓
[IMMEDIATE ROUTE TO LEGAL/FINANCE]
    ├─ Team: Legal/Finance Team + General Counsel
    ├─ SLA: 15 minutes (emergency contact)
    ├─ Response Type: Phone call + email
    └─ Escalation Path: General Counsel → CFO
         ↓
[LEGAL/FINANCE ACTIONS - URGENT]
    ├─ 1. IMMEDIATELY notify legal counsel
    ├─ 2. IMMEDIATELY notify finance/fraud team
    ├─ 3. Review customer account and history
    ├─ 4. Assess claim legitimacy:
    │   ├─ Valid service issue?
    │   ├─ Legitimate financial loss?
    │   ├─ Potential legal exposure?
    │   └─ Fraud or chargeback risk?
    ├─ 5. DO NOT admit liability or fault
    ├─ 6. DO NOT offer refund without approval
    ├─ 7. Prepare documented response
    ├─ 8. Consult external counsel if needed
    ├─ 9. Document all communications
    └─ 10. Establish case tracking file
         ↓
[RESOLUTION OPTIONS]
    ├─ OPTION 1: Refund approved (legal decision)
    │   └─ Process immediately with documentation
    ├─ OPTION 2: Partial resolution offered
    │   └─ Negotiate settlement
    ├─ OPTION 3: Dispute claim
    │   └─ Prepare legal defense
    └─ OPTION 4: Escalate to external counsel
        └─ Engage litigation team
```

### API Response
```json
{
  "is_critical_escalation": true,
  "escalation_category": "legal_refund",
  "severity": "critical",
  "target_team": "legal_finance_team",
  "sla_minutes": 15,
  "routing_priority": 1,
  "agent_notes": "CRITICAL: LEGAL/FINANCIAL - Escalate to legal/finance immediately. Do not make unilateral refund decisions. Document thoroughly."
}
```

### Example Trigger
```
Subject: Disputing charge - Legal action
Description: "I'm disputing this fraudulent charge and considering legal action"
→ Confidence: 0.95
→ Severity: CRITICAL
→ Team: Legal/Finance
→ SLA: 15 minutes
→ Action: DO NOT AUTO-RESPOND
```

---

## Escalation Decision Matrix

### Quick Reference

```
Priority | Category | Team | SLA | Key Action
---------|----------|------|-----|--------------------
   1     | VIP      | Premium | 30min | Premium Support
   1     | Cancel   | Retention | 15min | Phone Call (Retain)
   1     | Complaint| Complaint | 15min | Phone Call (Empathy)
   1     | Juris    | Legal | 60min | Verify Compliance
   1     | Legal    | Legal | 15min | DO NOT DECIDE
```

---

## API Integration

### Check if Escalation Needed
```bash
curl -X POST http://localhost:8000/escalations/detect \
  -d "subject=Your+Subject&description=Your+Description"
```

### Get All Escalation Statistics
```bash
curl http://localhost:8000/escalations/stats
```

### Response Structure
```json
{
  "is_escalation": true,
  "escalation_category": "category_name",
  "confidence": 0.95,
  "severity": "high|critical",
  "target_team": "team_name",
  "sla_minutes": 30,
  "agent_notes": "Detailed instructions for handling"
}
```

---

## Team Contact Information

### VIP Support Team
- **Contact**: vip-support@company.com
- **Phone**: 1-800-VIP-1111
- **Slack**: #vip-support
- **SLA**: 30 minutes
- **Hours**: 24/7

### Retention Specialists
- **Contact**: retention@company.com
- **Phone**: 1-800-KEEP-111
- **Slack**: #retention-team
- **SLA**: 15 minutes
- **Hours**: Business hours + emergency on-call

### Complaint Management Team
- **Contact**: complaints@company.com
- **Phone**: 1-800-CARE-111
- **Slack**: #complaint-management
- **SLA**: 15 minutes
- **Hours**: 24/7

### Legal Compliance Team
- **Contact**: legal@company.com
- **Phone**: 1-800-LEGAL-11
- **Slack**: #legal-compliance
- **SLA**: 60 minutes
- **Hours**: Business hours + emergency

### Legal/Finance Team
- **Contact**: legal-finance@company.com
- **Phone**: 1-800-URGENT-1
- **Slack**: #legal-finance (urgent)
- **SLA**: 15 minutes
- **Hours**: 24/7 emergency hotline

---

## Training & Monitoring

### For Support Team
1. ✓ Review all 5 escalation paths
2. ✓ Practice detection with examples
3. ✓ Memorize team contacts
4. ✓ Understand SLA requirements
5. ✓ Follow escalation process exactly

### Monitoring Metrics
- **Detection Accuracy**: % of real escalations correctly identified
- **SLA Adherence**: % of escalations routed within SLA
- **Team Response Time**: Average time to respond
- **Resolution Rate**: % resolved without further escalation

---

## Common Mistakes to Avoid

❌ **DON'T**: Auto-respond to any escalation category  
✓ **DO**: Always escalate and let team handle

❌ **DON'T**: Make refund decisions without legal approval  
✓ **DO**: Escalate financial requests immediately

❌ **DON'T**: Offer standard support to VIP/retention customers  
✓ **DO**: Provide premium/specialized service

❌ **DON'T**: Send generic response to upset customers  
✓ **DO**: Show empathy and take immediate action

❌ **DON'T**: Ignore compliance keywords  
✓ **DO**: Escalate any legal/regulatory indication

---

## Success Criteria

✓ **100% escalation** of the 5 categories (zero auto-responses)  
✓ **SLA compliance** for each team  
✓ **Customer satisfaction** in escalated cases  
✓ **No legal/compliance issues** due to auto-response  
✓ **Team readiness** for immediate handling  

System is designed to **NEVER auto-respond** to these critical categories while ensuring rapid specialist handling.

