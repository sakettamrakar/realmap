"""Sync tasks from DEV_PLAN.md to Jira issues."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

try:  # pragma: no cover - fallback for script execution
    from . import jira_client
except ImportError:  # pragma: no cover
    from tools import jira_client  # type: ignore

DEV_PLAN_PATH = Path(__file__).resolve().parent.parent / "DEV_PLAN.md"
MAPPING_PATH = Path(__file__).resolve().parent / "jira_mapping.json"


@dataclass
class DevPlanTask:
    task_id: str
    title: str
    description: str


_TASK_HEADING_RE = re.compile(r"^###\s+([A-Za-z0-9.]+)\s*(?:[:\-\u2013]\s*(.+))?$")


def parse_dev_plan_tasks(markdown: str) -> List[DevPlanTask]:
    """Parse DEV_PLAN markdown and extract task descriptions."""

    lines = markdown.splitlines()
    tasks: List[DevPlanTask] = []
    current_id: str | None = None
    current_title: str = ""
    current_body: List[str] = []

    def flush() -> None:
        nonlocal current_id, current_title, current_body
        if current_id is None:
            return
        description = "\n".join(line.rstrip() for line in current_body).strip()
        if description:
            tasks.append(DevPlanTask(task_id=current_id, title=current_title, description=description))
        current_id = None
        current_title = ""
        current_body = []

    for raw_line in lines:
        stripped = raw_line.strip()
        heading_match = _TASK_HEADING_RE.match(stripped)
        if heading_match:
            flush()
            current_id = heading_match.group(1)
            current_title = heading_match.group(2) or ""
            continue
        if stripped.startswith("## "):
            flush()
            continue
        if current_id is not None:
            current_body.append(raw_line)

    flush()
    return tasks


def _load_mapping(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_mapping(path: Path, mapping: Dict[str, str]) -> None:
    path.write_text(json.dumps(mapping, indent=2, sort_keys=True), encoding="utf-8")


def sync_dev_plan(dev_plan_path: Path = DEV_PLAN_PATH, mapping_path: Path = MAPPING_PATH) -> None:
    markdown = dev_plan_path.read_text(encoding="utf-8")
    tasks = parse_dev_plan_tasks(markdown)
    mapping = _load_mapping(mapping_path)

    for task in tasks:
        summary = f"{task.task_id} – {task.title}".strip()
        description = task.description or "No description provided."
        if task.task_id in mapping:
            jira_key = mapping[task.task_id]
            jira_client.update_issue_description(jira_key, description)
            print(f"Updated {jira_key} for task {task.task_id}")
        else:
            jira_key = jira_client.create_issue(summary, description, issue_type="Story")
            mapping[task.task_id] = jira_key
            print(f"Created {jira_key} for task {task.task_id}")

    _save_mapping(mapping_path, mapping)


if __name__ == "__main__":
    sync_dev_plan()
