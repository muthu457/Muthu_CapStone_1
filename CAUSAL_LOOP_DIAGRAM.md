# Causal Loop Diagram: Quality Feedback Cycle

## System Dynamics Overview

This diagram shows how feedback signals close the loop on quality and continuous improvement in the support triage system.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        QUALITY FEEDBACK LOOP SYSTEM                              │
└─────────────────────────────────────────────────────────────────────────────────┘


                           ┌──────────────────────┐
                           │   NEW TICKET ARRIVES │
                           └──────────┬───────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │  CLASSIFIER EVALUATES TICKET    │
                    │  (Rule-based with keywords)     │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  CONFIDENCE SCORE ASSIGNED  │  ◄──────┐
                    │  (0.0 - 1.0)                │         │
                    └──────────────┬──────────────┘         │
                                   │                        │
                    ┌──────────────▼──────────────┐         │
                    │  RAG RETRIEVES KNOWLEDGE    │         │
                    │  BASE ARTICLES              │         │
                    └──────────────┬──────────────┘         │
                                   │                        │
                    ┌──────────────▼──────────────┐         │
                    │  TONE-MATCHED RESPONSE      │         │
                    │  GENERATION                 │         │
                    └──────────────┬──────────────┘         │
                                   │                        │
                    ┌──────────────▼──────────────┐         │
                    │  RAGAS QUALITY SCORING      │         │
                    │  (Faithfulness,Relevance)   │         │
                    └──────────────┬──────────────┘         │
                                   │                        │
                    ┌──────────────▼──────────────┐         │
                    │  CONFIDENCE ROUTING DECISION│         │
                    │  - AUTO_SEND                │         │
                    │  - REVIEW                   │         │
                    │  - ESCALATE                 │         │
                    └──────────────┬──────────────┘         │
                                   │                        │
                ┌──────────────────┼──────────────────┐     │
                │                  │                  │     │
                ▼                  ▼                  ▼     │
        ┌────────────────┐  ┌────────────────┐ ┌─────────┐ │
        │ AUTO-SENT TO   │  │  HUMAN REVIEW  │ │ESCALATED│ │
        │ CUSTOMER       │  │   BY AGENT     │ │  TO VIP │ │
        │ (ROUTING=AUTO) │  │(ROUTING=REVIEW)│ │ SUPPORT │ │
        └────────┬───────┘  └────────┬───────┘ └────┬────┘ │
                 │                  │                │      │
                 │                  │     ┌─────────┘      │
                 │                  │     │                │
                 ▼                  ▼     ▼                │
        ┌────────────────────────────────────┐              │
        │  AGENT PROVIDES FEEDBACK           │              │
        │  ✓ ACCEPTED - Response was perfect │              │
        │  ✎ EDITED - Agent improved it      │              │
        │  ✗ REJECTED - Response was wrong   │              │
        └────────────────┬───────────────────┘              │
                         │                                   │
          ┌──────────────┼──────────────┐                   │
          │              │              │                   │
          ▼              ▼              ▼                   │
    [ACCEPTED]     [EDITED]         [REJECTED]             │
          │              │              │                   │
          │         ┌─────┴────┐        │                   │
          │         │          │        │                   │
          ▼         ▼          ▼        ▼                   │
    ┌─────────────────────────────────────┐                │
    │ FMEA FAILURE DETECTION              │                │
    │ (If Conf≥0.75 & (Edited|Rejected))  │                │
    │ → Log high-confidence failures      │                │
    └──────────────┬──────────────────────┘                │
                   │                                        │
                   ▼                                        │
    ┌──────────────────────────────────────┐              │
    │ QUALITY METRICS UPDATED              │              │
    │ - Acceptance rate by confidence      │              │
    │ - Rejection rate by category         │              │
    │ - Edit patterns by tone              │              │
    │ - RAGAS correlation                  │              │
    └──────────────┬───────────────────────┘              │
                   │                                       │
                   ▼                                       │
    ┌──────────────────────────────────────┐             │
    │ CALIBRATION ANALYSIS DETECTS ISSUES  │             │
    │ - Over-confident ranges              │             │
    │ - Under-confident ranges             │             │
    │ - Quality-confidence correlation     │             │
    └──────────────┬───────────────────────┘             │
                   │                                      │
          ┌────────┴───────────┐                         │
          │                    │                         │
          ▼                    ▼                         │
    [OVER-CONFIDENT]    [UNDER-CONFIDENT]               │
          │                    │                         │
          ▼                    ▼                         │
    - Lower            - Raise routing                   │
      confidence         thresholds                      │
      thresholds    - Auto-send more                     │
    - More human          responses                      │
      reviews        - Trust confidence                  │
    - Improve           more                            │
      classifier                                         │
          │                    │                         │
          └────────┬───────────┘                         │
                   │                                     │
                   ▼                                     │
    ┌──────────────────────────────────────┐            │
    │ TRUST ARCHITECTURE ADJUSTED           │            │
    │ (tunable_config.json)                │            │
    │ - Confidence thresholds updated      │            │
    │ - Quality gates modified              │            │
    │ - Routing policies refined            │            │
    │ - Auto-send % adjusted                │            │
    └──────────────┬───────────────────────┘            │
                   │                                     │
                   │  ◄─────────────────────────────────┘
                   │  (Loop closes: Next batch uses improved thresholds)
                   │
                   ▼
    ┌──────────────────────────────────────┐
    │ IMPROVED PERFORMANCE METRICS         │
    │ - Higher acceptance rate             │
    │ - Fewer escalations                  │
    │ - Better customer satisfaction       │
    │ - Smarter routing decisions          │
    └──────────────────────────────────────┘


REINFORCING LOOPS (↑ positive feedback):
═════════════════════════════════════════

Loop 1: Quality Virtuous Cycle
  Better Quality → More Accepted → Higher Confidence Warranted
  → Better Calibration → Better Routing → Better Quality

Loop 2: Learning Feedback
  More Feedback Data → Better Calibration → Better Thresholds
  → More Aligned Routing → Better Feedback Quality


BALANCING LOOPS (↔ corrective):
════════════════════════════════

Loop 1: Over-Confidence Correction
  Over-Confident → High Rejections → Lower Thresholds
  → More Review Required → Fewer False Auto-Sends

Loop 2: Under-Confidence Correction
  Under-Confident → Low Rejections → Raise Thresholds
  → More Auto-Sends → Optimal Throughput


KEY FEEDBACK SIGNALS:
═════════════════════

┌─────────────────────────────────────────────────────┐
│ 1. ACCEPTED (Positive)                              │
│    Signal: Classifier/Generator working well        │
│    Action: Maintain/increase confidence thresholds  │
│    Weight: +1 for calibration                       │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 2. EDITED (Mixed)                                   │
│    Signal: Close but not perfect                    │
│    Action: Review prompt templates, tone matching   │
│    Weight: +0.5 for calibration                     │
│    Learning: Store improved response for training   │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 3. REJECTED (Negative)                              │
│    Signal: Major failure in classification/response │
│    Action: Lower confidence, escalate similar cases │
│    Weight: -1 for calibration                       │
│    FMEA: Log failure mode for analysis              │
└─────────────────────────────────────────────────────┘


DELAY DYNAMICS:
════════════════

1. Response Delay (~200-500ms)
   Classifier → RAG → Prompt Engineering → Generation
   (Mostly eliminated via caching)

2. Feedback Collection Delay (~5-30 minutes)
   Agent reviews and provides feedback
   (Creates lag in signal)

3. Calibration Update Delay (~batch)
   New feedback → Analysis → Threshold adjustment
   (Tunable: immediate or nightly)

4. Impact Delay (~1-24 hours)
   New thresholds → Affects next batch of tickets
   (Visible in next day's metrics)


SYSTEM PROPERTIES:
═══════════════════

Stability: Stable with proper dampening (calibration prevents wild oscillation)
Response Time: Fast for immediate feedback, slower for trend detection
Learning: Continuous, incremental, data-driven
Robustness: Multiple feedback channels reduce single-point failure
Transparency: All decisions logged and explainable


EQUILIBRIUM POINT:
════════════════════

System naturally settles to:
  • Acceptance Rate: ~75-85% for high-confidence responses
  • Rejection Rate: ~5-10% (failures caught before customer)
  • Escalation Rate: ~10-15% (uncertain cases handled by humans)
  • Auto-Send Rate: ~60-70% (balancing speed and safety)

When feedback deviates, system adjusts thresholds to return to equilibrium.


METRICS DASHBOARD (Displays Every Hour):
═══════════════════════════════════════════

Last 1h:
  ✓ Acceptance Rate: 78%
  ✎ Edit Rate: 12%
  ✗ Rejection Rate: 10%
  ↑ Escalation %: 8%
  ◆ Avg Confidence: 0.72
  ◆ Avg Quality Score: 0.74
  ← Calibration Status: Well-calibrated

Last 24h:
  High-Confidence Buckets: Well-calibrated
  Mid-Confidence Buckets: Slightly over-confident (adjust thresholds down 5%)
  Low-Confidence Buckets: Under-confident (adjust thresholds up 3%)

FMEA Alerts:
  ⚠ Billing category showing 15% rejection rate (should be <5%)
  ⚠ Password-reset frustration tone: 20% edit rate
  → Review classifier accuracy for billing keywords

```

---

## Feedback Data Flow

```
┌─────────────────────────────────────┐
│ Agent Feedback                      │
└────────────────┬────────────────────┘
                 │
      ┌──────────┼──────────┐
      │          │          │
      ▼          ▼          ▼
  Accepted    Edited     Rejected
      │          │          │
      └──────────┼──────────┘
                 │
      ┌──────────▼──────────┐
      │ Store in feedback.  │
      │ json with:          │
      │ - ticket_id         │
      │ - feedback_type     │
      │ - original_response │
      │ - final_response    │
      │ - timestamp         │
      └──────────┬──────────┘
                 │
      ┌──────────▼──────────┐
      │ Trigger FMEA        │
      │ Analysis if:        │
      │ conf ≥ 0.75 &&      │
      │ (edited|rejected)   │
      └──────────┬──────────┘
                 │
      ┌──────────▼──────────┐
      │ Update Metrics:     │
      │ - Confidence bucket │
      │ - Category accuracy │
      │ - Tone effectiveness│
      │ - Quality score     │
      └──────────┬──────────┘
                 │
      ┌──────────▼──────────┐
      │ Recalculate         │
      │ Calibration Curve   │
      └──────────┬──────────┘
                 │
      ┌──────────▼──────────┐
      │ Generate            │
      │ Recommendations:    │
      │ - Threshold changes │
      │ - Process improvements
      │ - Training focus    │
      └──────────┬──────────┘
                 │
      ┌──────────▼──────────┐
      │ Apply Changes to    │
      │ trust_config.json   │
      │ (Automatic or       │
      │  Manual approval)   │
      └──────────┬──────────┘
                 │
      ┌──────────▼──────────┐
      │ Next Batch Uses     │
      │ Improved Thresholds │
      │ (Loop Closes!)      │
      └─────────────────────┘
```

---

## Example: How One Piece of Feedback Closes the Loop

**Scenario**: Mid-confidence billing response gets rejected

```
9:15 AM - TICKET ARRIVES
  ├─ Subject: "Double billing issue"
  ├─ Confidence: 0.72 (MEDIUM)
  └─ Quality: 0.68 (ACCEPTABLE)

9:15:30 AM - ROUTING DECISION
  ├─ Routing: REVIEW (due to MEDIUM confidence)
  ├─ Sent to Agent for Review
  └─ Reason: Confidence in MEDIUM band, requires human validation

9:20 AM - AGENT REVIEWS
  ├─ Agent reads proposed response
  ├─ Realizes: Response doesn't address refund possibility
  ├─ Decision: REJECTED (wrong approach)
  └─ Provides correct response with refund link

9:20:30 AM - FEEDBACK RECORDED
  ├─ Ticket Status: REJECTED
  ├─ Stored in feedback.json
  └─ FMEA Triggered (conf=0.72 ≥ 0.75? NO - not logged this time)

9:21 AM - BATCH CALIBRATION (hourly)
  ├─ 1000 tickets processed this hour
  ├─ Analysis finds: Billing category with 0.65-0.75 confidence has 20% rejection rate
  ├─ Expected: 70% acceptance at 0.70 confidence
  ├─ Actual: 50% acceptance
  └─ Verdict: OVER-CONFIDENT in this range

9:22 AM - RECOMMENDATION GENERATED
  ├─ Issue: "Billing classifier not distinguishing refund requests"
  ├─ Root Cause: Keyword matching misses specific refund language
  ├─ Recommendation: Lower confidence for billing tickets from 0.72 → 0.65
  └─ Effect: More will go to REVIEW, fewer to AUTO_SEND

9:25 AM - TRUST CONFIG UPDATED
  ├─ billing_confidence_threshold: 0.72 → 0.65
  ├─ Stored in trust_config.json
  ├─ Loaded by API automatically
  └─ All future billing tickets use new threshold

9:30 AM - NEXT TICKET (same type)
  ├─ Subject: "I was overcharged for the annual plan"
  ├─ Confidence: 0.69 (same as before, but classifier unchanged)
  ├─ Routing: REVIEW (uses new 0.65 threshold!)
  ├─ Agent reviews before sending
  └─ RESULT: Correct response sent, customer satisfied

═══════════════════════════════════════════════════════════════════
LOOP CLOSED: One rejection → Systematic improvement → Better outcomes

Loop time: ~15 minutes (automated calibration)
Impact: Prevents similar failures in future billing tickets
```

---

## Key Insights

1. **Feedback is Gold**: Every agent action trains the system
2. **Immediate Learning**: No batch retraining needed - thresholds adjust in real-time
3. **Explainability**: We know WHY each ticket routes where it does
4. **Self-Correcting**: Over-confidence automatically triggers review mode
5. **Scale**: System learns from 12,000+ tickets/week to refine routing
6. **No Divergence**: Calibration loop prevents catastrophic failures

