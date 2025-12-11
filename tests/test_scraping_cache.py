"""Test the conditional scraping cache functionality."""
import json
from pathlib import Path

import pytest

from cg_rera_extractor.utils.scraping_cache import (
    ScrapedCache,
    load_cache,
    persist_cache,
    should_skip_listing,
    mark_listing_scraped,
)


def test_cache_basic_operations(tmp_path):
    """Test basic cache operations."""
    cache_file = tmp_path / "test_cache.json"
    cache = ScrapedCache(cache_file)
    cache.load()
    
    # Initially empty
    assert len(cache) == 0
    assert not cache.contains("LISTING_001")
    
    # Add listing
    cache.add("LISTING_001")
    assert len(cache) == 1
    assert cache.contains("LISTING_001")
    assert "LISTING_001" in cache  # Test __contains__
    
    # Add more
    cache.add("LISTING_002")
    cache.add("LISTING_003")
    assert len(cache) == 3


def test_cache_persistence(tmp_path):
    """Test cache persists to and loads from disk."""
    cache_file = tmp_path / "test_cache.json"
    
    # Create and populate cache
    cache1 = ScrapedCache(cache_file)
    cache1.load()
    cache1.add("LISTING_001")
    cache1.add("LISTING_002")
    cache1.persist()
    
    # Verify file exists and has correct format
    assert cache_file.exists()
    data = json.loads(cache_file.read_text())
    assert "scraped_ids" in data
    assert "total_count" in data
    assert len(data["scraped_ids"]) == 2
    assert "LISTING_001" in data["scraped_ids"]
    
    # Load into new cache instance
    cache2 = ScrapedCache(cache_file)
    cache2.load()
    assert len(cache2) == 2
    assert cache2.contains("LISTING_001")
    assert cache2.contains("LISTING_002")


def test_cache_does_not_persist_if_not_modified(tmp_path):
    """Test cache only persists when modified."""
    cache_file = tmp_path / "test_cache.json"
    
    # Create and populate
    cache = ScrapedCache(cache_file)
    cache.load()
    cache.add("LISTING_001")
    cache.persist()
    
    # Get modification time
    mtime1 = cache_file.stat().st_mtime
    
    # Load again without changes
    cache2 = ScrapedCache(cache_file)
    cache2.load()
    cache2.persist()  # Should not write
    
    # Modification time should be same
    mtime2 = cache_file.stat().st_mtime
    assert mtime1 == mtime2


def test_should_skip_listing_full_mode():
    """Test that full mode never skips."""
    cache = ScrapedCache()
    cache.load()
    cache.add("LISTING_001")
    
    # Full mode should never skip
    assert not should_skip_listing("LISTING_001", "full", cache)
    assert not should_skip_listing("LISTING_002", "full", cache)


def test_should_skip_listing_delta_mode():
    """Test that delta mode skips cached listings."""
    cache = ScrapedCache()
    cache.load()
    cache.add("LISTING_001")
    
    # Delta mode should skip cached
    assert should_skip_listing("LISTING_001", "delta", cache)
    
    # But not skip uncached
    assert not should_skip_listing("LISTING_002", "delta", cache)


def test_mark_listing_scraped():
    """Test marking listings as scraped."""
    cache = ScrapedCache()
    cache.load()
    
    assert not cache.contains("LISTING_001")
    
    mark_listing_scraped("LISTING_001", cache)
    
    assert cache.contains("LISTING_001")


def test_cache_remove():
    """Test removing entries from cache."""
    cache = ScrapedCache()
    cache.load()
    cache.add("LISTING_001")
    cache.add("LISTING_002")
    
    assert len(cache) == 2
    
    cache.remove("LISTING_001")
    
    assert len(cache) == 1
    assert not cache.contains("LISTING_001")
    assert cache.contains("LISTING_002")


def test_cache_clear():
    """Test clearing the cache."""
    cache = ScrapedCache()
    cache.load()
    cache.add("LISTING_001")
    cache.add("LISTING_002")
    cache.add("LISTING_003")
    
    assert len(cache) == 3
    
    cache.clear()
    
    assert len(cache) == 0


def test_load_cache_helper(tmp_path):
    """Test the load_cache helper function."""
    cache_file = tmp_path / "test_cache.json"
    
    # Create initial cache
    cache1 = ScrapedCache(cache_file)
    cache1.load()
    cache1.add("LISTING_001")
    cache1.persist()
    
    # Load using helper
    cache2 = load_cache(cache_file)
    assert len(cache2) == 1
    assert cache2.contains("LISTING_001")


def test_persist_cache_helper(tmp_path):
    """Test the persist_cache helper function."""
    cache_file = tmp_path / "test_cache.json"
    
    cache = ScrapedCache(cache_file)
    cache.load()
    cache.add("LISTING_001")
    
    # Persist using helper
    persist_cache(cache)
    
    assert cache_file.exists()
    data = json.loads(cache_file.read_text())
    assert "LISTING_001" in data["scraped_ids"]


def test_cache_handles_missing_file(tmp_path):
    """Test cache gracefully handles missing file."""
    cache_file = tmp_path / "nonexistent.json"
    
    cache = ScrapedCache(cache_file)
    cache.load()  # Should not raise
    
    assert len(cache) == 0


def test_cache_handles_invalid_json(tmp_path):
    """Test cache handles corrupted JSON."""
    cache_file = tmp_path / "corrupt.json"
    cache_file.write_text("{ invalid json }")
    
    cache = ScrapedCache(cache_file)
    cache.load()  # Should not raise
    
    assert len(cache) == 0  # Should start fresh


def test_cache_handles_legacy_format(tmp_path):
    """Test cache handles legacy list format."""
    cache_file = tmp_path / "legacy.json"
    cache_file.write_text(json.dumps(["LISTING_001", "LISTING_002"]))
    
    cache = ScrapedCache(cache_file)
    cache.load()
    
    assert len(cache) == 2
    assert cache.contains("LISTING_001")
    assert cache.contains("LISTING_002")


def test_cache_duplicate_adds_are_idempotent():
    """Test adding same listing multiple times is idempotent."""
    cache = ScrapedCache()
    cache.load()
    
    cache.add("LISTING_001")
    cache.add("LISTING_001")
    cache.add("LISTING_001")
    
    assert len(cache) == 1  # Still only 1 entry


def test_mark_listing_scraped_with_immediate_persist(tmp_path):
    """Test marking with immediate persistence."""
    cache_file = tmp_path / "test_cache.json"
    cache = ScrapedCache(cache_file)
    cache.load()
    
    mark_listing_scraped("LISTING_001", cache, persist_immediately=True)
    
    # Should be persisted immediately
    assert cache_file.exists()
    data = json.loads(cache_file.read_text())
    assert "LISTING_001" in data["scraped_ids"]
