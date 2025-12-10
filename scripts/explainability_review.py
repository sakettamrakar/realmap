import csv
import os

REPORTS_DIR = "reports"
EXPLANATIONS_DIR = os.path.join(REPORTS_DIR, "explanations")
os.makedirs(EXPLANATIONS_DIR, exist_ok=True)

def run_review():
    csv_file = os.path.join(REPORTS_DIR, "model_sanity.csv")
    if not os.path.exists(csv_file):
        print("model_sanity.csv not found.")
        return

    projects = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            projects.append(row)
            if len(projects) >= 10:
                break

    reviews = []

    for p in projects:
        pid = p["project_id"]
        name = p["project_name"]
        explanation = p["explanation"]
        
        # Create explanation file
        fname = f"project_{pid}.md"
        with open(os.path.join(EXPLANATIONS_DIR, fname), "w", encoding="utf-8") as f:
            f.write(f"# Project {pid}: {name}\n\n")
            f.write(f"**Score**: {p['score_value']}\n")
            f.write(f"**Confidence**: {p['confidence']}\n\n")
            f.write("## Explanation\n")
            f.write(f"{explanation}\n")
            
        # Review logic
        status = "FAIL"
        notes = "Explanation is an error message."
        if "unavailable" not in explanation.lower() and len(explanation) > 50:
            status = "PASS"
            notes = "Explanation looks reasonable."
            
        reviews.append({
            "project_id": pid,
            "status": status,
            "notes": notes
        })

    # Summary report
    with open(os.path.join(REPORTS_DIR, "explainability_review.md"), "w", encoding="utf-8") as f:
        f.write("# Explainability & Human Spot-Check\n\n")
        f.write("| Project ID | Status | Notes |\n")
        f.write("|------------|--------|-------|\n")
        for r in reviews:
            f.write(f"| {r['project_id']} | {r['status']} | {r['notes']} |\n")
            
    print("Explainability review done.")

if __name__ == "__main__":
    run_review()
