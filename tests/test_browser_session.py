"""Tests for browser session abstractions and helpers."""

from __future__ import annotations

from typing import List

import pytest

from cg_rera_extractor.browser.captcha_flow import wait_for_captcha_solved
from cg_rera_extractor.browser.session import BrowserSession


class FakeBrowserSession:
    """Simple fake implementation that records actions for assertions."""

    def __init__(self) -> None:
        self.started = False
        self.closed = False
        self.actions: List[str] = []

    def start(self) -> None:
        self.started = True
        self.actions.append("start")

    def goto(self, url: str) -> None:
        self.actions.append(f"goto:{url}")

    def go_back(self) -> None:
        self.actions.append("go_back")

    def fill(self, selector: str, value: str) -> None:
        self.actions.append(f"fill:{selector}={value}")

    def select_option(self, selector: str, value: str | list[str]) -> None:
        self.actions.append(f"select:{selector}={value}")

    def click(self, selector: str) -> None:
        self.actions.append(f"click:{selector}")

    def wait_for_selector(self, selector: str, timeout_ms: int = 10_000) -> None:
        self.actions.append(f"wait:{selector}:{timeout_ms}")

    def get_page_html(self) -> str:
        return "<html></html>"

    def close(self) -> None:
        self.closed = True
        self.actions.append("close")


def test_fake_browser_session_matches_protocol() -> None:
    session = FakeBrowserSession()
    assert isinstance(session, BrowserSession)


def test_fake_browser_session_records_actions() -> None:
    session = FakeBrowserSession()
    session.start()
    session.goto("https://example.com")
    session.fill("#search", "Value")
    session.click("button[type=submit]")
    session.wait_for_selector(".results", timeout_ms=5_000)
    html = session.get_page_html()
    session.close()

    assert session.actions == [
        "start",
        "goto:https://example.com",
        "fill:#search=Value",
        "click:button[type=submit]",
        "wait:.results:5000",
        "close",
    ]
    assert html == "<html></html>"
    assert session.closed is True


def test_wait_for_captcha_solved_prompts(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_input(prompt: str) -> str:
        captured["prompt"] = prompt
        return ""

    monkeypatch.setattr("builtins.input", fake_input)

    wait_for_captcha_solved("Custom prompt")

    assert captured["prompt"] == "Custom prompt"
