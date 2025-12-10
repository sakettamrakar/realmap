
import os
import sys
import pytest
import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from cg_rera_extractor.cli import main as cli_main
from cg_rera_extractor.db.base import Base
from cg_rera_extractor.db.loader import load_run_into_db
from cg_rera_extractor.db.models import Project

# Ensure root is in path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Read fixture data
DETAIL_PAGE_PATH = ROOT / "tests/qa/fixtures/detail_page.html"
DETAIL_PAGE_HTML = DETAIL_PAGE_PATH.read_text(encoding="utf-8")

SEARCH_PAGE_HTML = """
<html>
<body>
    <table id="ContentPlaceHolder1_gv_ProjectList">
        <tbody>
        <tr>
            <th>S.No.</th>
            <th>Project Name</th>
            <th>Promoter Name</th>
            <th>District</th>
            <th>Tehsil</th>
            <th>Status</th>
            <th>View Details</th>
            <th>Reg No</th>
        </tr>
        <tr>
            <td>1</td>
            <td>Garden Villas</td>
            <td>Test Promoter</td>
            <td>Raipur</td>
            <td>Raipur</td>
            <td>Ongoing</td>
            <td><a href="ProjectDetails.aspx?id=1">View</a></td>
            <td>CG-REG-001</td>
        </tr>
        <tr>
            <td>2</td>
            <td>City Heights</td>
            <td>Another Promoter</td>
            <td>Raipur</td>
            <td>Raipur</td>
            <td>Ongoing</td>
            <td><a href="ProjectDetails.aspx?id=2">View</a></td>
            <td>CG-REG-002</td>
        </tr>
        </tbody>
    </table>
</body>
</html>
"""

class MockBrowserSession:
    def __init__(self, config=None):
        self.current_html = ""
        self.current_url = ""
        self._page = MagicMock() # Mock the underlying page object if accessed

    def start(self):
        pass

    def goto(self, url: str):
        self.current_url = url
        if "Approved_project_List.aspx" in url:
            self.current_html = SEARCH_PAGE_HTML
        elif "ProjectDetails.aspx" in url:
            self.current_html = DETAIL_PAGE_HTML
        else:
            self.current_html = "<html></html>"

    def go_back(self):
        pass

    def fill(self, selector: str, value: str):
        pass

    def select_option(self, selector: str, value):
        pass

    def click(self, selector: str):
        pass

    def wait_for_selector(self, selector: str, timeout_ms: int = 10000):
        pass

    def get_page_html(self) -> str:
        return self.current_html

    def close(self):
        pass

    def current_page(self):
        return self._page

    def current_context(self):
        return MagicMock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

@pytest.fixture(scope="module")
def e2e_env(tmp_path_factory):
    """Sets up a temporary environment for the E2E test."""
    temp_dir = tmp_path_factory.mktemp("e2e_run")
    output_dir = temp_dir / "outputs"
    output_dir.mkdir()
    
    db_path = temp_dir / "test_realmap.db"
    db_url = f"sqlite:///{db_path}"
    
    base_config_path = ROOT / "config.realcrawl-2projects.yaml"
    with open(base_config_path, "r") as f:
        config_data = yaml.safe_load(f)
    
    config_data["run"]["output_base_dir"] = str(output_dir)
    config_data["db"]["url"] = db_url
    config_data["browser"]["headless"] = True 
    
    config_path = temp_dir / "e2e_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)
        
    return {
        "config_path": str(config_path),
        "output_dir": output_dir,
        "db_url": db_url,
        "temp_dir": temp_dir
    }

def test_e2e_crawl_and_db_load(e2e_env):
    """
    Runs the full crawler flow (mocked browser) and verifies DB insertion.
    """
    config_path = e2e_env["config_path"]
    db_url = e2e_env["db_url"]
    output_dir = e2e_env["output_dir"]
    
    print(f"\n[E2E] Starting crawl with config: {config_path}")
    
    # Patch the BrowserSession AND the captcha waiter in the orchestrator module
    # We patch where they are USED, because the module is already imported
    with patch("cg_rera_extractor.runs.orchestrator.PlaywrightBrowserSession", side_effect=MockBrowserSession), \
         patch("cg_rera_extractor.runs.orchestrator.wait_for_captcha_solved") as mock_wait:
        
        sys.argv = ["cg_rera_extractor.cli", "--config", config_path, "--mode", "full"]
        try:
            cli_main()
        except SystemExit as e:
            assert e.code == 0, "Crawler CLI exited with error code"
        except Exception as e:
            pytest.fail(f"Crawler failed with exception: {e}")

    # Verify artifacts
    runs_dir = output_dir / "runs"
    assert runs_dir.exists(), "Runs directory not created"
    
    run_dirs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], key=os.path.getmtime, reverse=True)
    assert len(run_dirs) > 0, "No run directory found"
    latest_run = run_dirs[0]
    print(f"[E2E] Latest run dir: {latest_run}")
    
    scraped_json_dir = latest_run / "scraped_json"
    assert scraped_json_dir.exists(), "scraped_json dir missing"
    
    json_files = list(scraped_json_dir.glob("*.json"))
    assert len(json_files) == 2, f"Expected 2 scraped JSON files, found {len(json_files)}"
    print(f"[E2E] Found {len(json_files)} scraped JSON files.")

    # --- Step 2: Initialize DB ---
    print(f"[E2E] Initializing DB at {db_url}")
    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    
    # --- Step 3: Load Data ---
    print("[E2E] Loading data into DB...")
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    session = SessionLocal()
    
    try:
        stats = load_run_into_db(str(latest_run), session=session)
        session.commit()
        print(f"[E2E] Load stats: {stats}")
        
        assert stats["projects_upserted"] == 2
    except Exception as e:
        session.rollback()
        pytest.fail(f"DB Loading failed: {e}")
    finally:
        session.close()

    # --- Step 4: Verify Data ---
    session = SessionLocal()
    try:
        # Check Projects
        projects = session.execute(select(Project)).scalars().all()
        assert len(projects) == 2, "Expected 2 projects in DB"
        
        p1 = next((p for p in projects if p.rera_registration_number == "CG-REG-001"), None)
        assert p1 is not None
        assert p1.project_name == "Garden Villas"
        
        p2 = next((p for p in projects if p.rera_registration_number == "CG-REG-002"), None)
        assert p2 is not None
        
        print(f"  - Found Project: {p1.project_name} ({p1.rera_registration_number})")
        print(f"  - Found Project: {p2.project_name} ({p2.rera_registration_number})")
        
    finally:
        session.close()
