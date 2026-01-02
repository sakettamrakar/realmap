from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:betsson%40123@localhost:5432/realmapdb"

def update_pricing():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text("UPDATE project_unit_types SET base_price_inr=4500000, price_per_sqft_carpet=4500 WHERE id=4"))
            conn.execute(text("UPDATE project_unit_types SET base_price_inr=6500000, price_per_sqft_carpet=5500 WHERE id=5"))
            print("Successfully updated and committed unit pricing.")

if __name__ == "__main__":
    update_pricing()
