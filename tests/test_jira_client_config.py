"""Tests for Jira client configuration handling."""

import pytest

from tools import jira_client


def test_missing_env_variables_raise_error(monkeypatch):
    for env_name in ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"):
        monkeypatch.delenv(env_name, raising=False)

    with pytest.raises(jira_client.JiraConfigError) as exc:
        jira_client.create_issue("summary", "desc")

    assert "JIRA_BASE_URL" in str(exc.value)
