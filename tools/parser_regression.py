#!/usr/bin/env python3
"""Regression harness for CG RERA HTML parsing and mapping."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cg_rera_extractor.listing import ListingRecord, parse_listing_html
from cg_rera_extractor.parsing import RawExtractedProject, map_raw_to_v1
from cg_rera_extractor.parsing.raw_extractor import extract_raw_from_html

DEFAULT_FIXTURE_DIR = REPO_ROOT / "tests" / "parser_regression" / "fixtures"
DEFAULT_GOLDEN_DIR = REPO_ROOT / "tests" / "parser_regression" / "golden"
DEFAULT_BASE_URL = "https://rera.cg.gov/"


class RegressionResult:
    """Container for parser outputs per fixture."""

    def __init__(self, fixture: Path, listing: list[ListingRecord], raw: RawExtractedProject):
        self.fixture = fixture
        self.listing = listing
        self.raw = raw
        self.v1 = map_raw_to_v1(raw, state_code="CG")

    def to_jsonable(self) -> dict:
        return {
            "fixture": self.fixture.name,
            "listing": [asdict(record) for record in self.listing],
            "raw": self.raw.model_dump(),
            "v1": self.v1.model_dump(),
        }


def iter_fixture_paths(inputs: list[str] | None, fixtures_dir: Path) -> list[Path]:
    if inputs:
        paths = [Path(item) for item in inputs]
    else:
        paths = sorted(fixtures_dir.glob("*.html"))
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing fixture(s): {', '.join(missing)}")
    return paths


def run_parsers(html: str, fixture_path: Path, base_url: str) -> RegressionResult:
    listing_records = parse_listing_html(html, base_url=base_url)
    raw = extract_raw_from_html(html, source_file=str(fixture_path))
    return RegressionResult(fixture=fixture_path, listing=listing_records, raw=raw)


def record_golden(fixtures: Iterable[Path], golden_dir: Path, base_url: str) -> list[Path]:
    golden_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for fixture in fixtures:
        html = fixture.read_text(encoding="utf-8")
        result = run_parsers(html, fixture, base_url)
        golden_path = golden_dir / f"{fixture.stem}.json"
        golden_path.write_text(json.dumps(result.to_jsonable(), indent=2, ensure_ascii=False), encoding="utf-8")
        outputs.append(golden_path)
    return outputs


def diff(expected, actual, path: str = "root") -> list[str]:  # type: ignore[override]
    differences: list[str] = []
    if isinstance(expected, dict) and isinstance(actual, dict):
        expected_keys = set(expected.keys())
        actual_keys = set(actual.keys())
        for key in sorted(expected_keys - actual_keys):
            differences.append(f"{path}.{key} missing in actual")
        for key in sorted(actual_keys - expected_keys):
            differences.append(f"{path}.{key} added in actual")
        for key in sorted(expected_keys & actual_keys):
            differences.extend(diff(expected[key], actual[key], f"{path}.{key}"))
    elif isinstance(expected, list) and isinstance(actual, list):
        min_len = min(len(expected), len(actual))
        for idx in range(min_len):
            differences.extend(diff(expected[idx], actual[idx], f"{path}[{idx}]"))
        for idx in range(min_len, len(expected)):
            differences.append(f"{path}[{idx}] missing in actual: {expected[idx]!r}")
        for idx in range(min_len, len(actual)):
            differences.append(f"{path}[{idx}] added in actual: {actual[idx]!r}")
    else:
        if expected != actual:
            differences.append(f"{path} changed: expected {expected!r}, actual {actual!r}")
    return differences


def check_golden(fixtures: Iterable[Path], golden_dir: Path, base_url: str) -> list[str]:
    discrepancies: list[str] = []
    for fixture in fixtures:
        html = fixture.read_text(encoding="utf-8")
        result = run_parsers(html, fixture, base_url)
        golden_path = golden_dir / f"{fixture.stem}.json"
        if not golden_path.exists():
            discrepancies.append(f"Missing golden file for {fixture.name} -> {golden_path}")
            continue
        golden_data = json.loads(golden_path.read_text(encoding="utf-8"))
        current = result.to_jsonable()
        differences = diff(golden_data, current)
        if differences:
            header = f"Differences for {fixture.name}:"
            discrepancies.append("\n".join([header, *(f"- {item}" for item in differences)]))
    return discrepancies


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["record", "check"], help="record goldens or check against them")
    parser.add_argument("fixtures", nargs="*", help="HTML fixture files to process (defaults to fixtures directory)")
    parser.add_argument("--fixtures-dir", default=str(DEFAULT_FIXTURE_DIR), help="Directory containing HTML fixtures")
    parser.add_argument("--golden-dir", default=str(DEFAULT_GOLDEN_DIR), help="Directory to write/read goldens")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL for resolving listing detail links")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    fixtures_dir = Path(args.fixtures_dir)
    golden_dir = Path(args.golden_dir)
    base_url = args.base_url

    try:
        fixtures = iter_fixture_paths(args.fixtures, fixtures_dir)
    except FileNotFoundError as exc:  # pragma: no cover - argument validation
        print(str(exc))
        return 2

    if args.mode == "record":
        outputs = record_golden(fixtures, golden_dir, base_url)
        print(f"Recorded {len(outputs)} golden file(s):")
        for path in outputs:
            print(f"- {path.relative_to(REPO_ROOT)}")
        return 0

    discrepancies = check_golden(fixtures, golden_dir, base_url)
    if discrepancies:
        print("Found discrepancies between current parser output and golden files:")
        for block in discrepancies:
            print(block)
            print()
        return 1

    print(f"All {len(list(fixtures))} fixture(s) match goldens.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
