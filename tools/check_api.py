
import requests
import json
try:
    # Assuming the API is running on localhost:8000
    r = requests.get("http://localhost:8000/projects/2/inventory")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"API Check failed (is server running?): {e}")
