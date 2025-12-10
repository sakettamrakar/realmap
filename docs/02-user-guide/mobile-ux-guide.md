# Mobile UX Guide

This guide summarizes the mobile-first UX patterns and components implemented in the frontend.

## Navigation

On small screens, navigation is driven by a bottom tab bar:

- **Home** – map + list experience tuned for mobile.
- **Check** – compliance or checklist-oriented flows.
- **Compare** – side-by-side comparison entry point.
- **Saved** – shortlisted projects.

The bottom navigation is implemented via dedicated mobile components in `frontend/src/components/mobile/` and integrated in `App.tsx` with a simple `activeTab` state.

## Compliance flow

A mobile-friendly compliance flow is exposed via a floating action button (FAB) and an animated overlay:

- Tapping the FAB opens a `ComplianceProgress` overlay.
- Steps guide the user through reading RERA details, checking location, and reviewing scores.
- On completion, the app routes back to the map with relevant filters applied.

## Shortlisting and saved projects

- Projects can be shortlisted directly from cards.
- The saved state is resilient to differences between string and numeric `project_id` representations.
- The **Saved** tab shows only shortlisted projects.

## Layout considerations

- Touch targets are sized appropriately for mobile.
- Map gestures and scroll behavior are tuned to avoid accidental panning or blocking key actions.
- Z-index and layering ensure interactive elements (e.g., shortlist buttons) remain tappable above overlays.

For exact components and implementation details, see:

- `frontend/src/components/mobile/BottomNav.tsx`
- `frontend/src/components/mobile/ComplianceProgress.tsx`
- `frontend/src/App.tsx`

For desktop layouts and broader UI design principles, see `web-app-usage.md` and `../03-engineering/code-structure.md`. 