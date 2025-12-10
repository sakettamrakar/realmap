# Canary Deployment Report

**Date**: 2025-12-10
**Status**: 🟡 PLANNED

## Metrics (Projected)
| Metric | Threshold | 6h Value | 24h Value | Status |
|--------|-----------|----------|-----------|--------|
| API Latency (p95) | < 2000ms | - | - | PENDING |
| Error Rate | < 1% | - | - | PENDING |
| Fallback Rate | < 5% | - | - | PENDING |
| Zero Scores | < 10% | - | - | PENDING |

## Plan
1. Deploy v1 to Canary Cluster (5% traffic).
2. Monitor strictly for 24h.
3. If green, promote to 25%.

## Rollback Trigger
Any metric violating threshold for > 15 mins triggers auto-rollback via `scripts/rollback_ai.sh`.
