"""Browser session abstractions for interacting with the CG RERA portal."""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from cg_rera_extractor.config.models import BrowserConfig


@runtime_checkable
class BrowserSession(Protocol):
    """Protocol describing the behaviour expected from browser sessions."""

    def start(self) -> None:
        """Start (or attach to) a browser session."""

    def goto(self, url: str) -> None:
        """Navigate to the supplied URL."""

    def go_back(self) -> None:
        """Navigate back in the browser history."""

    def fill(self, selector: str, value: str) -> None:
        """Fill a form field identified by ``selector`` with ``value``."""

    def select_option(self, selector: str, value: str | list[str]) -> None:
        """Select one or more options for a ``<select>`` element."""

    def click(self, selector: str) -> None:
        """Click an element matching ``selector``."""

    def wait_for_selector(self, selector: str, timeout_ms: int = 10_000) -> None:
        """Wait for a selector to appear on the page."""

    def get_page_html(self) -> str:
        """Return the current page HTML as a string."""

    def close(self) -> None:
        """Tear down the browser session and free any allocated resources."""

    def current_page(self) -> Page:
        """Return the underlying Playwright page for advanced interactions."""

    def current_context(self) -> BrowserContext:
        """Return the browser context for resource downloads."""


class PlaywrightBrowserSession:
    """Playwright-based implementation of :class:`BrowserSession`."""

    def __init__(self, config: Optional[BrowserConfig] = None) -> None:
        self._config = config or BrowserConfig()
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def __enter__(self) -> "PlaywrightBrowserSession":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()

    def start(self) -> None:
        """Launch the Playwright Chromium browser if it is not already running."""

        if self._page is not None:
            return

        self._playwright = sync_playwright().start()
        chromium = self._playwright.chromium
        self._browser = chromium.launch(
            headless=self._config.headless,
            slow_mo=self._config.slow_mo_ms or None,
        )
        self._context = self._browser.new_context()
        self._page = self._context.new_page()
        self._page.set_default_timeout(self._config.default_timeout_ms)

    def goto(self, url: str) -> None:
        page = self._require_page()
        page.goto(url)

    def go_back(self) -> None:
        page = self._require_page()
        page.go_back()

    def fill(self, selector: str, value: str) -> None:
        page = self._require_page()
        page.fill(selector, value)

    def select_option(self, selector: str, value: str | list[str]) -> None:
        page = self._require_page()
        page.select_option(selector, value=value)

    def click(self, selector: str) -> None:
        page = self._require_page()
        page.click(selector)

    def wait_for_selector(self, selector: str, timeout_ms: int = 10_000) -> None:
        page = self._require_page()
        page.wait_for_selector(selector, timeout=timeout_ms)

    def get_page_html(self) -> str:
        page = self._require_page()
        return page.content()

    def current_page(self) -> Page:
        return self._require_page()

    def current_context(self) -> BrowserContext:
        if self._context is None:
            raise RuntimeError("Browser session not started. Call start() first.")
        return self._context

    def close(self) -> None:
        if self._page is not None:
            self._page.close()
            self._page = None
        if self._context is not None:
            self._context.close()
            self._context = None
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    def _require_page(self) -> Page:
        if self._page is None:
            raise RuntimeError("Browser session not started. Call start() first.")
        return self._page


__all__ = ["BrowserSession", "PlaywrightBrowserSession"]
