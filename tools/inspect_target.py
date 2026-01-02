
import json
path = r"c:\GIT\realmap\outputs\raipur-20\runs\run_20251210_090333_f88ae6\scraped_json\project_CG_PCGRERA270418000009.v1.json"
with open(path, 'r', encoding='utf-8-sig') as f:
    data = json.load(f)
    print(f"Keys: {list(data.get('raw_data', {}).get('tables', {}).keys())}")
