
import sys
import os
import pytest
import yaml
import time
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from cg_rera_extractor.cli import main as cli_main
from cg_rera_extractor.db.base import Base
from cg_rera_extractor.db.loader import load_run_into_db
from cg_rera_extractor.db.models import Project, Promoter

# Ensure root is in path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@pytest.fixture(scope="module")
def interactive_env(tmp_path_factory):
    """Sets up the environment for interactive tests."""
    temp_dir = tmp_path_factory.mktemp("interactive_run")
    
    # Setup SQLite DB
    db_path = temp_dir / "interactive.db"
    db_url = f"sqlite:///{db_path}"
    
    # Initialize DB Schema
    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    
    return {
        "temp_dir": temp_dir,
        "db_url": db_url,
        "engine": engine
    }

def run_project_test(config_source_path, env, project_label):
    """Generic test runner for a project configuration."""
    print(f"\n=== Starting Interactive Test for {project_label} ===")
    
    # 1. Prepare Config
    with open(config_source_path, "r") as f:
        config_data = yaml.safe_load(f)
    
    output_dir = env["temp_dir"] / f"output_{project_label}"
    config_data["run"]["output_base_dir"] = str(output_dir)
    config_data["db"]["url"] = env["db_url"]
    config_data["browser"]["headless"] = False  # FORCE VISIBLE BROWSER
    
    test_config_path = env["temp_dir"] / f"config_{project_label}.yaml"
    with open(test_config_path, "w") as f:
        yaml.dump(config_data, f)
        
    # 2. Run Crawler
    # We invoke the CLI. It will pause for CAPTCHA.
    # The user must interact with the browser and terminal.
    sys.argv = ["cg_rera_extractor.cli", "--config", str(test_config_path), "--mode", "full"]
    
    print(f"[{project_label}] Launching crawler... Please watch for the browser window.")
    try:
        cli_main()
    except SystemExit as e:
        assert e.code == 0, f"[{project_label}] Crawler exited with error code {e.code}"
    
    # 3. Verify Artifacts
    runs_dir = output_dir / "runs"
    assert runs_dir.exists(), f"[{project_label}] No runs directory created"
    run_dirs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], key=os.path.getmtime, reverse=True)
    assert len(run_dirs) > 0, f"[{project_label}] No run folder found"
    latest_run = run_dirs[0]
    
    json_files = list((latest_run / "scraped_json").glob("*.json"))
    print(f"[{project_label}] Scraped {len(json_files)} projects.")
    assert len(json_files) > 0, f"[{project_label}] No data scraped. Did the search fail?"

    # 4. Load to DB
    print(f"[{project_label}] Loading data into DB...")
    SessionLocal = sessionmaker(bind=env["engine"], autocommit=False, autoflush=False, future=True)
    session = SessionLocal()
    try:
        stats = load_run_into_db(str(latest_run), session=session)
        session.commit()
        print(f"[{project_label}] DB Load Stats: {stats}")
        assert stats["projects_upserted"] > 0
    finally:
        session.close()

def test_raipur_ongoing(interactive_env):
    """Test Case 1: Raipur Ongoing Projects."""
    config_path = ROOT / "config.realcrawl-2projects.yaml"
    run_project_test(config_path, interactive_env, "raipur_ongoing")
    
    # Verify DB content
    session = sessionmaker(bind=interactive_env["engine"])()
    projects = session.execute(select(Project).where(Project.district == "Raipur")).scalars().all()
    assert len(projects) >= 1
    print(f"Verified {len(projects)} Raipur projects in DB.")
    session.close()

def test_durg_new(interactive_env):
    """Test Case 2: Durg New Projects."""
    config_path = ROOT / "config.test-durg.yaml"
    run_project_test(config_path, interactive_env, "durg_new")
    
    # Verify DB content
    session = sessionmaker(bind=interactive_env["engine"])()
    projects = session.execute(select(Project).where(Project.district == "Durg")).scalars().all()
    assert len(projects) >= 1
    print(f"Verified {len(projects)} Durg projects in DB.")
    session.close()

if __name__ == "__main__":
    # Allow running directly
    pytest.main([__file__, "-s"])
