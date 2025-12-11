# Quick Start: Delta Scraping Mode

## Enable Delta Mode in 3 Steps

### 1. Update your config file

```yaml
run:
  scraping_mode: delta  # Change from "full" to "delta"
  scraping_cache_file: data/scraped_cache.json
```

### 2. Run the scraper

```bash
python -m cg_rera_extractor.cli --config config.delta-mode.yaml --mode full
```

### 3. Check the logs

```
Delta mode enabled: 0 listings already scraped
[1/20] SCRAPED PCGRERA010618000020 successfully
[2/20] SCRAPED PCGRERA180518000011 successfully
...
Persisted scraping cache with 20 entries
```

---

## Next Run (Incremental Update)

Same command, but now it skips already-scraped listings:

```bash
python -m cg_rera_extractor.cli --config config.delta-mode.yaml --mode full
```

Output:
```
Delta mode enabled: 20 listings already scraped
[1/20] SKIPPED PCGRERA010618000020 - already scraped
[2/20] SKIPPED PCGRERA180518000011 - already scraped
[3/20] SCRAPED PCGRERA999999999999 successfully  # New listing!
```

---

## Switch Back to Full Mode

```yaml
run:
  scraping_mode: full  # Scrape everything
```

---

## Clear Cache (Start Fresh)

```bash
rm data/scraped_cache.json
```

---

## Check Cache Contents

```bash
cat data/scraped_cache.json
```

Output:
```json
{
  "scraped_ids": [
    "PCGRERA010618000020",
    "PCGRERA180518000011"
  ],
  "total_count": 2
}
```

---

## Config Examples

### Example 1: Full Mode (Default)
```yaml
run:
  scraping_mode: full  # or omit entirely
```

### Example 2: Delta Mode
```yaml
run:
  scraping_mode: delta
  scraping_cache_file: data/scraped_cache.json
```

### Example 3: Delta Mode with Custom Cache
```yaml
run:
  scraping_mode: delta
  scraping_cache_file: ./backups/my_cache.json
```

---

## Common Workflows

### Daily Incremental Updates
```bash
# Day 1: Scrape everything
scraping_mode: full
# Result: 100 listings scraped

# Day 2: Only new listings
scraping_mode: delta
# Result: 5 new listings scraped, 100 skipped

# Day 3: Only new listings
scraping_mode: delta
# Result: 3 new listings scraped, 105 skipped
```

### Force Re-scrape
```bash
# Option 1: Clear cache
rm data/scraped_cache.json

# Option 2: Use full mode
scraping_mode: full
```

---

## Troubleshooting

**Listings still being scraped in delta mode?**
- Check: `scraping_mode: delta` in config
- Check: Cache file exists with entries
- Check: Registration numbers match

**Want to start fresh?**
```bash
rm data/scraped_cache.json
```

---

## Performance

| Listings | Already Scraped | Delta Mode Time | Full Mode Time | Speedup |
|----------|----------------|-----------------|----------------|---------|
| 100 | 0 | 100% | 100% | 1x |
| 100 | 50 | 50% | 100% | **2x** |
| 100 | 90 | 10% | 100% | **10x** |

---

## Next Steps

See full documentation: [CONDITIONAL_SCRAPING.md](./CONDITIONAL_SCRAPING.md)
