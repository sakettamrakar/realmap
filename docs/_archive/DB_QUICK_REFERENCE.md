ARCHIVED - superseded by docs/DB_GUIDE.md and README.md.

# DB Pipeline Quick Reference

## TL;DR - Three Commands

```bash
# 1. Initialize database schema
python tools/init_db.py

# 2. Load a run into the database
python tools/load_runs_to_db.py --latest

# 3. Verify data was loaded
python tools/check_db_counts.py
```

---

## Command Details

### Initialize Schema
```bash
python tools/init_db.py
```
**Shows**: Database name and list of created tables
**Do this once** before first load

---

### Load Data
```bash
# Load most recent run
python tools/load_runs_to_db.py --latest

# Load specific run by ID
python tools/load_runs_to_db.py --run-id run_20251117_142842_d3db76

# Load from custom directory
python tools/load_runs_to_db.py --runs-dir ./outputs/demo-run/runs --latest

# Load all runs in directory
python tools/load_runs_to_db.py
```
**Shows**: Database target, runs loaded, and summary of inserted records

---

### Verify Loaded Data
```bash
# Show total row counts
python tools/check_db_counts.py

# Show data for specific project
python tools/check_db_counts.py --project-reg PCGRERA240218000002

# Change state code (default: CG)
python tools/check_db_counts.py --state-code MH
```
**Shows**: Exact count of rows in each table

---

## Expected Output

### init_db.py
```
Initializing database schema...
Database target: localhost/realmapdb

✓ Schema initialized successfully!

Tables created (7 total):
  • buildings
  • project_documents
  • projects
  • promoters
  • quarterly_updates
  • testabc
  • unit_types
```

### load_runs_to_db.py
```
======================================================================
Database Loader
======================================================================
Database target: localhost/realmapdb
Runs directory:  C:\GIT\realmap\outputs\runs

Loading single run: run_20251117_142842_d3db76

======================================================================
Load Summary
======================================================================
Projects upserted:    2
Promoters inserted:   3
Buildings inserted:   5
Unit types inserted:  8
Documents inserted:   12
Quarterly updates:    4

✓ Load completed successfully!
```

### check_db_counts.py
```
======================================================================
Database Row Counts
======================================================================
Database: localhost/realmapdb

Total Rows:
  Projects:                   2
  Promoters:                  3
  Buildings:                  5
  Unit Types:                 8
  Documents:                  12
  Quarterly Updates:          4

  TOTAL RECORDS:              34

======================================================================
```

---

## Troubleshooting

**No runs found**: Check that run directories exist under `outputs/runs/` (format: `run_YYYYMMDD_HHMMSS_*`)

**0 rows loaded**: V1 JSON files might have empty required fields (registration_number, promoter_name, etc.)

**Database connection failed**: Verify Postgres is running and `DATABASE_URL` environment variable is set correctly

**Table creation failed**: Check database permissions and that `realmapdb` database exists

---

## Integration with System Check

DB verification is automatically included in the full system check:

```bash
python tools/system_full_check.py
```

This runs the complete pipeline verification including:
- Self-check
- Crawl test
- Database initialization
- Data loading
- **Database verification** (calls check_db_counts.py)
- API health check

---

## See Also

- `USER_GUIDE.md` - Complete user documentation
- `DB_PIPELINE_VERIFICATION.md` - Detailed verification guide
- `DB_DEBUG_SESSION_COMPLETION.md` - Session summary

