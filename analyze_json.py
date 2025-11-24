import json
import sys
from pathlib import Path

def analyze_json(file_path):
    try:
        data = json.loads(Path(file_path).read_text(encoding='utf-8'))
        print(f"Top level keys: {list(data.keys())}")
        
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"\nKey: {key}")
                print(f"  Subkeys: {list(value.keys())}")
                # Print a few values to check for "Preview"
                for k, v in list(value.items())[:3]:
                    print(f"  {k}: {v}")
            elif isinstance(value, list):
                print(f"\nKey: {key} (List of {len(value)} items)")
                if value:
                    print(f"  Item 0 keys: {list(value[0].keys())}")
                    # Check for "Preview"
                    print(f"  Item 0 sample: {value[0]}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Redirect stdout to a file
        with open('analysis_result.txt', 'w', encoding='utf-8') as f:
            sys.stdout = f
            analyze_json(sys.argv[1])
