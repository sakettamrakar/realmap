# API Reference

**Version:** 2.0.0  
**Date:** 2026-01-02  
**Status:** Live / Implemented

---

## 1. Overview
The RealMap API is built with **FastAPI**. It provides read-only access to project data, analytics, and discovery features.

**Base URL:** `http://localhost:8000/api/v1` (Default)

---

## 2. Core Endpoints

### Projects
*   **`GET /projects/search`**
    *   **Query Params:** `district`, `tehsil`, `lat`, `lon`, `radius_km`, `min_price`, `max_price`, `tags`, `rera_verified_only`.
    *   **Response:** Paginated list of projects with facets.
*   **`GET /projects/lookup/{identifier}`**
    *   **Path Params:** `identifier` (Database ID or RERA String).
    *   **Query Params:** `include_hierarchy` (bool), `include_jsonld` (bool).
    *   **Response:** Unified project identity with optional hierarchy.
*   **`GET /projects/{id}`**
    *   **Path Params:** `id` (Database ID).
    *   **Response:** Full Project Detail object.
*   **`GET /projects/map`**
    *   **Query Params:** `bbox` (min_lon, min_lat, max_lon, max_lat) OR `lat`/`lon`/`radius_km`.
    *   **Response:** GeoJSON feature collection for map pins.

### Rich Media
*   **`GET /projects/{id}/media`**
    *   **Response:** Structured media assets (Gallery, Floorplans, Videos) with metadata.

### Inventory
*   **`GET /projects/{id}/inventory`**
    *   **Response:** Detailed unit-level inventory (Available/Sold status, Area, Floor).

### Analytics & Discovery
*   **`GET /analytics/price-trends`**
    *   Returns historical price buckets for a given region.
*   **`GET /discovery/tags`**
    *   Returns list of available tags (e.g., "Metro", "Park") for filtering.

### AI & Chat
*   **`POST /chat/search`**
    *   **Body:** `{ "query": "apartments near aiims" }`
    *   **Response:** `{ "text": "...", "projects": [...] }`

---

## 3. Schemas

### ProjectSummary
```json
{
  "id": 123,
  "rera_id": "PCGRERA...",
  "name": "Super Heights",
  "min_price": 5000000,
  "overall_score": 85,
  "location": { "lat": 21.25, "lon": 81.63 },
  "tags": ["metro-connected", "ready-to-move"]
}
```

### ProjectMediaResponse
```json
{
  "project_id": 123,
  "gallery": [{ "url": "...", "type": "gallery" }],
  "floorplans": [{ "url": "...", "type": "floorplan" }]
}
```

### QA & Errors
All errors return standard HTTP codes:
*   `400` - Bad Request (Invalid Filter)
*   `404` - Resource Not Found
*   `500` - Internal Server Error

---

## 4. Middleware
*   **Rate Limiting:** IP-based throttling enabled by default.
*   **CORS:** Configured to allow requests from the frontend origin.

---

## 5. Related Documents
- [Architecture](./Architecture.md)
- [Data Model](./Data_Model.md)
