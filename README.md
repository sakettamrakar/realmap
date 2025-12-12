# RealMap Platform Documentation

**Single Source of Truth** for the Chhattisgarh RERA Intelligence Platform.

## 📚 Documentation Map

The documentation is organized into 4 logical quadrants:

### 1. Functional ([docs/01-functional](./docs/01-functional/))
*   **[Functional Specification](./docs/01-functional/Functional_Specification.md)**: Product capabilities, user personas, and design principles.
*   **[User Guide](./docs/01-functional/User_Guide.md)**: How to use the Web & Mobile application.

### 2. Technical ([docs/02-technical](./docs/02-technical/))
*   **[Architecture](./docs/02-technical/Architecture.md)**: High-level system design and component interaction.
*   **[Data Model](./docs/02-technical/Data_Model.md)**: Database schema, tables, and relationships.
*   **[Scraper & Pipeline](./docs/02-technical/Scraper_Pipeline.md)**: How data is ingested, validated, and loaded.
*   **[API Reference](./docs/02-technical/API_Reference.md)**: Backend endpoint documentation.

### 3. Artificial Intelligence ([docs/03-ai](./docs/03-ai/))
*   **[AI Overview](./docs/03-ai/AI_Overview.md)**: Feature roadmap and high-level AI strategy.
*   **[AI Implementation](./docs/03-ai/AI_Implementation.md)**: Technical guide for Models, Prompts, and Agents.

### 4. Operations ([docs/04-operations](./docs/04-operations/))
*   **[Operations Manual](./docs/04-operations/Operations_Manual.md)**: Installation, Deployment, and Troubleshooting.

---

## 🚀 Quick Start

1.  **Clone:** `git clone <repo>`
2.  **Setup:** `pip install -r requirements.txt`
3.  **Run Scraper:** `python -m cg_rera_extractor.cli run --config config.debug.yaml`
4.  **Start API:** `python -m cg_rera_extractor.api.main`

For full details, see the **[Operations Manual](./docs/04-operations/Operations_Manual.md)**.

---

## 🏗️ Repository Structure

*   `/cg_rera_extractor` - Core Python Logic (Scraper + API)
*   `/frontend` - React/Vite Web Application
*   `/tools` - CLI Utilities for ETL and QA
*   `/ai` - AI Microservice & Agent Specifications
*   `/docs` - **You are here**

---

*Verified & Consolidated: December 12, 2025*
