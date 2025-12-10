# AI Development Control Panel

**Version:** 2.0 (Agent Control Layer)  
**Status:** Active  
**Last Updated:** 2025-12-10

This document serves as the **Master Meta-Document** for the `realmap` AI microservice.

---

## 1. System Overview (Control Layer)

The AI System is composed of 5 specialist agents managed by a central config.
Each agent encapsulates specific logic, rules, and LLM prompts.

```ascii
+-------------------+
|   Application     |
|   (FastAPI/Work)  |
+---------+---------+
          |
          v
+---------+---------+      +-------------------+
|  Agent Manager    +----->| Observability     |
|  (Router/Config)  |      |Logger/Metrics     |
+---------+---------+      +-------------------+
          |
          +--> [Scoring Agent] ----> (Deterministic + LLM)
          |
          +--> [Enrichment Agent] -> (Normalization + Suggestion)
          |
          +--> [Anomaly Agent] ----> (Rule Check + Reasoning)
          |
          +--> [Suggestion Agent] -> (Generative UX)
          |
          +--> [Compliance Guard] -> (Safety Filter)
```

---

## 2. Agent Inventory

| Agent | Config | Role | Risk Profile |
| :--- | :--- | :--- | :--- |
| **scoring_agent** | `/AI/agents/scoring_agent.json` | Calculates 0-100 scores and explains them. | Medium |
| **enrichment_agent** | `/AI/agents/enrichment_agent.json` | Cleans data and likely-fills missing fields. | Low |
| **anomaly_detection_agent** | `/AI/agents/anomaly_detection_agent.json` | Flags suspicious or contradictory records. | High |
| **ai_suggestions_agent** | `/AI/agents/ai_suggestions_agent.json` | Generates marketing copy and tags. | Low |
| **compliance_guard_agent** | `/AI/agents/compliance_guard_agent.json` | Final gatekeeper for LLM output safety. | Critical |

---

## 3. Operations & Controls

### Enabling / Disabling Features
Modify `/config/agent-manager/agent-manager.json` to remove an agent from `agents_enabled` list. This should strictly disable its execution path.

### LLM Policy
*   All Agents MUST use the `/AI/core/local-llm-adapter.py`.
*   Direct API calls to external providers (OpenAI, etc.) are currently **FORBIDDEN** unless configured in the adapter.
*   Token usage must be logged via `/AI/observability/metrics.py`.

### Troubleshooting
*   **LLM Timeout:** Check `local-llm-adapter.py` logs. Reduce `CONTEXT_SIZE` in `.env`.
*   **Agent Failure:** Check `/AI/observability/logger.py` output.
*   **Json Error:** Ensure agent spec in `/AI/agents/*.json` is valid.

---

## 4. Workflows

### Implementing a New Task
1.  Define task in `/AI/task-library.md`.
2.  Assign to an existing Agent (update `responsibilities` in JSON).
3.  Add routing rule in `/config/agent-manager/agent-manager.json`.
4.  Implement logic in `services/ai-microservice` calling the Agent.

### Creating a New Agent
1.  Create `/AI/agents/new_agent.json`.
2.  Create `/AI/core/system-prompts/agent-new.txt`.
3.  Register in Agent Manager Config.

---

## 5. Documentation Map
*   **Task Definitions:** `/AI/task-library.md`
*   **Agent Prompts:** `/AI/core/system-prompts/`
*   **Manager Config:** `/config/agent-manager/agent-manager.json`
*   **Local LLM Code:** `/AI/core/local-llm-adapter.py`

---

## 6. Antigravity Native Agents (Workspace Level)

These agents operate at the workspace level to manage the implementation process itself.

| Native Agent | Configuration | Trigger Example |
| :--- | :--- | :--- |
| **Documentation Sync** | `.agent/personas/doc_sync_agent.json` | "Sync documentation for feature 1" |
| **QA Validation** | `.agent/personas/qa_validation_agent.json` | "Run QA validation on feature 2" |
| **Implementation** | `.agent/personas/implementation_agent.json` | "Implement feature 1" |
| **AI Orchestration** | `.agent/personas/orchestration_agent.json` | "Update AI agent definitions" |
| **Project Governance** | `.agent/personas/governance_agent.json` | "Clean up repository structure" |

### Development Workflow Guide

1.  **Define**: Use **AI Orchestration Agent** to define new task/agents in JSON.
2.  **Verify**: Use **QA Validation Agent** to check specs.
3.  **Code**: Use **Implementation Agent** to write the code.
4.  **Document**: Use **Documentation Sync Agent** to update docs.
5.  **Audit**: Use **Project Governance Agent** to ensure compliance.

