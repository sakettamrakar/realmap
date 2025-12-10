# Frontend Gap Analysis Report: 6-Point UX Standard (Points 18–23)

**Analysis Date:** December 2025  
**Auditor:** Senior Frontend Architect  
**Framework:** React + TypeScript (Vite)

---

## Executive Summary

| Point | Feature | Status | Gap Level |
|-------|---------|--------|-----------|
| 18 | Canonical Listing Page | 🟡 Partial | Medium |
| 19 | Area Transparency | 🔴 Missing | High |
| 20 | Normalized Comparison | 🟡 Partial | Medium |
| 21 | Smart Brochure Access | 🔴 Missing | High |
| 22 | Interactive Intelligence Map | 🟡 Partial | Medium |
| 23 | Transaction Insights | 🔴 Missing | High |

**Legend:** 🟢 Compliant | 🟡 Partial | 🔴 Missing

---

## Detailed Gap Analysis

### 18. Canonical Listing Page Template

**Requirement:** Standardized "Single Source of Truth" layout with 8 ordered sections.

**Current State:**
- ✅ Hero section exists (`ProjectHero.tsx`)
- ✅ Score Summary exists (`ScoreSummary.tsx`)
- ✅ Amenities Section exists (`AmenitiesSection.tsx`)
- ✅ Location Section with mini-map exists (`LocationSection.tsx`)
- ✅ Price Section exists (`PriceSection.tsx`)
- ❌ **Missing:** Tower > Unit hierarchy selector (Inventory)
- ❌ **Missing:** Floorplan gallery with unit type toggle
- ❌ **Missing:** Transaction History section (Intelligence)
- ❌ **Missing:** Price Trends visualization
- ❌ **Missing:** Reviews/Sentiment section
- ❌ **Wrong order:** Scores before Pricing (spec requires Pricing after Hero)

**Current Layout Order:**
```
1. Hero ✅
2. Snapshot (generic)
3. Score Summary
4. Amenities | Price (side-by-side)
5. Location
```

**Required Layout Order:**
```
1. Hero (Images + RERA ID + Developer Trust Score)
2. Price Matrix (Normalized pricing tables)
3. Inventory (Tower > Unit hierarchy)
4. Floorplans (Gallery with unit type toggle)
5. Amenities (Categorized + Lifestyle Score)
6. Map (Geospatial with isochrones)
7. Intelligence (Transaction History + Price Trends)
8. Reviews (Aggregated sentiment)
```

**Action Required:**
- [ ] Reorder sections in `ProjectDetailPanel.tsx`
- [ ] Create `InventorySection.tsx` (Tower > Unit selector)
- [ ] Create `FloorplanGallery.tsx`
- [ ] Create `IntelligenceSection.tsx` (Trends + Transactions)
- [ ] Add Developer Trust Score to Hero

---

### 19. Explicit Area Transparency (Compliance)

**Requirement:** Explicit labels next to every area figure.

**Current State:**
- ❌ `PriceSection.tsx` shows `Area (Sq.ft)` with no area type
- ❌ No distinction between carpet, builtup, super_builtup
- ❌ No tooltips or badges explaining area definitions
- ❌ No warning banner for mismatched area comparisons

**Evidence:**
```tsx
// PriceSection.tsx line 26
<th>Area (Sq.ft)</th>  // Generic, no area type specified
```

**Action Required:**
- [ ] Create `AreaLabel` component with badge + tooltip
- [ ] Update `PriceSection.tsx` to use area type from API
- [ ] Add `AreaComparisonWarning` banner component
- [ ] Consume `canonical_area_unit` from API response

---

### 20. Normalized Comparison Widgets

**Requirement:** `PriceComparisonWidget` plotting Project vs. Neighborhood with normalized `price_per_sqft_carpet`.

**Current State:**
- ✅ `CompareModal.tsx` exists with side-by-side comparison
- ❌ No chart/visualization (text only)
- ❌ No price normalization (raw values displayed)
- ❌ No neighborhood average comparison
- ❌ No handling of different area types between comparisons

**Evidence:**
```tsx
// CompareModal.tsx - shows raw scores, no price chart
<p className="value">{formatScore(project.scores?.overall_score)}</p>
```

**Action Required:**
- [ ] Create `PriceComparisonWidget.tsx` with chart visualization
- [ ] Implement area normalization logic
- [ ] Fetch neighborhood averages from `/analytics/price-trends`
- [ ] Add conversion factor warning for SBUA vs Carpet

---

### 21. Smart Brochure Access (Lead Gen)

**Requirement:** Smart Document component with OCR content, gated download, lead capture.

**Current State:**
- ❌ No brochure component exists
- ❌ No integration with `POST /access/brochure` API
- ❌ No lead capture form
- ❌ No OCR content display

**Action Required:**
- [ ] Create `SmartBrochure.tsx` component
- [ ] Implement `BrochureLeadForm.tsx` for lead capture
- [ ] Add integration with access API
- [ ] Show extracted text (public) vs PDF download (gated)

---

### 22. Interactive Intelligence Map

**Requirement:** Map with isochrones, POI markers, distance lines.

**Current State:**
- ✅ Basic Leaflet map in `LocationSection.tsx`
- ✅ Project marker displayed
- ✅ Nearby summary stats shown below map
- ❌ **Missing:** Isochrone polygons (travel time zones)
- ❌ **Missing:** POI markers on map
- ❌ **Missing:** Interactive POI sidebar
- ❌ **Missing:** Distance lines on hover

**Evidence:**
```tsx
// LocationSection.tsx - static marker only
<Marker position={[location.lat!, location.lon!]} icon={icon} />
// No isochrones, no POI layer
```

**Action Required:**
- [ ] Create `IsochroneMap.tsx` component
- [ ] Add isochrone polygon layer (15-min drive)
- [ ] Add POI markers from `social_infrastructure` data
- [ ] Create sidebar with distance calculations
- [ ] Draw distance lines on POI hover

---

### 23. Transaction Insights & Outlier Visualization

**Requirement:** Transaction table with outlier highlighting and verification badges.

**Current State:**
- ❌ No transaction data display
- ❌ No outlier detection visualization
- ❌ No verification source badges

**Action Required:**
- [ ] Create `TransactionTable.tsx` component
- [ ] Implement outlier highlighting (>20% deviation)
- [ ] Add verification source badges
- [ ] Integrate with transaction history API

---

## Implementation Priority Matrix

| Priority | Point | Effort | Business Impact |
|----------|-------|--------|-----------------|
| P0 (Critical) | 19 - Area Transparency | Medium | Legal/Compliance |
| P0 (Critical) | 21 - Smart Brochure | High | Lead generation |
| P1 (High) | 18 - Page Layout | High | User experience |
| P1 (High) | 20 - Price Comparison | Medium | Competitive intel |
| P2 (Medium) | 23 - Transaction Table | Medium | Trust/transparency |
| P2 (Medium) | 22 - Intelligence Map | High | Feature differentiation |

---

## Component Architecture Plan

```
frontend/src/components/
├── projectDetail/
│   ├── ProjectHero.tsx          (ENHANCE: Add Developer Trust Score)
│   ├── PriceSection.tsx         (ENHANCE: Add area labels)
│   ├── InventorySection.tsx     (NEW: Tower > Unit selector)
│   ├── FloorplanGallery.tsx     (NEW: Floorplan viewer)
│   ├── AmenitiesSection.tsx     (ENHANCE: Add Lifestyle Score)
│   ├── LocationSection.tsx      (REPLACE with IsochroneMap)
│   ├── IntelligenceSection.tsx  (NEW: Trends + Transactions)
│   └── ReviewsSection.tsx       (NEW: Sentiment display)
├── shared/
│   ├── AreaLabel.tsx            (NEW: Area type badge + tooltip)
│   ├── AreaComparisonWarning.tsx (NEW: Mismatch warning)
│   ├── PriceComparisonWidget.tsx (NEW: Chart component)
│   └── VerificationBadge.tsx    (NEW: Source badge)
├── brochure/
│   ├── SmartBrochure.tsx        (NEW: Main component)
│   └── BrochureLeadForm.tsx     (NEW: Lead capture form)
├── map/
│   ├── IsochroneMap.tsx         (NEW: Enhanced map)
│   ├── POIMarker.tsx            (NEW: POI marker)
│   └── POISidebar.tsx           (NEW: POI list)
└── transactions/
    └── TransactionTable.tsx     (NEW: Transaction display)
```

---

## Next Steps

1. **Step 2:** Define component interfaces and props
2. **Step 3:** Implement `PriceComparisonWidget` and `SmartBrochure` (priority)
3. **Step 4:** Restructure listing page layout
4. **Step 5:** Enhance map with isochrones
