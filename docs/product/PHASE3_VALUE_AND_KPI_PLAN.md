# AnomalyMatrix Phase 3 — Value & KPI Plan

> **Observability v0.5/v0.6:** `GET /observability/summary`, Influx-Metriken (optional), Dashboard-KPIs angebunden.

## Objective
Translate AnomalyMatrix capabilities into a measurable value system that operators, plant leaders, and executives can align on during the next sprint cycle.

---

## 1) KPI Tree (Outcome → Driver → Leading Indicators)

## North Star Outcome
**Reduced unplanned downtime with faster, higher-confidence incident resolution.**

## Level 1 Business Outcomes

1. **Availability & Throughput Improvement**
   - **Primary KPI:** Unplanned downtime hours per line/month
   - **Secondary KPI:** OEE availability component uplift

2. **Response Efficiency**
   - **Primary KPI:** MTTR (median + P75)
   - **Secondary KPI:** Time-to-first-action

3. **Alert Quality & Trust**
   - **Primary KPI:** Actionable alert ratio
   - **Secondary KPI:** False positive rate

4. **Reliability Program ROI**
   - **Primary KPI:** Avoided downtime cost (€)
   - **Secondary KPI:** Maintenance effort saved (hours), scrap avoided

## Level 2 Product Drivers

### A) Capture Quality
- Tag completeness rate
- Telemetry freshness SLA compliance
- % assets with healthy data score

### B) Detection Effectiveness
- Precision / recall on labeled incidents
- Duplicate alert compression rate
- Mean anomaly lead time before failure event

### C) Review & Resolution Quality
- % incidents with complete timeline narrative
- Root-cause confidence acceptance rate
- % incidents with closed feedback labels

### D) Operational Adoption
- Weekly active operators / eligible operators
- Shift handoff completion rate
- Playbook execution compliance

---

## 2) Rollout Narrative (Practical, real-path)

## Phase 3 story
Phase 3 is about turning strong detection into repeatable operational outcomes. We move from “we can detect anomalies” to “we consistently prevent losses and prove impact.”

### Narrative arc
1. **Stabilize signal-to-action loop**
   - Improve capture integrity and incident stitching to reduce noisy workflows.
2. **Operationalize response quality**
   - Standardize first-response and shift handoff to cut variability across teams.
3. **Institutionalize measurable value**
   - Tie every improvement to downtime, MTTR, and avoided cost dashboards.

### Rollout checkpoints
- **Checkpoint A (Week 1):** KPI baseline lock for target line(s)
- **Checkpoint B (Week 2):** Operator workflow enhancements live (capture + review)
- **Checkpoint C (Week 3):** Detection tuning loop active from operator feedback
- **Checkpoint D (Week 4):** Executive readout with quantified value trend

### Delivery principles
- Prioritize capabilities already supported by current architecture (real-path execution)
- Avoid speculative “moonshot” features in this sprint
- Every shipped item must map to at least one KPI driver

---

## 3) 8 High-Impact Feature Ideas for Next Sprint (real-path capabilities)

1. **Data Quality Guardrails Panel**
   - **What:** Live panel for stale tags, missing context tags, ingestion lag.
   - **Why high impact:** Immediate reduction in bad-input-driven alerts.
   - **KPI link:** Capture quality, false positive rate.

2. **Incident Stitching v2 (cross-signal grouping)**
   - **What:** Group temporally and causally related alerts into one incident thread.
   - **Why high impact:** Less queue noise, faster operator comprehension.
   - **KPI link:** Actionable alert ratio, time-to-first-action.

3. **Action Ladder in Alert Cards**
   - **What:** Structured “Now / Next / Escalate” actions with confidence and risk badges.
   - **Why high impact:** Standardizes first response under pressure.
   - **KPI link:** MTTR, response consistency.

4. **Shift Handoff Auto-Brief**
   - **What:** Auto-generated summary of open incidents, actions taken, pending risks.
   - **Why high impact:** Prevents context loss between teams.
   - **KPI link:** Handoff completion, re-triage rate.

5. **Label-to-Learning Feedback Loop**
   - **What:** Operator labels (true/false/maintenance-related) fed into threshold/model tuning workflow.
   - **Why high impact:** Continuous quality improvement with minimal friction.
   - **KPI link:** Precision, false positive rate.

6. **Timeline Replay Bookmarks**
   - **What:** Save and share key incident timestamps for training/postmortems.
   - **Why high impact:** Faster RCA collaboration and repeatable learning.
   - **KPI link:** MTTR, postmortem cycle time.

7. **CMMS Work-Order Linkback Enhancer**
   - **What:** Tighten incident-to-work-order mapping and closure feedback sync.
   - **Why high impact:** Closes detection-to-maintenance loop.
   - **KPI link:** Closed-loop completion, repeat fault rate.

8. **Value Tracker Widget (line-level)**
   - **What:** In-product widget estimating avoided downtime and response gains.
   - **Why high impact:** Makes value visible to both operators and management.
   - **KPI link:** ROI visibility, adoption depth.

---

## 4) Sprint KPI Targets (hypothesis range)

- **Actionable alert ratio:** +15% to +25%
- **False positive rate:** -20% to -30%
- **MTTR (median):** -10% to -20%
- **Time-to-first-action:** -15% to -25%
- **Shift handoff completion:** +20%

> Note: Treat as pilot hypotheses; confirm with baseline and weekly calibration.

---

## 5) Execution Checklist (concise)

- [ ] Lock baseline metrics for selected line(s)
- [ ] Ship features 1–4 first (operator impact core)
- [ ] Enable label feedback and weekly tuning cadence
- [ ] Validate CMMS loop closure data quality
- [ ] Publish weekly KPI delta to stakeholders
- [ ] Prepare end-of-sprint value narrative with evidence

