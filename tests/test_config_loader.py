"""Unit tests for the configuration loader."""
from pathlib import Path

import pytest

from cg_rera_extractor.config.env import DEFAULT_DATABASE_URL
from cg_rera_extractor.config.loader import load_config
from cg_rera_extractor.config.models import (
    AppConfig,
    BrowserConfig,
    DatabaseConfig,
    RunConfig,
    RunMode,
    SearchFilterConfig,
)


def test_load_config_from_example_file() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    config_path = repo_root / "config.example.yaml"

    config = load_config(str(config_path))

    assert isinstance(config, AppConfig)
    assert isinstance(config.browser, BrowserConfig)
    assert isinstance(config.db, DatabaseConfig)
    assert isinstance(config.run, RunConfig)
    assert isinstance(config.run.search_filters, SearchFilterConfig)
    assert config.run.mode is RunMode.FULL
    assert config.run.search_filters.districts == ["Raipur"]
    assert config.run.search_filters.statuses == ["Ongoing"]
    assert config.run.search_filters.project_types == []
    assert config.run.output_base_dir == "./outputs/demo-run"
    assert config.run.max_search_combinations == 10
    assert config.run.max_total_listings == 200
    assert config.browser.driver == "playwright"
    assert config.browser.headless is False
    assert config.browser.slow_mo_ms == 250
    assert config.browser.default_timeout_ms == 20000
    assert config.db.url == DEFAULT_DATABASE_URL


def test_load_config_missing_file(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError):
        load_config(str(missing_file))
