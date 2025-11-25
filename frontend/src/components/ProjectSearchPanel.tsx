import ProjectCard from "./ProjectCard";
import SectionHeader from "./SectionHeader";
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

export function ProjectSearchPanel({
  filters,
  onFiltersChange,
  projects,
  loading,
  onSelectProject,
  selectedProjectId,
  total,
}: Props) {
  const handleReset = () => onFiltersChange({ district: "", minOverallScore: 0, nameQuery: "" });

  return (
    <div className="panel">
      <SectionHeader
        eyebrow="Filters"
        title="Projects"
        subtitle="Find projects by location, score, or name"
        actions={
          <button className="ghost-button" onClick={handleReset} type="button">
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
            placeholder="e.g. City, Heights, Realty"
            value={filters.nameQuery}
            onChange={(e) => onFiltersChange({ nameQuery: e.target.value })}
          />
        </label>
      </div>

      <div className="list-meta">
        <p className="eyebrow">
          Showing {projects.length} {total ? `of ${total}` : ""} projects
        </p>
        {loading && <div className="pill pill-muted">Loading…</div>}
      </div>

      <div className="project-list">
        {projects.map((project) => (
          <ProjectCard
            key={project.project_id}
            project={project}
            selected={project.project_id === selectedProjectId}
            onSelect={onSelectProject}
          />
        ))}
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
