import type { ProjectDetail } from "../types/projects";

interface Props {
  open: boolean;
  projects: ProjectDetail[];
  loading?: boolean;
  onClose: () => void;
  selectionCount: number;
}

const formatScore = (score?: number | null) =>
  score === undefined || score === null ? "—" : score.toFixed(2);

const formatLocation = (project: ProjectDetail) => {
  const district = project.location?.district || "—";
  const tehsil = project.location?.tehsil || "";
  return tehsil ? `${district} / ${tehsil}` : district;
};

const formatOnsite = (project: ProjectDetail) => {
  const progressEntries = project.amenities?.onsite_progress
    ? Object.entries(project.amenities.onsite_progress)
    : [];
  if (progressEntries.length > 0) {
    return progressEntries
      .slice(0, 4)
      .map(([name, progress]) => `${name}: ${Math.round(progress * 100)}%`)
      .join(" • ");
  }
  if (project.amenities?.onsite_list?.length) {
    return project.amenities.onsite_list.slice(0, 4).join(" • ");
  }
  return "—";
};

const formatLocationContext = (project: ProjectDetail) => {
  const summary = project.amenities?.nearby_summary;
  if (!summary) return "—";
  const parts: string[] = [];
  if (summary.schools?.count != null) {
    parts.push(`Schools: ${summary.schools.count}`);
  }
  if (summary.hospitals?.count != null) {
    parts.push(`Hospitals: ${summary.hospitals.count}`);
  }
  if (summary.grocery?.count != null) {
    parts.push(`Grocery: ${summary.grocery.count}`);
  }
  return parts.join(" • ") || "—";
};

const CompareModal = ({ open, projects, loading, onClose, selectionCount }: Props) => {
  return (
    <div className={`compare-modal ${open ? "open" : ""}`} aria-hidden={!open}>
      <div className="compare-card">
        <div className="compare-header">
          <div>
            <p className="eyebrow">Compare</p>
            <h3>Side-by-side view ({selectionCount} selected)</h3>
          </div>
          <button className="pill pill-muted" onClick={onClose} type="button">
            Close
          </button>
        </div>

        {loading && <p>Loading selected projects…</p>}
        {!loading && projects.length === 0 && (
          <p className="muted">Select at least two projects to start comparing.</p>
        )}

        {!loading && projects.length > 0 && (
          <div className="compare-table" role="table">
            <div className="compare-row compare-row-heading" role="row">
              <div className="compare-cell heading" role="columnheader"></div>
              {projects.map((project) => (
                <div key={project.project.project_id} className="compare-cell heading" role="columnheader">
                  <strong>{project.project.name}</strong>
                  <p className="eyebrow">{project.project.status || "Status unknown"}</p>
                </div>
              ))}
            </div>

            <div className="compare-row" role="row">
              <div className="compare-cell section-label" role="rowheader">
                Summary
              </div>
              {projects.map((project) => (
                <div key={`${project.project.project_id}-summary`} className="compare-cell" role="cell">
                  <p className="eyebrow">District / Tehsil</p>
                  <p>{formatLocation(project)}</p>
                  <p className="eyebrow">RERA</p>
                  <p>{project.project.rera_number || "—"}</p>
                </div>
              ))}
            </div>

            <div className="compare-row" role="row">
              <div className="compare-cell section-label" role="rowheader">
                Scores
              </div>
              {projects.map((project) => (
                <div key={`${project.project.project_id}-scores`} className="compare-cell" role="cell">
                  <p className="eyebrow">Overall</p>
                  <p className="value">{formatScore(project.scores?.overall_score)}</p>
                  <p className="eyebrow">Amenity / Location</p>
                  <p>
                    {formatScore(project.scores?.amenity_score)} / {formatScore(project.scores?.location_score)}
                  </p>
                </div>
              ))}
            </div>

            <div className="compare-row" role="row">
              <div className="compare-cell section-label" role="rowheader">
                On-site amenities
              </div>
              {projects.map((project) => (
                <div key={`${project.project.project_id}-amenities`} className="compare-cell" role="cell">
                  <p>{formatOnsite(project)}</p>
                  {project.amenities?.onsite_counts && (
                    <p className="eyebrow">
                      Total: {project.amenities.onsite_counts.total ?? "—"} | Primary:
                      {" "}
                      {project.amenities.onsite_counts.primary ?? "—"}
                    </p>
                  )}
                </div>
              ))}
            </div>

            <div className="compare-row" role="row">
              <div className="compare-cell section-label" role="rowheader">
                Location context
              </div>
              {projects.map((project) => (
                <div key={`${project.project.project_id}-location`} className="compare-cell" role="cell">
                  <p>{formatLocationContext(project)}</p>
                  <p className="eyebrow">Based on nearby data</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CompareModal;
