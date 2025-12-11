
from sqlalchemy import create_engine, text
from cg_rera_extractor.config.loader import load_config
import os
import logging

logging.basicConfig(level=logging.INFO)

config_path = "config.yaml" if os.path.exists("config.yaml") else "config.example.yaml"
app_config = load_config(config_path)
db_url = app_config.db.url
engine = create_engine(db_url)

with engine.connect() as conn:
    print(f"Connecting to {db_url.split('@')[-1]}") # redact password
    result = conn.execute(text("SELECT count(*) FROM rera_filings"))
    count = result.scalar()
    print(f"ReraFilings Count: {count}")
    
    if count > 0:
        row = conn.execute(text("SELECT * FROM rera_filings ORDER BY id DESC LIMIT 1")).fetchone()
        print(f"Latest Filing ID: {row.id}")
        print(f"File Path: {row.file_path}")
