
import psycopg2
from decimal import Decimal
from datetime import date

def backfill_pricing():
    conn = psycopg2.connect("postgresql://postgres:betsson%40123@localhost:5432/realmapdb")
    cur = conn.cursor()
    
    # Get all projects with unit types
    cur.execute("SELECT DISTINCT project_id FROM unit_types")
    project_ids = [r[0] for r in cur.fetchall()]
    
    print(f"Found {len(project_ids)} projects with unit types.")
    
    for pid in project_ids:
        # Check if snapshot already exists
        cur.execute("SELECT count(*) FROM project_pricing_snapshots WHERE project_id = %s", (pid,))
        if cur.fetchone()[0] > 0:
            print(f"Project {pid} already has pricing snapshots. Skipping.")
            continue
            
        cur.execute("SELECT type_name, sale_price, carpet_area_sqmt FROM unit_types WHERE project_id = %s", (pid,))
        units = cur.fetchall()
        
        for name, price, area in units:
            if price is None:
                continue
                
            # Convert area to sqft
            area_sqft = Decimal(str(area)) * Decimal("10.764") if area else None
            price_per_sqft = price / area_sqft if (price and area_sqft) else None
            
            cur.execute("""
                INSERT INTO project_pricing_snapshots (
                    project_id, snapshot_date, unit_type_label, 
                    min_price_total, max_price_total, 
                    min_price_per_sqft, max_price_per_sqft,
                    source_type, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                pid, date.today(), name, 
                price, price, 
                price_per_sqft, price_per_sqft,
                "backfill_from_v1_unit_types", True
            ))
            
        print(f"Backfilled pricing for project {pid}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    backfill_pricing()
