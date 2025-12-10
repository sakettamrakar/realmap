# Glossary

Key terms used across the CG RERA platform.

- **RERA**: Real Estate Regulatory Authority (Chhattisgarh).
- **Project**: A registered real estate project with a unique RERA registration number.
- **Promoter**: Developer or entity responsible for the project.
- **V1 JSON**: Normalized scraper output schema representing a project run.
- **Run**: A single execution of the scraper pipeline, writing artifacts under `runs/run_<id>/`.
- **Normalized Address**: Canonical address string used for geocoding.
- **Geo Precision**: Level of accuracy for coordinates (e.g., rooftop, locality).
- **Amenity POI**: Point of interest record used for amenity enrichment.
- **Project Amenity Stats**: Aggregated amenity counts and distances per project.
- **Project Scores**: Composite scores summarizing a project’s amenity and location quality.
- **QA**: Quality assurance jobs comparing HTML vs JSON and validating pipeline outputs.
