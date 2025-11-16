"""Unit tests for the configuration loader."""
from pathlib import Path

import pytest

from cg_rera_extractor.config.loader import load_config
from cg_rera_extractor.config.models import AppConfig, CrawlMode


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    content = """
run:
  crawl_mode: incremental
  max_projects: 5
  output_dir: ~/cg-rera/outputs
  search_filters:
    - district: Bilaspur
      tehsil: Kota
      status: Registered
browser:
  provider: playwright
  headless: false
  default_timeout_ms: 20000
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(content.strip(), encoding="utf-8")
    return config_path


def test_load_config_returns_app_config(config_file: Path) -> None:
    config = load_config(config_file)

    assert isinstance(config, AppConfig)
    assert config.run.crawl_mode == CrawlMode.INCREMENTAL
    assert config.run.max_projects == 5
    assert config.run.output_dir.name == "outputs"
    assert config.browser.headless is False
    assert config.browser.default_timeout_ms == 20000
    assert config.run.search_filters[0].summary() == "district=Bilaspur, tehsil=Kota, status=Registered"


def test_load_config_missing_file(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError):
        load_config(missing_file)
