import classNames from "classnames";
import ScoreBadge from "./ScoreBadge";
import type { ProjectSummary } from "../types/projects";

interface Props {
  project: ProjectSummary;
  selected?: boolean;
  onSelect: (projectId: number) => void;
  onHover?: (projectId: number | null) => void;
  hovered?: boolean;
}

const formatScore = (score?: number | null) =>
  score === undefined || score === null ? "–" : score.toFixed(2);

const ProjectCard = ({ project, selected, onSelect, onHover, hovered }: Props) => {
  return (
    <button
      className={classNames("project-card", { selected, hovered })}
      onClick={() => onSelect(project.project_id)}
      onMouseEnter={() => onHover?.(project.project_id)}
      onMouseLeave={() => onHover?.(null)}
      data-project-id={project.project_id}
    >
      <div className="card-header">
        <div className="card-title-group">
          <p className="eyebrow">{project.district || "District unknown"}</p>
          <h3>{project.name}</h3>
          {(project.tehsil || project.project_type) && (
            <p className="muted">
              {[project.tehsil, project.project_type].filter(Boolean).join(" · ")}
            </p>
          )}
        </div>
        <div className="badge-stack">
          {onToggleShortlist && (
            <button
              type="button"
              className={classNames("shortlist-button", {
                active: isShortlisted,
              })}
              aria-label={isShortlisted ? "Remove from shortlist" : "Add to shortlist"}
              onClick={(event) => {
                event.stopPropagation();
                onToggleShortlist(project, Boolean(isShortlisted));
              }}
            >
              {isShortlisted ? "★" : "☆"}
            </button>
          )}
          <ScoreBadge score={project.overall_score} />
          <span className="status-pill">{project.status || "Status unknown"}</span>
        </div>
      </div>

      <div className="card-meta-grid">
        <div>
          <p className="eyebrow">Location</p>
          <p className="value">{formatScore(project.location_score)}</p>
        </div>
        <div>
          <p className="eyebrow">Amenities</p>
          <p className="value">{formatScore(project.amenity_score)}</p>
        </div>
        <div>
          <p className="eyebrow">Units</p>
          <p className="value">{project.units ?? "—"}</p>
        </div>
        {project.distance_km != null && (
          <div>
            <p className="eyebrow">From reference</p>
            <p className="value">{project.distance_km.toFixed(1)} km</p>
          </div>
        )}
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
};

export default ProjectCard;
