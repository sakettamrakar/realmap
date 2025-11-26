import { useRef, useEffect } from "react";
import type { ProjectDetail } from "../types/projects";
import { ProjectHero } from "./projectDetail/ProjectHero";
import { ProjectSnapshot } from "./projectDetail/ProjectSnapshot";
import { ScoreSummary } from "./projectDetail/ScoreSummary";
import { AmenitiesSection } from "./projectDetail/AmenitiesSection";
import { LocationSection } from "./projectDetail/LocationSection";
import { PriceSection } from "./projectDetail/PriceSection";

interface Props {
  project: ProjectDetail | null;
  loading?: boolean;
  onClose: () => void;
  onCenterOnProject?: (coords: { lat: number; lon: number }) => void;
  isShortlisted?: boolean;
  onShortlist?: () => void;
}

const ProjectDetailPanel = ({
  project,
  loading,
  onClose,
  onCenterOnProject,
  isShortlisted = false,
  onShortlist = () => { }
}: Props) => {
  const panelRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (project && panelRef.current) {
      panelRef.current.scrollTop = 0;
    }
  }, [project]);

  if (!project && !loading) return null;

  return (
    <aside className={`detail-panel ${project ? 'open' : ''}`} ref={panelRef}>
      <div className="detail-header-sticky">
        <button className="close-btn" onClick={onClose}>
          ← Back
        </button>
        {project && (
          <div className="sticky-title">
            <span className="name">{project.project.name}</span>
            {project.scores?.overall_score && (
              <span className="score">Score: {project.scores.overall_score.toFixed(0)}</span>
            )}
          </div>
        )}
      </div>

      <div className="detail-body">
        {loading && <div className="loading-state">Loading project details...</div>}

        {!loading && project && (
          <div className="detail-content">
            <ProjectHero
              project={project}
              onShowMap={() => {
                if (project.location?.lat && project.location?.lon) {
                  onCenterOnProject?.({ lat: project.location.lat, lon: project.location.lon });
                }
              }}
              onShortlist={onShortlist}
              isShortlisted={isShortlisted}
            />

            <ProjectSnapshot project={project} />

            <ScoreSummary
              scores={project.scores}
              explanation={project.score_explanation}
            />

            <div className="detail-grid-row">
              <div className="detail-col-main">
                <AmenitiesSection amenities={project.amenities} />
                <LocationSection location={project.location} amenities={project.amenities} />
              </div>
              <div className="detail-col-side">
                <PriceSection pricing={project.pricing} />
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};

export default ProjectDetailPanel;
