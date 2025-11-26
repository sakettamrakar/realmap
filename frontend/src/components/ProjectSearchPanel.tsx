import { useEffect } from "react";
import ProjectCard from "./ProjectCard";
import SectionHeader from "./SectionHeader";
import type { Filters } from "../types/filters";
import type { ProjectSummary } from "../types/projects";

const sortOptions: {
  value: Filters["sortBy"];
  label: string;
  defaultDir: Filters["sortDir"];
}[] = [
  { value: "overall_score", label: "Best overall score", defaultDir: "desc" },
  { value: "location_score", label: "Best location score", defaultDir: "desc" },
  { value: "registration_date", label: "Latest registration", defaultDir: "desc" },
  { value: "name", label: "Name A–Z", defaultDir: "asc" },
];

const districtOptions = [
  "",
  "Raipur",
  "Durg",
  "Bilaspur",
  "Korba",
  "Rajnandgaon",
  "Raigarh",
  "Dhamtari",
  "Surguja",
  "Bastar",
  "Kanker",
];

interface Props {
  filters: Filters;
  onFiltersChange: (next: Partial<Filters>) => void;
  projects: ProjectSummary[];
  loading?: boolean;
  onSelectProject: (projectId: number) => void;
  onHoverProject?: (projectId: number | null) => void;
  selectedProjectId?: number | null;
  hoveredProjectId?: number | null;
  total?: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onResetFilters: () => void;
  defaultFilters: Filters;
}

export function ProjectSearchPanel({
  filters,
  onFiltersChange,
  projects,
  loading,
  onSelectProject,
  onHoverProject,
  selectedProjectId,
  hoveredProjectId,
  total,
  page,
  pageSize,
  onPageChange,
  onResetFilters,
  defaultFilters,
}: Props) {
  const totalPages = Math.max(1, Math.ceil((total ?? 0) / (pageSize || 1)));

  useEffect(() => {
    if (!hoveredProjectId) return;
    const el = document.querySelector(
      `[data-project-id="${hoveredProjectId}"]`,
    ) as HTMLElement | null;
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [hoveredProjectId]);

  const activeChips: { key: string; label: string; onRemove: () => void }[] = [];

  if (filters.district) {
    activeChips.push({
      key: "district",
      label: `District: ${filters.district}`,
      onRemove: () => onFiltersChange({ district: "" }),
    });
  }

  if (filters.minOverallScore > 0) {
    activeChips.push({
      key: "min-score",
      label: `Min score: ${filters.minOverallScore.toFixed(2)}`,
      onRemove: () => onFiltersChange({ minOverallScore: defaultFilters.minOverallScore }),
    });
  }

  if (filters.nameQuery.trim()) {
    activeChips.push({
      key: "search",
      label: `Search: "${filters.nameQuery}"`,
      onRemove: () => onFiltersChange({ nameQuery: defaultFilters.nameQuery }),
    });
  }

  const sortLabel = sortOptions.find((option) => option.value === filters.sortBy)?.label;
  if (
    filters.sortBy !== defaultFilters.sortBy ||
    filters.sortDir !== defaultFilters.sortDir
  ) {
    activeChips.push({
      key: "sort",
      label: `Sort: ${sortLabel ?? filters.sortBy} (${filters.sortDir})`,
      onRemove: () =>
        onFiltersChange({
          sortBy: defaultFilters.sortBy,
          sortDir: defaultFilters.sortDir,
        }),
    });
  }

  const handleSortChange = (value: Filters["sortBy"]) => {
    const selected = sortOptions.find((option) => option.value === value);
    onFiltersChange({
      sortBy: value,
      sortDir: selected?.defaultDir ?? filters.sortDir,
    });
  };

  return (
    <div className="panel">
      <SectionHeader
        eyebrow="Filters"
        title="Projects"
        subtitle="Find projects by location, score, or name"
        actions={
          <button className="ghost-button" onClick={onResetFilters} type="button">
            Reset filters
          </button>
        }
      />

      <div className="filter-group">
        <p className="group-title">Location Filters</p>
        <div className="filter-row">
          <label className="field">
            <span>District</span>
            <select
              value={filters.district}
              onChange={(e) => onFiltersChange({ district: e.target.value })}
            >
              {districtOptions.map((district) => (
                <option key={district || "all"} value={district}>
                  {district || "All districts"}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Tehsil (optional)</span>
            <input type="text" placeholder="Enter tehsil" disabled value="" />
          </label>
        </div>
      </div>

      <div className="filter-group">
        <p className="group-title">Sorting</p>
        <div className="filter-row">
          <label className="field">
            <span>Sort by</span>
            <div className="sort-controls">
              <select
                value={filters.sortBy}
                onChange={(e) => handleSortChange(e.target.value as Filters["sortBy"])}
              >
                {sortOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="ghost-button sort-toggle"
                onClick={() =>
                  onFiltersChange({ sortDir: filters.sortDir === "asc" ? "desc" : "asc" })
                }
                aria-label="Toggle sort direction"
              >
                {filters.sortDir === "asc" ? "Asc ↑" : "Desc ↓"}
              </button>
            </div>
          </label>
        </div>
      </div>

      <div className="filter-group">
        <p className="group-title">Scores</p>
        <label className="field">
          <span>Min overall score</span>
          <div className="field-range">
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={filters.minOverallScore}
              onChange={(e) => onFiltersChange({ minOverallScore: Number(e.target.value) })}
            />
            <span className="range-value">{filters.minOverallScore.toFixed(2)}</span>
          </div>
        </label>
      </div>

      <div className="filter-group">
        <p className="group-title">Search</p>
        <label className="field">
          <span>Project or promoter</span>
          <input
            type="text"
            placeholder="Search by project or promoter…"
            value={filters.nameQuery}
            onChange={(e) => onFiltersChange({ nameQuery: e.target.value })}
          />
        </label>
      </div>

      {activeChips.length > 0 && (
        <div className="chip-row" aria-label="Active filters">
          {activeChips.map((chip) => (
            <button
              key={chip.key}
              className="filter-chip"
              type="button"
              onClick={chip.onRemove}
              aria-label={`Remove ${chip.label} filter`}
            >
              <span>{chip.label}</span>
              <span aria-hidden="true">×</span>
            </button>
          ))}
        </div>
      )}

      <div className="list-meta">
        <p className="eyebrow">
          Showing {projects.length} {total ? `of ${total}` : ""} projects
        </p>
        <div className="meta-actions">
          <div className="pill pill-muted">Page {page} of {totalPages}</div>
          {loading && <div className="pill pill-muted">Loading…</div>}
        </div>
      </div>

      <div className="project-list">
        {loading && projects.length === 0 && (
          <>
            {[1, 2, 3].map((placeholder) => (
              <div key={placeholder} className="project-card skeleton-card">
                <div className="skeleton skeleton-title" />
                <div className="skeleton skeleton-text" />
                <div className="skeleton skeleton-text" />
              </div>
            ))}
          </>
        )}

        {projects.map((project) => (
          <ProjectCard
            key={project.project_id}
            project={project}
            selected={project.project_id === selectedProjectId}
            hovered={project.project_id === hoveredProjectId}
            onSelect={onSelectProject}
            onHover={onHoverProject}
          />
        ))}
        {!loading && projects.length === 0 && (
          <div className="empty-state">
            <p>No projects match these filters.</p>
            <p className="eyebrow">Try relaxing filters or clearing search.</p>
          </div>
        )}
      </div>

      <div className="pagination">
        <button
          type="button"
          className="ghost-button"
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={page <= 1 || loading}
        >
          Previous
        </button>
        <span className="muted">
          Page {page} of {totalPages}
        </span>
        <button
          type="button"
          className="ghost-button"
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
          disabled={page >= totalPages || loading}
        >
          Next
        </button>
      </div>
    </div>
  );
}

export default ProjectSearchPanel;
