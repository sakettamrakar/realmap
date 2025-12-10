# AI Prompt Book

**Status:** Active  
**Version:** 1.0  
**Last Updated:** 2025-12-10

## A. Overview
This Prompt Book serves as the canonical source of truth for developing the AI microservice layer of the `realmap` repository. It contains standardized procedures, templates, and reference guides for implementing the 12 core AI features. It is designed to be used by both human developers and AI coding assistants (e.g., Antigravity, Copilot) to ensure consistency, governance, and quality.

**Safety Note:** *All AI-generated suggestions, code, and data must be reviewed by a human engineer before being merged into production. Do not auto-push AI output.*

**Quick Start:** Run `docs/prompts/ai_prompts/01_feature_score_prompt.md` to begin the first implementation.

## B. Quick-Start Checklist
1.  **Clone Repo:** `git clone <repo_url> && cd realmap`
2.  **Environment:** `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
3.  **Infrastructure:**
    ```bash
    docker-compose -f docker/docker-compose.ai.yml up -d postgres redis
    ```
4.  **Model Setup:** Download models as per [Local Model Setup](./local_model_setup.md).
5.  **Migrations:** `alembic upgrade head`
6.  **Start Service:** `uvicorn ai_service.main:app --reload --port 8001`
7.  **Test Score:** `curl -X POST http://localhost:8001/api/v1/score/project/test_id`
8.  **Unit Tests:** `pytest tests/unit/ai`
9.  **Integration:** `pytest tests/integration/ai/test_scoring.py`

## C. Folder Layout & Naming Conventions
The AI microservice structure is strictly defined:
```
/
├── services/
│   └── ai/                 # Core AI Logic
│       ├── models/         # Pydantic models & Schemas
│       ├── inference/      # Model wrappers (LLM / ML)
│       ├── pipelines/      # Feature-specific pipelines
│       └── utils/          # Helpers (normalization)
├── docs/
│   └── prompts/            # THIS FOLDER
│       ├── ai_prompts/     # Specific feature prompts (01-12)
│       ├── prompt_book.md  # Governance
│       └── ...
└── tests/
    └── ai/                 # AI-specific tests
```

## D. Canonical Prompt Template
Use this template for all task execution.

```markdown
# [Feature ID] Feature Name

## Role
Senior Python ML Engineer & Backend Developer.

## Goal
Implement [Specific Functionality] that [Value Proposition].

## Inputs
- **Files:** [List key file paths]
- **Database:** [Table names, Schema details]
- **Environment:** [Env vars like MODEL_PATH]

## Outputs
- **Code:** [New files to create]
- **Database:** [New tables/columns or rows]
- **API:** [New Endpoints e.g., POST /api/v1/...]

## Constraints
- **Resource Limits:** optimize for [6GB VRAM / CPU]
- **Safety:** Do NOT overwrite [Critical Field] without `admin_override` flag.
- **Idempotency:** Re-running the job must update the existing record, not duplicate.
- **Style:** Follow PEP8, Type Hints, Docstrings.

## Files to Modify
- [Path 1]
- [Path 2]

## Tests to Run
- `pytest tests/unit/...`
- Manual curl verification

## Acceptance Criteria
- [ ] Endpoint returns 200 OK with valid JSON structure.
- [ ] Database record created/updated correctly.
- [ ] Latency is under [X] ms.
- [ ] Unit tests pass.
- [ ] Code is linted and typed.
```

## E. How to Use Prompts
**Guidance:** Execute features sequentially (01 -> 12) or as needed. Do not mix contexts.

**Sample Run:**
1.  Open `docs/prompts/ai_prompts/01_feature_score_prompt.md`.
2.  Paste the content into your AI Coding Assistant chat.
3.  Review the generated code plan.
4.  Apply changes.
5.  Run the specified tests.

## F. Developer Responsibilities & QA Checklist
- [ ] **Code Review:** verify logic, security, and performance.
- [ ] **Test Coverage:** Ensure >80% coverage on new modules.
- [ ] **Metrics Validation:** Check if scoring distribution looks normal (e.g., not all 100s).
- [ ] **Manual Review:** Inspect the first 50-500 processed records manually.
- [ ] **Feedback Loop:** If AI output is consistently bad, update the Prompt or Model parameters.

## G. Handover Template
When marking a feature as "Done", update the implementation log with:
*   **Feature:** [Name]
*   **Endpoints:** `POST /api/v1/...`
*   **DB Tables:** `table_name`
*   **Model:** [Name & Version]
*   **Monitoring:** [Dashboard Link / Log tag]

## H. Agent Debugging Prompts

Use these prompts to have Antigravity debug specific agent behaviors.

### 1. General Agent Debug
> "Antigravity, inspect the logs in `/AI/observability/logger.py` for [AGENT_NAME]. Why did task [TASK_ID] fail?"

### 2. Scoring Agent Tweak
> "Antigravity, the Scoring Agent is generating explanations that are too long. Update `/AI/core/system-prompts/agent-scoring.txt` to enforce a 15-word limit."

### 3. Compliance Over-Blocking
> "Antigravity, the Compliance Guard is blocking valid descriptions. Add 'Real Estate Marketing' to the allow-list in `compliance_guard_agent.json` instructions."

### 4. Local LLM Diagnostic
> "Antigravity, run `python /AI/core/local-llm-adapter.py` and report the tokens/sec. Is it under 10 t/s?"

### 5. Master Architecture Query
> "Antigravity, verify if `routes_score.py` is correctly using the `scoring_agent.json` config. Does the input payload match the schema in `scoring_agent.json`?"

