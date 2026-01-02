# Database Changes Specification

## 1. New Tables

### `parent_projects`
Stores the canonical identity of a real estate project.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID/Serial | PK | Unique identifier |
| `name` | VARCHAR | NOT NULL | Canonical project name |
| `slug` | VARCHAR | UNIQUE | URL-friendly name |
| `full_address` | TEXT | NOT NULL | Canonical address |
| `promoter_name` | VARCHAR | NOT NULL | Canonical developer/promoter name |
| `locality_id` | INTEGER | FK | Link to `localities.id` |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation time |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update time |

---

## 2. Modified Tables

### `projects`
Updated to support the parent-child relationship.

| Change Type | Column | Type | Constraints |
| :--- | :--- | :--- | :--- |
| **Add Column** | `parent_project_id` | UUID/Serial | FK to `parent_projects.id` |
| **Add Index** | `idx_projects_parent_id` | - | Index for fast grouping |

---

## 3. Constraints & Indexes

### New Constraints
- **`uq_parent_project_identity`**: Unique constraint on `parent_projects(name, full_address, promoter_name)` to prevent duplicate parents.

### Existing Constraints (Preserved)
- **`uq_projects_state_reg_number`**: Remains on `projects(state_code, rera_registration_number)`. This ensures each RERA ID is only stored once.

---

## 4. SQL Migration Snippet (Conceptual)
```sql
-- 1. Create Parent Projects
CREATE TABLE parent_projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    slug VARCHAR UNIQUE,
    full_address TEXT NOT NULL,
    promoter_name VARCHAR NOT NULL,
    locality_id INTEGER REFERENCES localities(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. Add FK to Projects
ALTER TABLE projects ADD COLUMN parent_project_id INTEGER REFERENCES parent_projects(id);

-- 3. Create Index
CREATE INDEX idx_projects_parent_id ON projects(parent_project_id);
```
