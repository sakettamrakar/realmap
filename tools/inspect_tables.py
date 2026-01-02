
from pathlib import Path
import json

base_output = Path(r"c:\GIT\realmap\outputs")
v1_files = list(base_output.rglob("*.v1.json"))
print(f"Checking {len(v1_files)} files...")

for path in v1_files[:5]:
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            raw_data = data.get('raw_data', {})
            tables = raw_data.get('tables', {})
            print(f"\nFile: {path.name}")
            print(f"Table Keys: {list(tables.keys())}")
            
            # Print a sample of "Brief Details" if it exists
            for k in tables:
                if "brief" in k.lower():
                    print(f"Found Brief Table: {k}")
                    if tables[k]:
                        print(f"Headers: {tables[k][0].get('headers')}")
    except Exception as e:
        print(f"Error {path.name}: {e}")
