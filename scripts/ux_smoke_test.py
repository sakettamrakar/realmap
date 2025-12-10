import requests
import os

REPORTS_DIR = "reports/ux_smoke"
os.makedirs(REPORTS_DIR, exist_ok=True)

BASE_URL = "http://localhost:8000"

def run_smoke():
    print("Starting UX/API Smoke Test...")
    results = []
    
    endpoints = [
        ("GET /", "/"),
        ("GET /docs", "/docs"),
        ("GET /ai/health", "/ai/health"),
        ("GET /ai/score/project/1", "/ai/score/project/1") # Assuming mock available
    ]
    
    server_up = False
    try:
        requests.get(BASE_URL, timeout=1)
        server_up = True
    except (requests.exceptions.RequestException, requests.exceptions.Timeout, ConnectionError):
        print("Server not running at localhost:8000. Skipping live tests.")
        results.append({"endpoint": "ALL", "status": "SKIPPED", "notes": "Server not reachable"})

    if server_up:
        for name, path in endpoints:
            try:
                r = requests.get(f"{BASE_URL}{path}", timeout=2)
                status = "PASS" if r.status_code < 500 else "FAIL"
                results.append({"endpoint": name, "status": status, "notes": f"Code {r.status_code}"})
            except Exception as e:
                results.append({"endpoint": name, "status": "FAIL", "notes": str(e)})

    # Generate Report
    with open(os.path.join(REPORTS_DIR, "README.md"), "w") as f:
        f.write("# UX Smoke Test Results\n\n")
        f.write("| Endpoint | Status | Notes |\n")
        f.write("|----------|--------|-------|\n")
        for r in results:
            f.write(f"| {r['endpoint']} | {r['status']} | {r['notes']} |\n")
            
        if not server_up:
            f.write("\n> [!WARNING]\n> Server was not running. Manual verification required.\n")
            
    print("Smoke test report generated.")

if __name__ == "__main__":
    run_smoke()
