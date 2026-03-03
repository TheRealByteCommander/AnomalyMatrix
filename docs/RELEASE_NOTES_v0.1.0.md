# AnomalyMatrix v0.1.0 – Release Notes

## Highlights
- MVP monorepo scaffold (backend, frontend, edge-acquisition, opcua-gateway, infra, scripts, tests, contracts)
- Phase 2 vertical flow integrated:
  - capture stub -> inference -> inspection result -> UI detail/trends
- Phase 3 real-path foundations:
  - pluggable inference provider interface
  - results query/trend-summary APIs
  - OPC-UA publish mapping integration point
- Product documentation packs and KPI/value planning
- Complete one-file installer package

## Included installer assets
- `AnomalyMatrix-installer.run`
- `AnomalyMatrix-installer-v0.1.0.run`

## Verification status
- PR gates merged into `master`
- CI green on merged Phase 3 branches before merge

## Install quickstart
```bash
./dist/AnomalyMatrix-installer-v0.1.0.run
```

## Notes
This is an MVP foundation release. Core data flow and platform scaffolding are in place; production hardening and real camera/model integrations continue in next iterations.
