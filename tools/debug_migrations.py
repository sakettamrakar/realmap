import traceback
from sqlalchemy.exc import SQLAlchemyError
from cg_rera_extractor.db.init_db import init_db

try:
    init_db()
    print("Migrations applied successfully.")
except SQLAlchemyError as e:
    print("SQLAlchemy Error:")
    print(str(e))
    if hasattr(e, 'orig'):
        print("Original Error:")
        print(e.orig)
except Exception:
    traceback.print_exc()
