# API Reference

**Version:** 1.0.0
**Date:** 2025-12-12

---

## 1. Overview
The RealMap API is built with **FastAPI**. It provides read-only access to project data, analytics, and discovery features.

**Base URL:** `http://localhost:8000/api/v1` (Default)

---

## 2. Core Endpoints

### Projects
*   **`GET /projects`**
    *   **Query Params:** `district`, `limit`, `offset`, `min_score`.
    *   **Response:** List of Project Summaries.
*   **`GET /projects/{id}`**
    *   **Path Params:** `id` (Database ID or RERA String).
    *   **Response:** Full Project Detail object (incl. amenities, documents).
*   **`GET /projects/map`**
    *   **Query Params:** `bbox` (min_lon, min_lat, max_lon, max_lat).
    *   **Response:** GeoJSON feature collection for map pins.

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
  "id": "PCGRERA...",
  "name": "Super Heights",
  "min_price": 5000000,
  "overall_score": 85,
  "location": { "lat": 21.25, "lon": 81.63 }
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
