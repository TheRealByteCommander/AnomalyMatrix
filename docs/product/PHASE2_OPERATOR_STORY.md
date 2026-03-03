# AnomalyMatrix Phase 2 — Operator Story (Capture → Detect → Review)

## Why this flow matters (operator value framing)

Operators don’t need “more dashboards.” They need a reliable rhythm that helps them act fast with confidence:

1. **Capture** the right signals without setup friction
2. **Detect** meaningful anomalies early (without noise overload)
3. **Review** incidents quickly and close the loop for the next shift

**Operator promise:**
- Less guesswork during stressful moments
- Faster decisions with clear next actions
- Better shift continuity and fewer repeat incidents

---

## Concise value framing by step

## 1) Capture
**Value:** Trustworthy input = trustworthy alerts.

- Standardized data intake from key asset signals and events
- Context tags (line, recipe, shift, maintenance window) attached automatically
- Signal quality checks to prevent garbage-in/garbage-out

**Operator outcome:** fewer false alarms from bad data and less manual context hunting.

## 2) Detect
**Value:** Spot risk early, not after downtime starts.

- Hybrid detection (baselines + known-pattern checks)
- Severity + confidence scoring in plain language
- Deduplicated incidents instead of fragmented alert storms

**Operator outcome:** a smaller, higher-quality queue that is actually actionable.

## 3) Review
**Value:** Resolve faster and improve future response quality.

- Incident timeline with key signal shifts and operator notes
- Root-cause hints with ranked likely contributors
- Shift handoff summary generated automatically

**Operator outcome:** shorter MTTR and stronger handoffs across teams.

---

## KPI hypotheses (to validate in next iteration)

1. **Alert Precision Lift**
   - Hypothesis: capture-context enrichment + detection dedup improves precision by **20–30%**.
   - Metric: confirmed actionable alerts / total alerts.

2. **MTTR Reduction**
   - Hypothesis: structured review timeline reduces MTTR by **15–25%**.
   - Metric: median time from incident open to closure.

3. **Handoff Quality Improvement**
   - Hypothesis: auto shift summary cuts unresolved carry-over incidents by **20%**.
   - Metric: % incidents requiring re-triage next shift.

4. **False Positive Reduction**
   - Hypothesis: signal quality gates + context-aware thresholds reduce false positives by **25%**.
   - Metric: dismissed alerts with “no action required” reason.

5. **Time-to-First-Action**
   - Hypothesis: clearer severity/confidence framing improves first action speed by **20%**.
   - Metric: median time from alert creation to first logged operator action.

6. **Operator Adoption Depth**
   - Hypothesis: better workflow coherence increases weekly active operators by **15%**.
   - Metric: WAU/eligible operators + feature usage per stage.

---

## 6 feature ideas for next iteration (Phase 2.x)

1. **Capture Health Score**
   - Real-time per-asset data quality score (missing tags, stale telemetry, drift warning).
   - Impact: prevents noisy detection caused by bad upstream capture.

2. **Incident Stitching Engine**
   - Automatically groups related alerts into one operator incident thread.
   - Impact: reduces alert fragmentation and cognitive load.

3. **Confidence-Aware Action Cards**
   - “Do now / Verify next / Escalate” guidance based on severity + confidence + asset criticality.
   - Impact: faster, safer first response.

4. **Review Replay Mode (5-minute digest)**
   - Compresses a full incident into a short sequence of key turning points.
   - Impact: accelerates post-incident understanding and training.

5. **Shift Handoff Co-Pilot**
   - Auto-drafts handoff message with unresolved risks, actions taken, and watch items.
   - Impact: fewer dropped details between shifts.

6. **Feedback-to-Model Loop**
   - Operator labels (true issue / false positive / maintenance-caused) directly tune detection profiles.
   - Impact: continuous precision improvements grounded in floor reality.

---

## Practical rollout notes

- Start with one critical line as reference implementation.
- Baseline current KPIs for 2–4 weeks before feature A/B rollout.
- Require closed-loop incident labeling to fuel model and rule improvements.
- Keep UI copy operational and action-first (“what to do now” over analytics jargon).

