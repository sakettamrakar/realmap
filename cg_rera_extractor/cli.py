"""Command line interface for running CG RERA crawls.

Supports overriding the configured run mode via ``--mode`` to select DRY_RUN,
LISTINGS_ONLY, or FULL execution paths.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
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

    config = load_config(args.config)
    if args.mode:
        override = args.mode.replace("-", "_").upper()
        config.run.mode = RunMode[override]
    
    # Setup logging to both console and file
    # Create logs directory in output_base_dir
    log_dir = Path(config.run.output_base_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate log filename with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"scraper_{timestamp}.log"
    
    # Configure logging with both console and file handlers
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler(log_file, encoding='utf-8')  # File output
        ]
    )
    
    logging.info("="*60)
    logging.info("Starting scraper run - log file: %s", log_file)
    logging.info("Config: %s", args.config)
    logging.info("="*60)
    
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
