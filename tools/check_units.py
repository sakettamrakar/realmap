from cg_rera_extractor.db import get_session_local, Unit, get_engine
import sys

def main():
    try:
        engine = get_engine()
        SessionLocal = get_session_local(engine)
        with SessionLocal() as db:
            count = db.query(Unit).count()
            print(f"Units in DB: {count}")
    except Exception as e:
        print(f"Error checking units: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
