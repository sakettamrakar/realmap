from sqlalchemy import create_engine, text
import json

DB_URL = "postgresql://postgres:betsson%40123@localhost:5432/realmapdb"

def inspect_pricing(reg_num):
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        # Find project
        proj = conn.execute(text("SELECT id, project_name FROM projects WHERE rera_registration_number = :reg"), {"reg": reg_num}).fetchone()
        if not proj:
            print(f"Project {reg_num} not found")
            return
        
        print(f"Project: {proj.project_name} (ID: {proj.id})")
        
        # Get unit types
        units = conn.execute(text("SELECT id, base_price_inr, price_per_sqft_carpet, floor_plan_image_url FROM project_unit_types WHERE project_id = :pid"), {"pid": proj.id}).fetchall()
        
        print(f"Found {len(units)} unit types.")
        for u in units:
            print(f"- Unit ID: {u.id}, Price: {u.base_price_inr}, Price/Sqft: {u.price_per_sqft_carpet}, Image: {u.floor_plan_image_url}")

if __name__ == "__main__":
    inspect_pricing("PCGRERA270418000009")
