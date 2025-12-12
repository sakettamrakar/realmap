# User Guide

**Version:** 1.0.0
**Date:** 2025-12-12

---

## 1. Getting Started

### Prerequisites
- Backend API running on `http://localhost:8000`.
- Frontend running on `http://localhost:5173`.

### Launching the App
```bash
cd frontend
npm run dev
# Open http://localhost:5173
```

---

## 2. Web Application Usage

### Home Screen (Map + List)
- **Map:** Drag and zoom to explore. Pins represent projects. Color indicates Score (Green=High, Red=Low).
- **List:** Shows projects in the current map view (if "Sync" is enabled).
- **Search:** Use the top bar to search by Project Name or Builder.

### Filters
- **Location:** Filter by District or Tehsil.
- **Budget:** Use the slider to set Min/Max price.
- **Score:** Filter for projects with >80 Quality Score.
- **Verified:** Toggle "RERA Verified" to see only official listings.

### Project Details
Click any card or pin to open the Detail View:
- **Overview:** Key dates, RERA ID, Promoter.
- **Scores:** Detailed breakdown of Connectivity, Lifestyle, etc.
- **Documents:** Download approved brochures and certificates.

---

## 3. Mobile Experience

The mobile interface is optimized for touch and on-the-go usage.

### Navigation
- **Home:** Map-centric search.
- **Check:** Run a quick compliance check on a project.
- **Compare:** Compare saved projects side-by-side.
- **Saved:** Access your shortlisted properties.

### Compliance Overlay
1. Tap the **Check** FAB (Floating Action Button).
2. Follow the steps: Validate RERA ID -> Check Location -> Review Litigation.
3. Get a "Safe/Unsafe" recommendation.

---

## 4. Analyst Workflows

**For Data Teams & Analysts:**
1. **Quality Check:** Use the "Data Quality" dashboard to find projects with missing lat/lon.
2. **Price Trends:** Access the `/analytics` view to see price history charts for specific districts.
3. **Exports:** Admin users can export search results to CSV for offline analysis.

---

## 5. Troubleshooting Common Issues
- **"Map not loading":** Check internet connection (OpenStreetMap requires access).
- **"No projects found":** Try widening your budget filter or zooming out on the map.
- **"API Error":** Ensure the backend server is running (`python -m ai.main` or `uvicorn`).

---

## 6. Related Documents
- [Functional Specification](../01-functional/Functional_Specification.md)
- [Operations Manual](../04-operations/Operations_Manual.md)
