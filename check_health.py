
import requests
import time
import sys

url = "http://localhost:8000/health"
max_retries = 10

for i in range(max_retries):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"Health check passed: {response.json()}")
            sys.exit(0)
        else:
            print(f"Health check failed: {response.status_code}")
    except Exception as e:
        print(f"Waiting for API... ({e})")
    time.sleep(2)

sys.exit(1)
