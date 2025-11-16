"""Tests for syncing DEV_PLAN tasks to Jira."""

from pathlib import Path

from tools import sync_dev_plan_to_jira as sync


def test_parse_dev_plan_tasks_extracts_blocks():
    markdown = (
        "## Phase\n"
        "### T1 – First task\n"
        "Line A\n"
        "- bullet\n"
        "### P2.1: Second task\n"
        "Another line\n"
    )
    tasks = sync.parse_dev_plan_tasks(markdown)
    assert len(tasks) == 2
    assert tasks[0].task_id == "T1"
    assert "Line A" in tasks[0].description
    assert tasks[1].task_id == "P2.1"


def test_sync_dev_plan_creates_and_updates(tmp_path, monkeypatch):
    plan_path = tmp_path / "DEV_PLAN.md"
    plan_path.write_text(
        "### T1 – Existing\nOld description\n\n### T2 – New Task\nNew description\n",
        encoding="utf-8",
    )
    mapping_path = tmp_path / "jira_mapping.json"
    mapping_path.write_text('{"T1": "CGRE-1"}', encoding="utf-8")

    updated = {}
    created = {}
    comments = []

    def fake_update(issue_key: str, description: str) -> None:
        updated[issue_key] = description

    def fake_create(summary: str, description: str, issue_type: str = "Story") -> str:
        created[summary] = description
        return "CGRE-2"

    def fake_comment(issue_key: str, comment: str) -> None:
        comments.append((issue_key, comment))

    monkeypatch.setattr(sync.jira_client, "update_issue_description", fake_update)
    monkeypatch.setattr(sync.jira_client, "create_issue", fake_create)
    monkeypatch.setattr(sync.jira_client, "add_comment", fake_comment)
    monkeypatch.setattr(sync, "build_run_comment", lambda: "Synced via tests")

    sync.sync_dev_plan(dev_plan_path=plan_path, mapping_path=mapping_path)

    assert updated == {"CGRE-1": "Old description"}
    assert created == {"T2 – New Task": "New description"}
    assert comments == [("CGRE-1", "Synced via tests"), ("CGRE-2", "Synced via tests")]
    saved_mapping = mapping_path.read_text(encoding="utf-8")
    assert "CGRE-2" in saved_mapping
