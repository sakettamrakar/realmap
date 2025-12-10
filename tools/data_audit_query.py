"""Database audit script for data quality analysis."""
from sqlalchemy import text
from cg_rera_extractor.db import get_engine

engine = get_engine()

with engine.connect() as conn:
    # Get all tables
    tables_result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """))
    tables = [row[0] for row in tables_result]
    print('=== TABLES ===')
    for t in tables:
        print(f'  {t}')
    
    print('\n=== TABLE COUNTS ===')
    for t in tables:
        try:
            count_result = conn.execute(text(f'SELECT COUNT(*) FROM "{t}"'))
            count = count_result.scalar()
            print(f'{t}: {count} rows')
        except Exception as e:
            print(f'{t}: ERROR - {e}')
    
    # Analyze projects table columns
    print('\n=== PROJECTS TABLE COLUMNS NULL ANALYSIS ===')
    columns_result = conn.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'projects' AND table_schema = 'public'
        ORDER BY ordinal_position
    """))
    columns = [(row[0], row[1], row[2]) for row in columns_result]
    
    total_result = conn.execute(text('SELECT COUNT(*) FROM projects'))
    total_projects = total_result.scalar() or 1
    
    for col_name, data_type, is_nullable in columns:
        try:
            null_result = conn.execute(text(f'SELECT COUNT(*) FROM projects WHERE "{col_name}" IS NULL'))
            null_count = null_result.scalar()
            null_pct = (null_count / total_projects) * 100 if total_projects > 0 else 0
            print(f'{col_name} ({data_type}): {null_count}/{total_projects} NULL ({null_pct:.1f}%)')
        except Exception as e:
            print(f'{col_name}: ERROR - {e}')
            
    # Analyze unit_types table
    print('\n=== UNIT_TYPES TABLE NULL ANALYSIS ===')
    ut_columns_result = conn.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns 
        WHERE table_name = 'unit_types' AND table_schema = 'public'
        ORDER BY ordinal_position
    """))
    ut_columns = [(row[0], row[1]) for row in ut_columns_result]
    
    ut_total_result = conn.execute(text('SELECT COUNT(*) FROM unit_types'))
    total_ut = ut_total_result.scalar() or 1
    
    for col_name, data_type in ut_columns:
        try:
            null_result = conn.execute(text(f'SELECT COUNT(*) FROM unit_types WHERE "{col_name}" IS NULL'))
            null_count = null_result.scalar()
            null_pct = (null_count / total_ut) * 100 if total_ut > 0 else 0
            print(f'{col_name} ({data_type}): {null_count}/{total_ut} NULL ({null_pct:.1f}%)')
        except Exception as e:
            print(f'{col_name}: ERROR - {e}')
            
    # Analyze promoters table
    print('\n=== PROMOTERS TABLE NULL ANALYSIS ===')
    prom_columns_result = conn.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns 
        WHERE table_name = 'promoters' AND table_schema = 'public'
        ORDER BY ordinal_position
    """))
    prom_columns = [(row[0], row[1]) for row in prom_columns_result]
    
    prom_total_result = conn.execute(text('SELECT COUNT(*) FROM promoters'))
    total_prom = prom_total_result.scalar() or 1
    
    for col_name, data_type in prom_columns:
        try:
            null_result = conn.execute(text(f'SELECT COUNT(*) FROM promoters WHERE "{col_name}" IS NULL'))
            null_count = null_result.scalar()
            null_pct = (null_count / total_prom) * 100 if total_prom > 0 else 0
            print(f'{col_name} ({data_type}): {null_count}/{total_prom} NULL ({null_pct:.1f}%)')
        except Exception as e:
            print(f'{col_name}: ERROR - {e}')
            
    # Analyze project_pricing_snapshots table
    print('\n=== PROJECT_PRICING_SNAPSHOTS TABLE NULL ANALYSIS ===')
    pps_columns_result = conn.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns 
        WHERE table_name = 'project_pricing_snapshots' AND table_schema = 'public'
        ORDER BY ordinal_position
    """))
    pps_columns = [(row[0], row[1]) for row in pps_columns_result]
    
    pps_total_result = conn.execute(text('SELECT COUNT(*) FROM project_pricing_snapshots'))
    total_pps = pps_total_result.scalar() or 1
    
    for col_name, data_type in pps_columns:
        try:
            null_result = conn.execute(text(f'SELECT COUNT(*) FROM project_pricing_snapshots WHERE "{col_name}" IS NULL'))
            null_count = null_result.scalar()
            null_pct = (null_count / total_pps) * 100 if total_pps > 0 else 0
            print(f'{col_name} ({data_type}): {null_count}/{total_pps} NULL ({null_pct:.1f}%)')
        except Exception as e:
            print(f'{col_name}: ERROR - {e}')
            
    # Analyze project_scores table
    print('\n=== PROJECT_SCORES TABLE NULL ANALYSIS ===')
    ps_columns_result = conn.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns 
        WHERE table_name = 'project_scores' AND table_schema = 'public'
        ORDER BY ordinal_position
    """))
    ps_columns = [(row[0], row[1]) for row in ps_columns_result]
    
    ps_total_result = conn.execute(text('SELECT COUNT(*) FROM project_scores'))
    total_ps = ps_total_result.scalar() or 1
    
    for col_name, data_type in ps_columns:
        try:
            null_result = conn.execute(text(f'SELECT COUNT(*) FROM project_scores WHERE "{col_name}" IS NULL'))
            null_count = null_result.scalar()
            null_pct = (null_count / total_ps) * 100 if total_ps > 0 else 0
            print(f'{col_name} ({data_type}): {null_count}/{total_ps} NULL ({null_pct:.1f}%)')
        except Exception as e:
            print(f'{col_name}: ERROR - {e}')
