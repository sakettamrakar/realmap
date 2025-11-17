from __future__ import annotations

import logging

from cg_rera_extractor.browser.search_page_config import SearchPageSelectors
from cg_rera_extractor.browser.search_page_flow import (
    SearchFilters,
    apply_filters_or_fallback,
)


class FailingSession:
    def select_option(self, selector: str, value) -> None:  # pragma: no cover - simple fake
        raise RuntimeError(f"Selector not found: {selector}")


def test_manual_fallback_triggers_on_missing_selector(monkeypatch, capsys) -> None:
    prompts: list[str] = []

    def fake_input(prompt: str) -> str:
        prompts.append(prompt)
        return ""

    monkeypatch.setattr("builtins.input", fake_input)

    filters = SearchFilters(district="Raipur", status="Ongoing", project_types=None)
    selectors = SearchPageSelectors(district=None, status=None, project_type=None, submit_button=None)

    went_manual = apply_filters_or_fallback(FailingSession(), selectors, filters, logging.getLogger(__name__))

    assert went_manual is True
    captured = capsys.readouterr()
    assert "MANUAL FILTER MODE" in captured.out
    assert any("Press ENTER" in prompt for prompt in prompts)
