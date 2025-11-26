# UI Refactor Specification: Realmap Upgrade

## 1. Current UI Overview

The current Realmap frontend is a **Single Page Application (SPA)** built with React, TypeScript, and Vite. It uses local state in `App.tsx` to manage views, without a client-side routing library (like `react-router-dom`).

- **Entry Point**: `src/App.tsx`
- **Main Layout**: A split-screen layout with a **Search Panel** (left) and a **Map View** (right).
- **Detail View**: A side panel (`ProjectDetailPanel`) that slides in/overlays when a project is selected.
- **State Management**: `App.tsx` holds all state (`filters`, `searchResults`, `selectedProject`, `mapPins`).
- **Styling**: Vanilla CSS in `src/styles.css`.

### Key Components
- `ProjectSearchPanel`: Contains both the filter controls and the list of project cards.
- `ProjectMapView`: Renders the map and pins.
- `ProjectDetailPanel`: Displays project details (Summary, Scores, Pricing, Amenities, Location).

---

## 2. Gap Analysis vs Target

| Feature | Current Implementation | Target "99acres-like" Experience | Gap / Action |
| :--- | :--- | :--- | :--- |
| **Layout** | Split Search/Map + Side Panel Detail | **Search Page**: Sidebar + List + Map.<br>**Detail Page**: Full-page immersive view. | **High**: Need to separate "Search View" and "Detail View" into distinct "pages" (even if virtual). |
| **Filters** | Mixed with list in `ProjectSearchPanel`. | Dedicated **Left Sidebar** for filters. | **High**: Extract filters into `FiltersSidebar`. |
| **Project Card** | Basic info (Name, Score, Price). | Rich Card: Name, Locality, Type, Price Band, **BHK Mix**, Scores, **Nearby POIs**, **Badges** (RERA, Promoter). | **High**: Redesign `ProjectCard` to include richer data and badges. |
| **Detail Hero** | Simple header in side panel. | **Hero Section**: Title, Locality, Price, Scores, Status, Quick Actions. | **High**: Create `ProjectHero` component. |
| **Detail Content** | Vertical sections in side panel. | **Snapshot Table**, **Score Deep-dive**, **Amenities Grid**, **Location Map**. | **Medium**: Refactor `ProjectDetailPanel` sections into standalone components. |
| **Scores** | Bar charts + simple values. | Score + "Why this score?" explanation + Value Badge. | **Low**: Logic exists, needs UI polish. |

---

## 3. Proposed Component Structure

We will retain the single-page architecture but structure components to act like distinct pages.

### A. `ProjectSearchPage` (The default view)
Layout: 3-column or 2-column with map.
*Suggestion: Sidebar (Filters) | List (Cards) | Map (Optional/Toggle)*

```tsx
<ProjectSearchPage>
  <FiltersSidebar>
    {/* Budget, Type, Status, Score Sliders */}
  </FiltersSidebar>
  
  <ProjectListPanel>
    <ProjectListHeader>
      {/* Sort Dropdown, Active Filter Chips, Total Count */}
    </ProjectListHeader>
    
    <ProjectList>
      <ProjectCard /> {/* Repeated */}
    </ProjectList>
  </ProjectListPanel>
  
  <MapPanel /> {/* Existing Map View */}
</ProjectSearchPage>
```

### B. `ProjectDetailPage` (The full-page view)
Replaces the Search Page content when a project is clicked.

```tsx
<ProjectDetailPage>
  <ProjectHero>
    {/* Title, Address, Price Range, Overall Score Badge, Status Tag, CTAs */}
  </ProjectHero>
  
  <ProjectSnapshot>
    {/* Table: RERA ID, Developer, Possession, Area, Units, Towers */}
  </ProjectSnapshot>
  
  <ScoreSummary>
    {/* 3 Main Scores (Overall, Location, Amenity) + Value Badge */}
    {/* "Why this score?" text/bullets */}
  </ScoreSummary>
  
  <AmenitiesSection>
    {/* Grid of icons/text for onsite amenities */}
  </AmenitiesSection>
  
  <LocationSection>
    {/* Map centered on project */}
    {/* Nearby POI counts (Schools, Hospitals) */}
  </LocationSection>
  
  <PriceSection>
    {/* Unit Mix Table (BHK, Area, Price) */}
  </PriceSection>
</ProjectDetailPage>
```

### Data Flow & Routing
- **Routing**: Continue using `App.tsx` state (`view` state: `'search' | 'detail'`).
- **Data**: 
    - `ProjectSearchPage` consumes `searchResults` and `filters`.
    - `ProjectDetailPage` consumes `selectedProject` (full detail fetched via `getProject`).

---

## 4. Feature Classification

### MANDATORY (Phase 1)
*Must be implemented to meet the core upgrade goal.*

1.  **Search Layout Refactor**: Move filters to a dedicated `FiltersSidebar`.
2.  **Filter Enhancements**:
    -   **Budget Filter**: Min/Max price inputs.
    -   **Project Type**: Checkboxes (Apartment, Plot, Commercial).
    -   **Status**: Checkboxes (Ready, Under Construction).
3.  **Project Card Redesign**:
    -   Show **BHK Mix** (e.g., "2, 3 BHK").
    -   Show **Price Band** (e.g., "₹45L - 1.2Cr").
    -   Show **RERA Verified** badge.
    -   Show top 2 nearby POIs (e.g., "2 Schools nearby").
4.  **Detail Page Transformation**:
    -   Convert Side Panel to **Full Page View**.
    -   Implement **Hero Section** with high-level summary.
    -   Implement **Snapshot Table** for quick facts.
    -   **Amenities Grid** (visual improvement over current list).

### GOOD TO HAVE (Phase 2)
*High value additions once core structure is stable.*

1.  **Value-for-Money Badge**: Display `High / Medium / Low` based on `value_score`.
2.  **"Why this score?"**: Bullet points for Pros/Cons (already in backend `score_explanation`).
3.  **Map Pin Distinction**: Different icons for "Exact" vs "Approximate" location.
4.  **Shortlist/Compare**: Polish the existing shortlist/compare UI to match the new design.

### OPTIONAL (Phase 3)
*Cosmetic or data-dependent features.*

1.  **Price Trends**: Visual graph (requires historical data).
2.  **Gallery**: Image carousel (if images become available).
3.  **Sticky Header**: For Detail page navigation.

---

## 5. Implementation Plan

1.  **Component Extraction (Refactor)**
    -   Create `src/components/search/FiltersSidebar.tsx`.
    -   Create `src/components/search/ProjectListHeader.tsx`.
    -   Move existing filter logic from `ProjectSearchPanel` to these new components.

2.  **Card Redesign**
    -   Update `ProjectCard.tsx`.
    -   Ensure it handles missing data gracefully (e.g., missing BHK mix).

3.  **Detail Page Construction**
    -   Create `src/components/detail/ProjectHero.tsx`.
    -   Create `src/components/detail/ProjectSnapshot.tsx`.
    -   Refactor `ProjectDetailPanel.tsx` into `ProjectDetailPage.tsx` using the new sub-components.

4.  **App Integration**
    -   Update `App.tsx` to toggle between `<ProjectSearchPage />` and `<ProjectDetailPage />` instead of opening a side panel.
    -   Ensure "Back" button in Detail Page restores Search Page state.

5.  **Styling Polish**
    -   Update `styles.css` (or add modules) to support the new layouts (Sidebar grid, Hero banner).
