# Functional Specification

**Version:** 1.0.0  
**Status:** DRAFT  
**Date:** 2025-12-12  

---

## 1. Executive Summary

RealMap is an advanced real estate intelligence platform designed to ingest, normalize, and visualize Chhattisgarh RERA (CG RERA) project data. It solves the fragmentation and opacity of the regulatory real estate market by transforming raw, scraped data into a structured, queryable, and analytically rich dataset.

### Core Users
- **Home Buyers:** Searching for verified projects with specific amenities.
- **Analysts:** Tracking price trends and supply in emerging sectors.
- **Admin:** Monitoring ingestion health and data quality.

### Key Capabilities
- **Ingestion:** Automated full/delta scraping of RERA portal.
- **Enrichment:** Geospatial normalization, amenity scoring (0-100), AI-based feature extraction.
- **Discovery:** Map-based exploration, faceted search, and AI Chat Assistant.

---

## 2. User Interface & Experience

### Design Principles
- **Map-First Exploration:** High-contrast, interactive map with clustering.
- **Explicit Labeling:** Clear distinction between Carpet, Built-up, and Super Built-up areas.
- **Response Design:** Fully optimized for Mobile and Desktop.

### Desktop Components
- **Search Page:** Split view with Faceted Sidebar (Budget, BHK, Status) and Grid/Map results.
- **Project Detail Page:** Immersive hero section, "Snapshot" table, Radar chart for scores, and Deep Links to brochures.

### Mobile Experience
- **Navigation:** Bottom Tab Bar (Home, Check, Compare, Saved).
- **Compliance Flow:** Dedicated "Check Compliance" overlay with step-by-step verification.
- **Interactions:** Touch-optimized tap targets, bottom-sheet filters.

---

## 3. Detailed Functional Requirements

### 3.1 Listing & Search
- **Sidebar Filters:** Budget Range, BHK (1-5+), Status (Ready/Under Const), Tags (e.g., "Metro Connected").
- **Map Interaction:** "Search as I move" toggle. Pins distinguish "Exact" vs "Approximate" location.
- **Cards:** display Price Range, Configuration, and "RERA Verified" badges.

### 3.2 Project Detail View
- **Hero:** Main image, Builder Logo, Overall Score Badge.
- **Scores:** 5-point radar chart (Connectivity, Lifestyle, Safety, Environment, Investment).
- **Amenities:** Categorized grid (Health, Social, etc.) sourced from `amenity_taxonomy`.
- **Documents:** Access to brochures via a lead-capture gate (signed URLs).

### 3.3 AI Features
- **Chat Assistant:** Natural language search ("3BHK near AIIMS under 50L") utilizing `pgvector` and LLM synthesis.
- **Document Analysis:** Auto-extract "Completion Date" and "Litigation Status" from RERA PDFs.
- **Price Anomaly:** AI flags listings with suspicious price/sqft values.

### 3.4 Backend & Ingestion
- **Delta Scraping:** Skips existing records to run in <15 mins.
- **Geocoding:** Dual-provider (Nominatim/Google) with bounds checking (India only).
- **API:** REST endpoints for `search`, `details`, `analytics`, and `chat`.

---

## 4. Target UI Refactor (Future State)

The following improvements are planned for the next major UI overhaul:
- **Full Page Detail:** Move from side-panel to dedicated `/project/:id` route.
- **Value Badges:** "High/Medium/Low" value stickers based on AI estimation.
- **Comparisons:** Side-by-side comparison view for up to 3 projects.

---

## 5. Related Documents
- [User Guide](../01-functional/User_Guide.md) - How to use the application.
- [Architecture](../02-technical/Architecture.md) - System design and components.
- [API Reference](../02-technical/API_Reference.md) - Backend endpoints.
