"""Command line interface for running CG RERA crawls.

Supports overriding the configured run mode via ``--mode`` to select DRY_RUN,
LISTINGS_ONLY, or FULL execution paths.
"""
from __future__ import annotations

import argparse
import logging
from typing import Sequence

from cg_rera_extractor.config.loader import load_config
from cg_rera_extractor.config.models import RunMode
from cg_rera_extractor.runs.orchestrator import run_crawl


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CG RERA extractor run orchestrator")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the YAML configuration file controlling the crawl",
    )
    parser.add_argument(
        "--mode",
        choices=["dry-run", "listings-only", "full"],
        help=(
            "Override the run mode from the config file: "
            "dry-run (no browser), listings-only (no detail fetch), full (default)."
        ),
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    config = load_config(args.config)
    if args.mode:
        override = args.mode.replace("-", "_").upper()
        config.run.mode = RunMode[override]
    status = run_crawl(config)
    logging.info("Run %s finished with counts: %s", status.run_id, status.counts)

    if status.warnings:
        logging.warning("Run completed with %d warnings", len(status.warnings))
        for warning in status.warnings:
            logging.warning(" - %s", warning)

    if status.errors:
        logging.error("Run completed with %d errors", len(status.errors))
        for error in status.errors:
            logging.error(" - %s", error)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
