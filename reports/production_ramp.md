# Production Ramp Plan

**Feature**: AI Scoring v1

## Schedule
- **Phase 1 (Canary)**: 5% Users. Duration: 24h.
- **Phase 2**: 25% Users. Duration: 24h.
- **Phase 3**: 50% Users. Duration: 24h.
- **Phase 4**: 100% Users.

## Checkpoint Rationale
- **Phase 1 -> 2**: Confirm latency stability.
- **Phase 2 -> 3**: Confirm DB load with increased writes to `ai_scores`.
- **Phase 3 -> 4**: Sales team sign-off on score quality.

## Post-Launch Review
Scheduled for: 2025-12-17
Attendees: Engineering, Product, Data Science.
