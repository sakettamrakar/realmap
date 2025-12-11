"""
Fast cache layer for conditional scraping.

This module provides O(1) lookup for checking if a listing has already been scraped,
enabling delta scraping mode where only new listings are processed.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

ScrapingMode = Literal["delta", "full"]


class ScrapedCache:
    """
    Fast in-memory cache of scraped listing IDs with persistent storage.
    
    Uses a set for O(1) lookup performance and persists to a JSON file.
    """
    
    def __init__(self, cache_file: str | Path = "data/scraped_cache.json"):
        """
        Initialize the cache.
        
        Args:
            cache_file: Path to the cache file (JSON format)
        """
        self.cache_file = Path(cache_file)
        self._cache: set[str] = set()
        self._modified = False
    
    def load(self) -> None:
        """Load the cache from disk."""
        if not self.cache_file.exists():
            logger.info(f"Cache file not found, starting with empty cache: {self.cache_file}")
            self._cache = set()
            return
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                self._cache = set(data)
            elif isinstance(data, dict) and "scraped_ids" in data:
                self._cache = set(data["scraped_ids"])
            else:
                logger.warning(f"Invalid cache format, starting fresh: {self.cache_file}")
                self._cache = set()
            
            logger.info(f"Loaded {len(self._cache)} scraped IDs from cache: {self.cache_file}")
        
        except Exception as exc:
            logger.error(f"Failed to load cache from {self.cache_file}: {exc}")
            self._cache = set()
    
    def persist(self) -> None:
        """Persist the cache to disk."""
        if not self._modified:
            logger.debug("Cache not modified, skipping persist")
            return
        
        try:
            # Ensure directory exists
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temp file first for atomic write
            temp_file = self.cache_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {
                        "scraped_ids": sorted(self._cache),
                        "total_count": len(self._cache)
                    },
                    f,
                    indent=2,
                    ensure_ascii=False
                )
            
            # Atomic rename
            temp_file.replace(self.cache_file)
            
            logger.info(f"Persisted {len(self._cache)} scraped IDs to cache: {self.cache_file}")
            self._modified = False
        
        except Exception as exc:
            logger.error(f"Failed to persist cache to {self.cache_file}: {exc}")
    
    def contains(self, listing_id: str) -> bool:
        """
        Check if a listing ID exists in the cache.
        
        Args:
            listing_id: The listing identifier (e.g., registration number)
        
        Returns:
            True if the listing has been scraped before
        """
        return listing_id in self._cache
    
    def add(self, listing_id: str) -> None:
        """
        Add a listing ID to the cache.
        
        Args:
            listing_id: The listing identifier to add
        """
        if listing_id not in self._cache:
            self._cache.add(listing_id)
            self._modified = True
    
    def remove(self, listing_id: str) -> None:
        """
        Remove a listing ID from the cache.
        
        Args:
            listing_id: The listing identifier to remove
        """
        if listing_id in self._cache:
            self._cache.discard(listing_id)
            self._modified = True
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        self._cache.clear()
        self._modified = True
    
    def size(self) -> int:
        """Get the number of entries in the cache."""
        return len(self._cache)
    
    def __contains__(self, listing_id: str) -> bool:
        """Support 'in' operator."""
        return self.contains(listing_id)
    
    def __len__(self) -> int:
        """Support len() function."""
        return self.size()


def load_cache(cache_file: str | Path = "data/scraped_cache.json") -> ScrapedCache:
    """
    Load the scraped listings cache from disk.
    
    Args:
        cache_file: Path to the cache file
    
    Returns:
        ScrapedCache instance with loaded data
    """
    cache = ScrapedCache(cache_file)
    cache.load()
    return cache


def persist_cache(cache: ScrapedCache) -> None:
    """
    Persist the cache to disk.
    
    Args:
        cache: ScrapedCache instance to persist
    """
    cache.persist()


def should_skip_listing(
    listing_id: str,
    mode: ScrapingMode,
    cache: ScrapedCache,
) -> bool:
    """
    Determine if a listing should be skipped based on mode and cache.
    
    Args:
        listing_id: The listing identifier
        mode: Scraping mode ("delta" or "full")
        cache: ScrapedCache instance
    
    Returns:
        True if the listing should be skipped, False if it should be scraped
    """
    if mode == "full":
        return False
    
    if mode == "delta":
        return cache.contains(listing_id)
    
    logger.warning(f"Unknown scraping mode: {mode}, defaulting to full scrape")
    return False


def mark_listing_scraped(
    listing_id: str,
    cache: ScrapedCache,
    persist_immediately: bool = False,
) -> None:
    """
    Mark a listing as scraped in the cache.
    
    Args:
        listing_id: The listing identifier
        cache: ScrapedCache instance
        persist_immediately: If True, persist cache to disk immediately
    """
    cache.add(listing_id)
    
    if persist_immediately:
        cache.persist()


__all__ = [
    "ScrapedCache",
    "ScrapingMode",
    "load_cache",
    "persist_cache",
    "should_skip_listing",
    "mark_listing_scraped",
]
