
import classNames from "classnames";
import ScoreBadge from "./ScoreBadge";
import { Card, CardBody, CardFooter } from "./ui/Card";
import { Button } from "./ui/Button";
import { AnomalyBadge } from "./ai/AnomalyBadge";
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

const getValueBadgeInfo = (bucket?: string) => {
  switch (bucket) {
    case "excellent":
      return { label: "High Value", className: "bg-emerald-50 text-emerald-700 border-emerald-200" };
    case "good":
      return { label: "Good Value", className: "bg-sky-50 text-sky-700 border-sky-200" };
    case "fair":
      return { label: "Fair Value", className: "bg-amber-50 text-amber-700 border-amber-200" };
    case "poor":
      return { label: "Low Value", className: "bg-rose-50 text-rose-700 border-rose-200" };
    default:
      return { label: "Unknown Value", className: "bg-slate-50 text-slate-500 border-slate-200" };
  }
};

const ProjectCard = ({
  project,
  selected,
  onSelect,
  onHover,
  // hovered, // Not explicitly used for styling in the new design if we use group-hover but good to keep props consistent
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

  const valueInfo = project.value_bucket && project.value_bucket !== "unknown" ? getValueBadgeInfo(project.value_bucket) : null;

  return (
    <Card
      className={classNames("h-full flex flex-col overflow-hidden", { "ring-2 ring-sky-500 border-sky-500": selected })}
      hoverEffect={true}
      onClick={() => onSelect(project.project_id)}
    >
      <div
        className="flex-1"
        onMouseEnter={() => onHover?.(project.project_id)}
        onMouseLeave={() => onHover?.(null)}
      >
        <CardBody className="flex flex-col h-full">
          <div className="flex justify-between items-start mb-4 gap-3">
            <div className="min-w-0 flex-1">
              <h3 className="font-bold text-lg text-slate-900 line-clamp-1 group-hover:text-sky-600 transition-colors">
                {project.name}
              </h3>
              <p className="text-sm text-slate-500 line-clamp-1 mt-0.5">{subTitle}</p>
            </div>
            <div className="shrink-0">
              <ScoreBadge
                score={project.overall_score}
                status={project.score_status}
                reason={project.score_status_reason}
                amenityScore={project.amenity_score}
                locationScore={project.location_score}
              />
            </div>
          </div>

          <div className="flex items-center gap-3 mb-4 flex-wrap">
            {project.min_price_total ? (
              <span className="text-lg font-bold text-slate-900">
                ₹{formatPrice(project.min_price_total)}
                {project.max_price_total &&
                  project.max_price_total !== project.min_price_total
                  ? ` – ${formatPrice(project.max_price_total)}`
                  : ""}
              </span>
            ) : (
              <span className="text-sm font-medium text-slate-400 italic">Price on Request</span>
            )}

            {valueInfo && (
              <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${valueInfo.className}`}>
                {valueInfo.label}
              </span>
            )}
          </div>

          <div className="flex items-center gap-4 text-xs font-medium text-slate-500 mb-4 border-t border-slate-100 pt-3">
            <span className="flex items-center gap-1.5 text-emerald-600 bg-emerald-50 px-2 py-1 rounded-md border border-emerald-100">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
              RERA Verified
            </span>
            <span className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-slate-50 border border-slate-200">
              <span className={`w-1.5 h-1.5 rounded-full ${project.status === 'Completed' ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
              {project.status || "Status Unknown"}
            </span>
            {project.phase_count && project.phase_count > 1 && (
              <span className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-sky-50 border border-sky-200 text-sky-700 font-bold">
                {project.phase_count} Phases
              </span>
            )}
            {/* Feature 5: Anomaly Detection Badge */}
            <AnomalyBadge
              pricePerSqft={project.min_price_per_sqft}
              carpetArea={project.area_sqft}
              unitType={project.project_type}
              totalPrice={project.min_price_total}
            />
          </div>

          {nearbyChips.length > 0 && (
            <div className="mt-auto">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Nearby Highlights</div>
              <div className="flex flex-wrap gap-2">
                {nearbyChips.slice(0, 3).map((chip, i) => (
                  <span key={i} className="text-xs bg-slate-50 text-slate-600 px-2 py-1 rounded-md border border-slate-200">
                    {chip}
                  </span>
                ))}
              </div>
            </div>
          )}
        </CardBody>
      </div>

      <CardFooter className="flex gap-3 justify-between items-center py-3 bg-slate-50/80 backdrop-blur-sm">
        <Button
          variant="primary"
          size="sm"
          className="flex-1 shadow-none"
          onClick={(e) => {
            e.stopPropagation();
            onSelect(project.project_id);
          }}
        >
          View Details
        </Button>
        {onToggleShortlist && (
          <Button
            variant={isShortlisted ? "secondary" : "ghost"}
            size="sm"
            className={classNames("shrink-0", { "!bg-sky-50 !text-sky-600 !border-sky-200": isShortlisted })}
            onClick={(e) => {
              e.stopPropagation();
              onToggleShortlist(project, Boolean(isShortlisted));
            }}
          >
            {isShortlisted ? (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" className="mr-1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                Saved
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mr-1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                Save
              </>
            )}
          </Button>
        )}
      </CardFooter>
    </Card>
  );
};

export default ProjectCard;
