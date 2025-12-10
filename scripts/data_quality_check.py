import sys
import os
import json
import csv
import logging
from datetime import datetime
from sqlalchemy import text
import statistics

# Ensure project root is in path
sys.path.append(os.getcwd())

from cg_rera_extractor.db import get_engine, get_session_local
from ai.features.builder import build_feature_pack
from ai.scoring.logic import score_project_quality

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

def run_checks():
    logger.info("Starting Data & Model Sanity Run...")
    
    engine = get_engine()
    SessionLocal = get_session_local(engine)
    session = SessionLocal()
    
    # 1. Select 100 recent projects
    logger.info("Selecting 100 recent projects...")
    query = text("SELECT id, project_name, district, status FROM projects ORDER BY id DESC LIMIT 100")
    projects = session.execute(query).fetchall()
    
    if not projects:
        logger.error("No projects found in DB!")
        return

    project_ids = [p.id for p in projects]
    logger.info(f"Selected {len(project_ids)} projects.")

    # 2. Data Quality Metrics
    logger.info("Computing data quality metrics...")
    quality_issues = []
    
    # Define required fields
    required_fields = ["project_name", "district", "status"]
    
    null_counts = {f: 0 for f in required_fields}
    total_projects = len(projects)
    
    for p in projects:
        # Check nulls
        for f in required_fields:
            if getattr(p, f) is None:
                null_counts[f] += 1
                quality_issues.append({"project_id": p.id, "issue": f"Missing {f}"})
                
    # Null percentages
    null_pcts = {f: (count / total_projects) * 100 for f, count in null_counts.items()}
    
    dq_report = {
        "sample_size": total_projects,
        "null_percentages": null_pcts,
        "quality_issues_count": len(quality_issues),
        "failing_projects": [q["project_id"] for q in quality_issues]
    }
    
    with open(os.path.join(REPORTS_DIR, "data_quality_report.json"), "w") as f:
        json.dump(dq_report, f, indent=2)
        
    logger.info("Data quality report saved.")

    # 3. Run AI Microservice & 4. Model Sanity CSV
    logger.info("Running AI microservice (mock/real)...")
    
    model_sanity_rows = []
    scores = []
    confidences = []
    
    csv_file = os.path.join(REPORTS_DIR, "model_sanity.csv")
    
    with open(csv_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["project_id", "project_name", "score_value", "confidence", "explanation", "tokens_used", "model_name", "status"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for pid in project_ids:
            try:
                # Build features
                # Note: build_feature_pack needs a session or uses its own. 
                # Assuming it works with the session we have or creates one. 
                # Looking at test code, it takes db arg or uses default.
                # Let's pass our session if pos, or let it do its thing.
                # Actually build_feature_pack(project_id, db=...) signature seen in test.
                
                features = build_feature_pack(pid, db=session)
                
                # logic.score_project_quality(features)
                result = score_project_quality(features.features) # features is a Snapshot object, .features is dict?
                
                score_val = result.get("score")
                conf = result.get("confidence")
                expl = result.get("explanation")
                meta = result.get("metadata", {})
                
                row = {
                    "project_id": pid,
                    "project_name": features.features.get("name"),
                    "score_value": score_val,
                    "confidence": conf,
                    "explanation": expl,
                    "tokens_used": meta.get("tokens_used", 0),
                    "model_name": meta.get("model_name", "unknown"),
                    "status": "SUCCESS"
                }
                
                writer.writerow(row)
                model_sanity_rows.append(row)
                
                if score_val is not None:
                    scores.append(score_val)
                if conf is not None:
                    confidences.append(conf)
                    
            except Exception as e:
                logger.error(f"Error scoring project {pid}: {e}")
                writer.writerow({
                    "project_id": pid,
                    "status": f"ERROR: {str(e)}"
                })

    # 5. Summary Stats
    if scores:
        mean_score = statistics.mean(scores)
        std_score = statistics.stdev(scores) if len(scores) > 1 else 0
        low_conf_count = sum(1 for c in confidences if c < 0.4)
        low_conf_pct = (low_conf_count / len(confidences)) * 100
    else:
        mean_score = 0
        std_score = 0
        low_conf_pct = 0

    # 6. Audit Report
    audit_file = os.path.join(REPORTS_DIR, "data_model_audit.md")
    with open(audit_file, "w") as f:
        f.write("# Data & Model Audit Report\n\n")
        f.write(f"**Date**: {datetime.now().isoformat()}\n")
        f.write(f"**Sample Size**: {total_projects}\n\n")
        
        f.write("## Data Quality\n")
        f.write(f"- Null Percentages: {null_pcts}\n")
        f.write(f"- Issues Found: {len(quality_issues)}\n\n")
        
        f.write("## Model Sanity\n")
        f.write(f"- Mean Score: {mean_score:.2f}\n")
        f.write(f"- Std Dev: {std_score:.2f}\n")
        f.write(f"- Low Confidence (<0.4): {low_conf_pct:.2f}%\n")
        
        if low_conf_pct > 20:
            f.write("\n> [!IMPORTANT]\n> ACTION REQUIRED: Low confidence rate is too high (>20%).\n")
        
        f.write("\n## Recommendations\n")
        if null_pcts.get("district", 0) > 20:
            f.write("- Fix district extraction logic.\n")
        if low_conf_pct > 20:
             f.write("- Investigate model prompts for low confidence cases.\n")

    logger.info("Done.")
    session.close()

if __name__ == "__main__":
    try:
        run_checks()
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Fatal error: {e}")
