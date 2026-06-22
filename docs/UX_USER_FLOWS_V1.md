# UX User Flows v1 (Operator-first HMI)

> **Implementierungsstand v0.6.0:** Operator- und QA-Flows im HMI; Feedback (QA) auf Inspection Detail; RBAC-Rollen im Backend.

## Core personas
- Operator (line monitoring, quick decision)
- QA Lead (review anomalies, classify defect)
- Process Engineer (trend/drift diagnostics)

## Main flows
1. **Operator daily check**
   - Open Dashboard
   - Read status labels (green/amber/red)
   - Check latest inspection list
   - Escalate red to QA

2. **Inspection drill-down**
   - Open Inspection Detail
   - Review anomaly score + defect label
   - Trigger human validation workflow (future action)

3. **Trend review**
   - Open Trends
   - Scan threshold breaches
   - Mark process warning and notify engineer

4. **Configuration sanity check**
   - Open Configuration
   - Verify recipe/model/opc profile in read-only mode

## UX principles
- 3-second scannability
- color + text state labels together
- operator-safe read-only scaffold first
