import type { ProjectDetail } from "../types/projects";

interface Props {
  project: ProjectDetail | null;
  loading?: boolean;
  onClose: () => void;
}

const formatScore = (score?: number) =>
  score === undefined || score === null ? "–" : score.toFixed(2);

const ProjectDetailPanel = ({ project, loading, onClose }: Props) => {
  const amenities = project?.amenities;
  const location = project?.location;
  const scores = project?.scores;

  const nearbySummaryEntries = amenities?.nearby_summary
    ? Object.entries(amenities.nearby_summary)
    : [];

  if (!project && !loading) return null;

  return (
    <aside className="detail-panel">
      <div className="detail-header">
        <div>
          <p className="eyebrow">Project detail</p>
          <h3>{project?.project.name || "Loading..."}</h3>
        </div>
        <button className="pill" onClick={onClose}>
          Close
        </button>
      </div>

      {loading && <p>Loading project details…</p>}

      {!loading && project && (
        <div className="detail-content">
          <section>
            <h4>Project summary</h4>
            <div className="definition">
              <span>RERA number</span>
              <strong>{project.project.rera_number || "—"}</strong>
            </div>
            <div className="definition">
              <span>Developer</span>
              <strong>{project.project.developer || "—"}</strong>
            </div>
            <div className="definition">
              <span>Type</span>
              <strong>{project.project.project_type || "—"}</strong>
            </div>
            <div className="definition">
              <span>Status</span>
              <strong>{project.project.status || "—"}</strong>
            </div>
            <div className="definition">
              <span>District / Tehsil</span>
              <strong>
                {(location?.district || "—") +
                  (location?.tehsil ? ` / ${location.tehsil}` : "")}
              </strong>
            </div>
          </section>

          <section>
            <h4>Scores</h4>
            <div className="score-grid">
              <div className="score-card">
                <p className="eyebrow">Overall</p>
                <p className="score-value">{formatScore(scores?.overall_score)}</p>
              </div>
              <div className="score-card">
                <p className="eyebrow">Location</p>
                <p className="score-value">{formatScore(scores?.location_score)}</p>
              </div>
              <div className="score-card">
                <p className="eyebrow">Amenities</p>
                <p className="score-value">{formatScore(scores?.amenity_score)}</p>
              </div>
            </div>
          </section>

          <section>
            <h4>On-site amenities</h4>
            {amenities?.onsite_list && amenities.onsite_list.length > 0 ? (
              <div className="tag-row">
                {amenities.onsite_list.map((amenity) => (
                  <span key={amenity} className="pill pill-muted">
                    {amenity}
                  </span>
                ))}
              </div>
            ) : (
              <p className="eyebrow">No amenity list available.</p>
            )}
            {amenities?.onsite_counts && (
              <p className="eyebrow">
                Total: {amenities.onsite_counts.total ?? "—"} | Primary:{" "}
                {amenities.onsite_counts.primary ?? "—"} | Secondary:{" "}
                {amenities.onsite_counts.secondary ?? "—"}
              </p>
            )}
          </section>

          <section>
            <h4>Location context</h4>
            {nearbySummaryEntries.length > 0 ? (
              <div className="definition-grid">
                {nearbySummaryEntries.map(([category, summary]) => (
                  <div key={category} className="definition">
                    <span className="eyebrow">{category}</span>
                    <strong>
                      {summary.count ?? "—"} nearby
                      {summary.avg_distance_km
                        ? ` · avg ${summary.avg_distance_km.toFixed(1)} km`
                        : ""}
                    </strong>
                  </div>
                ))}
              </div>
            ) : (
              <p className="eyebrow">
                No nearby POI summary yet. Run the location pipeline to populate.
              </p>
            )}
            {amenities?.top_nearby && (
              <div className="top-nearby">
                {Object.entries(amenities.top_nearby).map(([category, items]) => (
                  <div key={category}>
                    <p className="eyebrow">{category}</p>
                    <ul>
                      {items.map((item, idx) => (
                        <li key={`${category}-${idx}`}>
                          {item.name || "Unknown"}{" "}
                          {item.distance_km
                            ? `(${item.distance_km.toFixed(1)} km)`
                            : ""}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </aside>
  );
};

export default ProjectDetailPanel;
