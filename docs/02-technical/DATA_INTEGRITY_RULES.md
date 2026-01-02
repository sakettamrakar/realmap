# Data Integrity Rules & Deduplication Strategy

## 1. Identity Rules

### Parent Project Identity
A **Parent Project** is uniquely identified by the combination of:
1. `project_name` (Normalized)
2. `full_address` (Normalized)
3. `promoter_name` (Normalized)

*Rule: If these three match, they belong to the same physical project.*

### RERA Registration Identity
A **Project Registration** (Child) is uniquely identified by:
1. `state_code`
2. `rera_registration_number`

---

## 2. Normalization Requirements
To prevent "False Negatives" (duplicates that don't match due to formatting), the following normalization must be applied before comparison:
- **Case**: Convert to UPPERCASE.
- **Whitespace**: Trim leading/trailing spaces; collapse multiple spaces into one.
- **Special Characters**: Remove dots, commas, and dashes from names for comparison purposes.
- **Address**: Use geocoded coordinates (Latitude/Longitude) as a secondary validation if the address string differs slightly.

---

## 3. UPSERT Strategy

### Step 1: Parent Resolution
```python
parent = session.query(ParentProject).filter_by(
    name=normalized_name,
    address=normalized_address,
    promoter=normalized_promoter
).first()

if not parent:
    parent = ParentProject(...)
    session.add(parent)
    session.flush()
```

### Step 2: Registration UPSERT
```python
stmt = insert(Project).values(
    rera_registration_number=reg_num,
    parent_project_id=parent.id,
    ...
)
stmt = stmt.on_conflict_do_update(
    constraint='uq_projects_state_reg_number',
    set_={...}
)
session.execute(stmt)
```

---

## 4. Enforcement Layers
1. **Database Level**: Unique constraints on `parent_projects` and `projects`.
2. **Application Level**: Normalization service used by both Ingestion and Search.
3. **QA Level**: Periodic "Fuzzy Match" jobs to flag potential duplicates that escaped exact matching (e.g., "Overseas Palm" vs "Overseas Palm Resorts").
