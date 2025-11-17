"""Inspect the CG RERA search page DOM to help find selectors.

Usage::

    python tools/inspect_search_page_dom.py --config config.phase2.sample.yaml
"""
from __future__ import annotations

import argparse

from cg_rera_extractor.browser.search_page_config import get_search_page_config
from cg_rera_extractor.config.loader import load_config
from playwright.sync_api import sync_playwright


def _describe_elements(elements):
    rows: list[str] = []
    for element in elements:
        attrs = element.evaluate("(el) => ({ id: el.id, name: el.name, text: el.innerText.trim() })")
        rows.append(f"id={attrs['id']!r} name={attrs['name']!r} text={attrs['text']!r}")
    return rows


def inspect_dom(config_path: str) -> None:
    app_config = load_config(config_path)
    search_config = get_search_page_config(app_config)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(search_config.url)

        selects = page.query_selector_all("select")
        buttons = page.query_selector_all("button")

        print(f"Loaded {search_config.url}")
        print("\n<select> elements:")
        for row in _describe_elements(selects):
            print(f"  - {row}")

        print("\n<button> elements:")
        for row in _describe_elements(buttons):
            print(f"  - {row}")

        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect CG RERA search page DOM for selectors")
    parser.add_argument(
        "--config",
        default="config.example.yaml",
        help="Path to YAML config file with search_page.url configured",
    )
    args = parser.parse_args()

    inspect_dom(args.config)


if __name__ == "__main__":
    main()
