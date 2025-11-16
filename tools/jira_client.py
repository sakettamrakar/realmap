"""Minimal Jira Cloud REST API client for helper scripts."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional

import requests


@dataclass
class JiraConfig:
    base_url: str
    email: str
    api_token: str
    project_key: str


REQUIRED_ENV_VARS = ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN")


class JiraConfigError(RuntimeError):
    """Raised when Jira configuration is incomplete."""


_DEF_PROJECT_KEY = "CGRE"


def _load_config() -> JiraConfig:
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        raise JiraConfigError(
            "Missing required environment variables: " + ", ".join(sorted(missing))
        )

    project_key = os.environ.get("JIRA_PROJECT_KEY", _DEF_PROJECT_KEY)
    base_url = os.environ["JIRA_BASE_URL"].rstrip("/")
    email = os.environ["JIRA_EMAIL"]
    api_token = os.environ["JIRA_API_TOKEN"]

    return JiraConfig(base_url=base_url, email=email, api_token=api_token, project_key=project_key)


def _request(method: str, path: str, payload: Optional[Dict] = None) -> requests.Response:
    config = _load_config()
    url = f"{config.base_url}/rest/api/3{path}"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    response = requests.request(
        method=method,
        url=url,
        json=payload,
        headers=headers,
        auth=(config.email, config.api_token),
        timeout=30,
    )
    response.raise_for_status()
    return response


def create_issue(summary: str, description: str, issue_type: str = "Story") -> str:
    """Create a Jira issue and return its key (e.g. CGRE-12)."""

    config = _load_config()
    payload = {
        "fields": {
            "project": {"key": config.project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
        }
    }
    response = _request("POST", "/issue", payload)
    data = response.json()
    issue_key = data.get("key")
    if not issue_key:
        raise RuntimeError("Jira did not return an issue key.")
    return issue_key


def update_issue_description(issue_key: str, description: str) -> None:
    """Replace the description of a Jira issue."""

    payload = {"fields": {"description": description}}
    _request("PUT", f"/issue/{issue_key}", payload)


def add_comment(issue_key: str, comment: str) -> None:
    """Add a comment to a Jira issue."""

    payload = {"body": comment}
    _request("POST", f"/issue/{issue_key}/comment", payload)

