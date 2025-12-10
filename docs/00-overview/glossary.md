# Glossary

Key terms used across the CG RERA platform.

- **RERA**: Real Estate Regulatory Authority (Chhattisgarh), the regulatory portal that is scraped.
- **Project**: A registered real estate project with a unique RERA registration number.
- **Promoter**: The developer or entity responsible for the project.
- **V1 JSON**: The normalized scraper output schema representing a single project for a given run.
- **Run**: A single execution of the scraper pipeline, writing artifacts under `runs/run_<id>/` or a configured base directory.
- **Normalized Address**: Canonical address string constructed from structured fields and used for geocoding.
- **Geo Precision**: Level of accuracy for coordinates (e.g., rooftop, locality, city-level).
- **Amenity POI**: Point-of-interest record (school, hospital, transit, etc.) used in amenity enrichment.
- **Project Amenity Stats**: Aggregated amenity counts, distances, and rollups per project.
- **Project Scores**: Composite scores summarizing a projects amenity and location quality across multiple dimensions.
- **QA (Quality Assurance)**: Jobs and tools that compare HTML vs JSON, validate geo coverage, and check amenity/score outputs.
- **Discovery Tags**: Curated labels (e.g., metro-connected) attached to projects for faceted search.
- **RERA Verification**: Structured status and evidence confirming that a project is present and current on the official portal.
- **Landmarks**: Named places (e.g., major malls, tech parks) linked to nearby projects for discovery and trust.
