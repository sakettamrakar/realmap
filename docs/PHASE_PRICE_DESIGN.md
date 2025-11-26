# Phase Price Design

This document outlines the design for the price and inventory scaffolding.

## Goals

- Introduce a flexible schema for unit types and pricing snapshots.
- Allow manual ingestion of price data (CSV).
- Expose price bands via API for search and filtering.
- Display price ranges in the UI.

## Database Schema

### Table: `project_unit_types`

Represents a canonical unit configuration within a project.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | SERIAL (PK) | Unique identifier |
| `project_id` | INTEGER (FK) | Reference to `projects.id` |
| `unit_label` | VARCHAR(100) | e.g., "2 BHK", "3 BHK Type A" |
| `bedrooms` | INTEGER | Number of bedrooms |
| `bathrooms` | INTEGER | Number of bathrooms |
| `carpet_area_min_sqft` | NUMERIC(10, 2) | Minimum carpet area |
| `carpet_area_max_sqft` | NUMERIC(10, 2) | Maximum carpet area |
| `super_builtup_area_min_sqft` | NUMERIC(10, 2) | Min super built-up area |
| `super_builtup_area_max_sqft` | NUMERIC(10, 2) | Max super built-up area |
| `is_active` | BOOLEAN | Whether this unit type is currently active/valid |
| `raw_data` | JSONB | Source-specific raw data |
| `created_at` | TIMESTAMPTZ | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | Update timestamp |

### Table: `project_pricing_snapshots`

Captures price observations at a specific point in time.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | SERIAL (PK) | Unique identifier |
| `project_id` | INTEGER (FK) | Reference to `projects.id` |
| `snapshot_date` | DATE | Date of the price observation |
| `unit_type_label` | VARCHAR(100) | Optional: specific unit type label |
| `min_price_total` | NUMERIC(14, 2) | Minimum total price (INR) |
| `max_price_total` | NUMERIC(14, 2) | Maximum total price (INR) |
| `min_price_per_sqft` | NUMERIC(10, 2) | Min price per sqft |
| `max_price_per_sqft` | NUMERIC(10, 2) | Max price per sqft |
| `source_type` | VARCHAR(50) | 'manual', 'portal_scrape', etc. |
| `source_reference` | TEXT | URL, filename, etc. |
| `raw_data` | JSONB | Source-specific raw data |
| `is_active` | BOOLEAN | Whether this snapshot is considered valid |
| `created_at` | TIMESTAMPTZ | Creation timestamp |

## Future Considerations

- **Value Score**: We plan to add a `value_score` to `project_scores` in the future, representing how good the deal is relative to the market and project quality.
