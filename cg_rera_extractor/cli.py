"""Command line interface for running CG RERA crawls."""
from __future__ import annotations

import argparse
import logging
from typing import Sequence

from cg_rera_extractor.config.loader import load_config
from cg_rera_extractor.runs.orchestrator import run_crawl


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CG RERA extractor run orchestrator")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the YAML configuration file controlling the crawl",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    config = load_config(args.config)
    status = run_crawl(config)
    logging.info("Run %s finished with counts: %s", status.run_id, status.counts)

    if status.errors:
        logging.error("Run completed with %d errors", len(status.errors))
        for error in status.errors:
            logging.error(" - %s", error)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
