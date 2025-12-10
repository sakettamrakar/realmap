
import requests
import sys

# We need Project ID. Using 2 from previous check.
PROJECT_ID = 2
URL = f"http://localhost:8001/ai/score/project/{PROJECT_ID}"

print(f"Calling Scoring Endpoint: {URL}")

try:
    # Post request
    # Note: AI service might take time to load model on first request
    response = requests.post(URL, timeout=300) # 5 min timeout for model load
    
    if response.status_code == 200:
        print("Success!")
        print(response.json())
        sys.exit(0)
    else:
        print(f"Failed: {response.status_code}")
        print(response.text)
        sys.exit(1)
        
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
