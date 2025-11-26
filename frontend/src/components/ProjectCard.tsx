import classNames from "classnames";
import ScoreBadge from "./ScoreBadge";
import type { ProjectSummary } from "../types/projects";

interface Props {
  project: ProjectSummary;
  selected?: boolean;
  onSelect: (projectId: number) => void;
  onHover?: (projectId: number | null) => void;
  hovered?: boolean;
  isShortlisted?: boolean;
  onToggleShortlist?: (project: ProjectSummary, wasShortlisted: boolean) => void;
}

const formatScore = (score?: number | null) =>
  score === undefined || score === null ? "–" : score.toFixed(2);

const formatPrice = (price: number) => {
  if (price >= 10000000) {
    return `${(price / 10000000).toFixed(2)} Cr`;
  }
  if (price >= 100000) {
    return `${(price / 100000).toFixed(2)} L`;
  }
  return price.toLocaleString("en-IN");
};

const ProjectCard = ({ project, selected, onSelect, onHover, hovered, isShortlisted, onToggleShortlist }: Props) => {
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
          <ScoreBadge score={project.overall_score} status={project.score_status} reason={project.score_status_reason} />
          <span className="status-pill">{project.status || "Status unknown"}</span>
        </div>
      </div>

      <div className="card-meta-grid">
        <div>
          <p className="eyebrow">Price</p>
          <p className="value">
            {project.min_price_total ? (
              <>
                ₹{formatPrice(project.min_price_total)}
                {project.max_price_total && project.max_price_total !== project.min_price_total ? `–${formatPrice(project.max_price_total)}` : ""}
              </>
            ) : (
              <span className="muted">N/A</span>
            )}
          </p>
        </div>
        <div>
          <p className="eyebrow">Location</p>
          <p className="value">{formatScore(project.location_score)}</p>
        </div>
        <div>
          <p className="eyebrow">Amenities</p>
          <p className="value">{formatScore(project.amenity_score)}</p>
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
