"""Browser session abstraction used by fetchers and scrapers."""

from __future__ import annotations

from typing import Protocol


class BrowserSession(Protocol):
    """Protocol that mimics the minimal browser session operations we need."""

    def goto(self, url: str) -> None:
        """Navigate to the provided URL."""

    def get_page_html(self) -> str:
        """Return the current page HTML as a UTF-8 string."""

