import type { Filters } from "../types/filters";
import type { ProjectSummary } from "../types/projects";

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
  selectedProjectId?: number | null;
  total?: number;
}

const formatScore = (score?: number) =>
  score === undefined || score === null ? "–" : score.toFixed(2);

export function ProjectSearchPanel({
  filters,
  onFiltersChange,
  projects,
  loading,
  onSelectProject,
  selectedProjectId,
  total,
}: Props) {
  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Filters</p>
          <h2>Projects</h2>
        </div>
        {loading && <div className="pill pill-muted">Loading…</div>}
      </div>

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
          <span>Min overall score</span>
          <div className="field-range">
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={filters.minOverallScore}
              onChange={(e) =>
                onFiltersChange({ minOverallScore: Number(e.target.value) })
              }
            />
            <span className="range-value">
              {filters.minOverallScore.toFixed(2)}
            </span>
          </div>
        </label>
      </div>

      <label className="field">
        <span>Project name contains</span>
        <input
          type="text"
          placeholder="e.g. City, Heights"
          value={filters.nameQuery}
          onChange={(e) => onFiltersChange({ nameQuery: e.target.value })}
        />
      </label>

      <div className="list-meta">
        <p className="eyebrow">
          Showing {projects.length} {total ? `of ${total}` : ""} projects
        </p>
      </div>

      <div className="project-list">
        {projects.map((project) => {
          const isSelected = project.project_id === selectedProjectId;
          return (
            <button
              key={project.project_id}
              className={`project-card ${isSelected ? "selected" : ""}`}
              onClick={() => onSelectProject(project.project_id)}
            >
              <div className="card-header">
                <div>
                  <p className="eyebrow">{project.district}</p>
                  <h3>{project.name}</h3>
                </div>
                <div className="pill">{formatScore(project.overall_score)}</div>
              </div>
              <div className="card-meta">
                <span>{project.status || "Status unknown"}</span>
                {project.project_type && <span>· {project.project_type}</span>}
                {project.distance_km != null && (
                  <span>· {project.distance_km.toFixed(1)} km</span>
                )}
              </div>
              <div className="score-row">
                <div>
                  <p className="eyebrow">Location</p>
                  <p>{formatScore(project.location_score)}</p>
                </div>
                <div>
                  <p className="eyebrow">Amenities</p>
                  <p>{formatScore(project.amenity_score)}</p>
                </div>
                <div>
                  <p className="eyebrow">Units</p>
                  <p>{project.units ?? "—"}</p>
                </div>
              </div>
              {project.highlight_amenities && project.highlight_amenities.length > 0 && (
                <div className="tag-row">
                  {project.highlight_amenities.slice(0, 4).map((amenity) => (
                    <span key={amenity} className="pill pill-muted">
                      {amenity}
                    </span>
                  ))}
                </div>
              )}
            </button>
          );
        })}
        {!loading && projects.length === 0 && (
          <div className="empty-state">
            <p>No projects match these filters yet.</p>
            <p className="eyebrow">Try widening the district or lowering the score.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default ProjectSearchPanel;
