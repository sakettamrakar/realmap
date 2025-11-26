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

const formatPrice = (price: number) => {
  if (price >= 10000000) {
    return `${(price / 10000000).toFixed(2)} Cr`;
  }
  if (price >= 100000) {
    return `${(price / 100000).toFixed(2)} L`;
  }
  return price.toLocaleString("en-IN");
};

const getValueBadgeClass = (bucket?: string) => {
  switch (bucket) {
    case "excellent":
      return "value-badge value-excellent";
    case "good":
      return "value-badge value-good";
    case "fair":
      return "value-badge value-fair";
    case "poor":
      return "value-badge value-poor";
    default:
      return "value-badge value-unknown";
  }
};

const ProjectCard = ({
  project,
  selected,
  onSelect,
  onHover,
  hovered,
  isShortlisted,
  onToggleShortlist,
}: Props) => {
  const locationText = [project.village_or_locality, project.tehsil, project.district]
    .filter(Boolean)
    .join(", ");

  const typeText = project.project_type || "Project";
  const subTitle = `${typeText} in ${locationText || "Chhattisgarh"}`;

  const nearbyChips = [];
  if (project.nearby_counts?.schools) {
    nearbyChips.push(`${project.nearby_counts.schools} Schools`);
  }
  if (project.nearby_counts?.hospitals) {
    nearbyChips.push(`${project.nearby_counts.hospitals} Hospitals`);
  }
  if (project.nearby_counts?.transit) {
    nearbyChips.push(`${project.nearby_counts.transit} Transit points`);
  }

  return (
    <div
      className={classNames("project-card-new", { selected, hovered })}
      onMouseEnter={() => onHover?.(project.project_id)}
      onMouseLeave={() => onHover?.(null)}
      data-project-id={project.project_id}
    >
      <div className="card-content" onClick={() => onSelect(project.project_id)}>
        <div className="card-main">
          <div className="card-header-row">
            <div>
              <h3 className="card-title">{project.name}</h3>
              <p className="card-subtitle">{subTitle}</p>
            </div>
            <div className="card-score-block">
              <ScoreBadge
                score={project.overall_score}
                status={project.score_status}
                reason={project.score_status_reason}
                amenityScore={project.amenity_score}
                locationScore={project.location_score}
              />
            </div>
          </div>

          <div className="card-price-row">
            {project.min_price_total ? (
              <span className="price-tag">
                ₹{formatPrice(project.min_price_total)}
                {project.max_price_total &&
                  project.max_price_total !== project.min_price_total
                  ? ` – ${formatPrice(project.max_price_total)}`
                  : ""}
              </span>
            ) : (
              <span className="price-tag muted">Price on Request</span>
            )}
            {project.value_bucket && project.value_bucket !== "unknown" && (
              <span className={getValueBadgeClass(project.value_bucket)}>
                {project.value_bucket === "excellent" ? "High Value" :
                  project.value_bucket === "good" ? "Good Value" :
                    project.value_bucket === "fair" ? "Fair Value" : "Low Value"}
              </span>
            )}
          </div>

          <div className="card-meta-row">
            <span className="meta-item">
              <span className="icon">✓</span> RERA Verified
            </span>
            <span className="meta-item">
              • {project.status || "Status Unknown"}
            </span>
          </div>

          {nearbyChips.length > 0 && (
            <div className="card-poi-row">
              <span className="poi-label">Nearby:</span>
              {nearbyChips.slice(0, 3).map((chip, i) => (
                <span key={i} className="poi-chip">
                  {chip}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="card-actions">
        <button
          className="action-btn primary"
          onClick={(e) => {
            e.stopPropagation();
            onSelect(project.project_id);
          }}
        >
          View Details
        </button>
        {onToggleShortlist && (
          <button
            className={classNames("action-btn secondary", { active: isShortlisted })}
            onClick={(e) => {
              e.stopPropagation();
              onToggleShortlist(project, Boolean(isShortlisted));
            }}
          >
            {isShortlisted ? "Shortlisted ★" : "Shortlist ☆"}
          </button>
        )}
      </div>
    </div>
  );
};

export default ProjectCard;
