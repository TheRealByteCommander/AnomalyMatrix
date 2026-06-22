# AnomalyMatrix — Product/Feature Ideation Pack (2026-03-03)

> **Umsetzungsstand (2026-06):** MVP v0.6.0 — Inspection-Pipeline, HMI, RBAC, Feedback, OPC-UA asyncua, Observability optional. Offen: echtes Training, E2E-Gates, Executive-Dashboards.

## Scope & Product Lens
**Product goal:** Reduce unplanned industrial downtime by detecting anomalies early, accelerating root-cause analysis, and operationalizing reliable response playbooks.

**Target users:**
- **Primary:** Plant operators, reliability engineers, maintenance teams
- **Secondary:** Plant managers, operations directors, corporate executives

**Buying context:** Industrial buyers value reliability, explainability, fast time-to-value, and measurable business outcomes (MTTR, OEE, scrap, energy, safety incidents).

---

## 1) Prioritized Feature Backlog (P1/P2/P3)

### P1 — Must-win (land-and-expand core)

1. **Hybrid Anomaly Detection Engine (Rules + ML + Baselines)**
   - **Business value:** Detects both known and unknown failure patterns; reduces missed incidents.
   - **Differentiation:** Combines deterministic trust (rules) with adaptive learning in one scoring pipeline.
   - **Impact KPI:** ↑ true positive rate, ↓ false negatives, ↓ unplanned downtime.

2. **Root-Cause Navigator (Signal Correlation Graph)**
   - **Business value:** Cuts diagnostic time by showing likely causal chains across sensors/assets.
   - **Differentiation:** Causality-oriented UX (not just alert lists), ranked hypotheses with confidence.
   - **Impact KPI:** ↓ MTTR, ↓ engineer-hours per incident.

3. **Operator Workbench + Actionable Alerting**
   - **Business value:** Converts anomaly alerts into clear next actions with SOP links and severity policies.
   - **Differentiation:** “Alert-to-action” workflow integrated in one pane.
   - **Impact KPI:** ↓ alert fatigue, ↑ response SLA adherence.

4. **Asset Health Timeline (Time Travel + Event Overlay)**
   - **Business value:** Fast reconstruction of “what changed before failure” across telemetry + maintenance + process states.
   - **Differentiation:** Unified timeline with cross-layer context (OT + CMMS events).
   - **Impact KPI:** ↓ investigation duration, ↑ repeatable postmortems.

5. **Rapid Onboarding Connectors (OPC UA, MQTT, Modbus, historian CSV/API)**
   - **Business value:** Shortens pilot setup from months to weeks.
   - **Differentiation:** Prebuilt industrial data profiles + mapping assistant.
   - **Impact KPI:** ↓ time-to-first-anomaly, ↑ pilot conversion.

6. **Model Governance & Explainability Card**
   - **Business value:** Improves trust/adoption in regulated and safety-critical environments.
   - **Differentiation:** Per-alert explanation card (top contributing signals, baseline drift, confidence).
   - **Impact KPI:** ↑ operator acceptance, ↑ action rate on ML alerts.

### P2 — Scale and stickiness

7. **Adaptive Thresholding by Shift/Season/Recipe**
   - **Business value:** Reduces false positives during normal but context-specific variance.
   - **Differentiation:** Context-aware baselines tuned by production mode.
   - **Impact KPI:** ↓ false positives, ↑ precision.

8. **Playbook Automation Engine (Semi-Automated Remediation)**
   - **Business value:** Standardizes response; reduces dependence on individual heroics.
   - **Differentiation:** Triggered runbooks with approval gates.
   - **Impact KPI:** ↓ response variance, ↓ repeat incidents.

9. **Multi-Site Fleet View + Benchmarking**
   - **Business value:** Enables corporate reliability teams to compare plants and replicate best practices.
   - **Differentiation:** Site-normalized health scoring and outlier ranking.
   - **Impact KPI:** ↑ cross-site performance consistency.

10. **Anomaly Replay Sandbox (What-if Simulation)**
    - **Business value:** Lets teams test thresholds/rules safely before production rollout.
    - **Differentiation:** Scenario replay with model/rule A-B comparison.
    - **Impact KPI:** ↓ bad config rollouts, ↑ deployment confidence.

11. **Maintenance System Integration (CMMS/ERP ticket sync)**
    - **Business value:** Closes loop from detection to work order completion.
    - **Differentiation:** Native feedback loop to improve future detection quality.
    - **Impact KPI:** ↑ closed-loop completion, ↓ repeat faults.

### P3 — Competitive edge & long-term moat

12. **Digital Twin-Assisted Anomaly Context**
    - **Business value:** Better interpretation of anomalies using process topology and dependencies.
    - **Differentiation:** Twin-enriched anomaly scoring and blast-radius estimation.
    - **Impact KPI:** ↑ diagnosis accuracy for complex systems.

13. **Prescriptive Optimization (Energy + Reliability Trade-off)**
    - **Business value:** Recommends setpoint/process adjustments balancing efficiency and risk.
    - **Differentiation:** Joint optimization, not single-objective monitoring.
    - **Impact KPI:** ↓ energy cost per unit, ↑ stable throughput.

14. **Supplier/Component Risk Fingerprint**
    - **Business value:** Identifies recurring anomaly signatures tied to vendor/component cohorts.
    - **Differentiation:** Procurement-grade reliability intelligence.
    - **Impact KPI:** ↓ lifecycle failure costs.

15. **Operator Copilot (Natural language diagnostics assistant)**
    - **Business value:** Makes complex diagnostics accessible to less experienced operators.
    - **Differentiation:** Grounded answers over plant-specific telemetry and playbooks.
    - **Impact KPI:** ↓ time to competent action, ↑ first-response quality.

---

## 2) Feature Packs

### 10 Delight Features for Operators

1. **First-Response Button:** One-click “Stabilize Line” macro with approved safe actions.
2. **Smart Alert Digest:** Merges duplicate/noisy alerts into one clear incident narrative.
3. **Confidence Meter:** Green/amber/red confidence with rationale in plain language.
4. **Shift Handoff Snapshot:** Auto-generated summary of anomalies, actions, unresolved risks.
5. **Personalized Watchlist:** Operators subscribe to critical assets and anomaly types.
6. **Contextual SOP Jump:** Every alert deep-links to exact SOP step and checklist.
7. **Noise Blackout Windows:** Suppress non-critical alert classes during maintenance windows.
8. **Visual Baseline Bands:** Instantly see deviation from expected envelope on trend charts.
9. **Incident Clipboard:** Capture timeline notes/screenshots quickly for postmortem.
10. **“Explain this spike” Shortcut:** One-click micro-analysis around selected chart region.

### 5 Executive/Reporting Features

1. **Downtime Avoidance Dashboard:** Quantified avoided losses by plant/line/asset.
2. **Reliability ROI Report:** MTTR, MTTF, OEE lift, scrap reduction, maintenance efficiency.
3. **Risk Heatmap by Business Unit:** Financial exposure and criticality-ranked anomaly clusters.
4. **Quarterly Reliability Narrative Pack:** Board-ready summary with trend commentary and actions.
5. **Program Maturity Scorecard:** Adoption depth, playbook compliance, model trust index.

---

## 3) Naming, Messaging & Value Proposition Draft

## Product Naming Options
1. **AnomalyMatrix Pulse** (core product)
2. **AnomalyMatrix Sentinel** (monitoring-focused SKU)
3. **AnomalyMatrix Resolve** (RCA + action workflow package)

## Positioning Statement
**For industrial operations teams who cannot afford unplanned downtime, AnomalyMatrix is an industrial anomaly intelligence platform that detects early risk, explains root causes, and guides fast corrective action — so plants stay stable, efficient, and audit-ready.**

## Value Proposition (Industrial Buyer)
- **Reduce downtime before it happens** with earlier and more precise anomaly detection.
- **Cut investigation and response time** with explainable root-cause guidance.
- **Operationalize reliability at scale** through playbooks, integrations, and fleet benchmarking.
- **Prove business impact** with executive-grade ROI reporting tied to operations KPIs.

## Messaging Pillars
1. **See Risk Earlier** — Catch subtle degradation before failure.
2. **Know Why Faster** — Explainability and causal context, not black-box alerts.
3. **Act with Confidence** — Guided response and governance for real-world operations.
4. **Scale Across Sites** — Repeatable reliability gains across plants and teams.

## Sample Taglines
- **“From anomaly to action in minutes, not shifts.”**
- **“Industrial reliability, engineered for decisions.”**
- **“Detect early. Explain clearly. Resolve faster.”**

---

## 4) UX/Design Suggestions (Complementing Hilde's Flow)

> Assumption: Hilde’s flow emphasizes rapid triage, human-in-the-loop decisions, and handoff clarity.

1. **Three-Zone Incident Layout**
   - Left: incident queue, middle: causal timeline, right: recommended actions/SOP.
   - Supports fast triage without context switching.

2. **Decision-Centric Alert Cards**
   - Card structure: What happened → Why likely → What to do now.
   - Keeps operator cognition focused on action, not raw data noise.

3. **Progressive Detail Layers**
   - Level 1: operational summary; Level 2: signal diagnostics; Level 3: model internals.
   - Serves both frontline operators and reliability experts.

4. **Handoff-by-Design**
   - Dedicated shift handoff mode with unresolved items, risk ranking, and acknowledgement states.

5. **Confidence + Consequence Pairing**
   - Every recommendation shows confidence and potential business consequence if ignored.

6. **Dark-Mode, High-Contrast, Control-Room-Ready UI**
   - Accessible palettes, keyboard-first interactions, large-hit targets for touch terminals.

7. **Timeline-Centric Navigation**
   - Time scrubber persists globally so users keep temporal context while switching tabs.

8. **Recovery-First Empty/Error States**
   - Always include next best action (reconnect source, remap tag, retrain baseline).

9. **Role-Aware Home Screens**
   - Operator view: active incidents + next actions.
   - Manager view: SLA, risk exposure, completion rates.

10. **Narrative Exports**
   - One-click export turns incident timeline into a clean postmortem narrative.

---

## 5) Practical Action Plan (Next 90 Days)

### Phase 1 (Weeks 1–4) — Prove Core Value
- Ship: Hybrid Detection, Operator Workbench, Asset Health Timeline, baseline explainability.
- Success criteria: pilot line live, measurable alert quality, first avoided incident evidence.

### Phase 2 (Weeks 5–8) — Operationalize
- Ship: CMMS sync, adaptive thresholds, shift handoff, executive downtime dashboard.
- Success criteria: reduced MTTR + documented response consistency.

### Phase 3 (Weeks 9–12) — Scale Differentiation
- Ship: fleet benchmarking, replay sandbox, prescriptive suggestions (limited scope).
- Success criteria: multi-site comparability + roadmap-ready expansion case.

---

## 6) Prioritization Snapshot for Aria

- **P1 now:** Detection quality + RCA speed + actionability + onboarding connectors.
- **P2 next:** Standardization, closed-loop maintenance, multi-site management.
- **P3 later:** Strategic moat (twin context, prescriptive optimization, copilot).

**Decision heuristic:** Prioritize items that simultaneously improve (1) incident prevention, (2) operator response speed, and (3) executive ROI visibility.
