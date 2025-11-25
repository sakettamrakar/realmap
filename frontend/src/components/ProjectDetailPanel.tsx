import type { ProjectDetail } from "../types/projects";

interface Props {
  project: ProjectDetail | null;
  loading?: boolean;
  onClose: () => void;
  onCenterOnProject?: (coords: { lat: number; lon: number }) => void;
}

const formatScore = (score?: number) =>
  score === undefined || score === null ? "–" : score.toFixed(2);

const scoreBucket = (score?: number) => {
  if (score === undefined || score === null) return "unknown";
  if (score >= 0.75) return "high";
  if (score >= 0.5) return "medium";
  return "low";
};

const getScoreBarWidth = (score?: number) =>
  `${Math.min(Math.max((score ?? 0) * 100, 0), 100)}%`;

const progressStatus = (progress?: number) => {
  if (progress === undefined || progress === null) return "Not reported";
  if (progress < 0.3) return "Early";
  if (progress < 0.7) return "In progress";
  return "Mostly complete";
};

const ProjectDetailPanel = ({ project, loading, onClose, onCenterOnProject }: Props) => {
  const amenities = project?.amenities;
  const location = project?.location;
  const scores = project?.scores;

  const nearbySummaryEntries = amenities?.nearby_summary
    ? Object.entries(amenities.nearby_summary)
    : [];

  const onsiteAmenities = (() => {
    if (amenities?.onsite_progress) {
      return Object.entries(amenities.onsite_progress).map(([name, progress]) => ({
        name,
        progress,
      }));
    }
    if (amenities?.onsite_list) {
      return amenities.onsite_list.map((name) => ({ name, progress: undefined }));
    }
    return [];
  })();

  const centerEnabled = Boolean(location?.lat && location?.lon && onCenterOnProject);

  const topNearby = amenities?.top_nearby || {};

  const nearestDistanceFor = (category: string) => {
    const items = topNearby[category];
    if (!items?.length) return undefined;
    const distances = items
      .map((item) => item.distance_km)
      .filter((value): value is number => typeof value === "number");
    if (distances.length === 0) return undefined;
    return Math.min(...distances);
  };

  const locationHighlights = [
    {
      key: "schools",
      label: "Schools within 3 km",
      count: amenities?.nearby_summary?.schools?.count,
      nearest: nearestDistanceFor("schools"),
    },
    {
      key: "hospitals",
      label: "Hospitals within 5 km",
      count: amenities?.nearby_summary?.hospitals?.count,
      nearest: nearestDistanceFor("hospitals"),
    },
    {
      key: "grocery",
      label: "Grocery / daily needs within 2 km",
      count: amenities?.nearby_summary?.grocery?.count,
      nearest: nearestDistanceFor("grocery"),
    },
  ];

  if (!project && !loading) return null;

  return (
    <aside className="detail-panel">
      <div className="detail-header">
        <div>
          <p className="eyebrow">Project detail</p>
          <h3>{project?.project.name || "Loading..."}</h3>
        </div>
        <div className="detail-header-actions">
          <button
            className="pill"
            disabled={!centerEnabled}
            aria-label={centerEnabled ? "Center map on this project" : "Center map on this project (location unavailable)"}
            onClick={() =>
              centerEnabled &&
              onCenterOnProject?.({ lat: location!.lat as number, lon: location!.lon as number })
            }
          >
            Center map on this project
          </button>
          <button className="pill pill-muted" onClick={onClose}>
            Close
          </button>
        </div>
      </div>

      <div className="detail-body">
        {loading && <p>Loading project details…</p>}

        {!loading && project && (
          <div className="detail-content">
            <section className="detail-section">
              <div className="section-header">
                <h4>Project Summary</h4>
                <p className="eyebrow">Core RERA details</p>
              </div>
              <div className="definition-grid">
                <div className="definition">
                  <span>RERA Registration Number</span>
                  <strong>{project.project.rera_number || "—"}</strong>
                </div>
                <div className="definition">
                  <span>Developer</span>
                  <strong>{project.project.developer || "—"}</strong>
                </div>
                <div className="definition">
                  <span>District / Tehsil</span>
                  <strong>
                    {(location?.district || "—") + (location?.tehsil ? ` / ${location.tehsil}` : "")}
                  </strong>
                </div>
                <div className="definition">
                  <span>Status</span>
                  <strong>{project.project.status || "—"}</strong>
                </div>
                <div className="definition">
                  <span>Project Type</span>
                  <strong>{project.project.project_type || "—"}</strong>
                </div>
                <div className="definition">
                  <span>RERA Registration Date</span>
                  <strong>{project.project.registration_date || "—"}</strong>
                </div>
                <div className="definition">
                  <span>Proposed Completion</span>
                  <strong>{project.project.expected_completion || "—"}</strong>
                </div>
              </div>
            </section>

            <section className="detail-section">
              <div className="section-header">
                <h4>Scores</h4>
                <p className="eyebrow">Quality signals for the project and its surroundings</p>
              </div>
              <div className="score-grid">
                <div className={`score-card score-${scoreBucket(scores?.overall_score)}`}>
                  <p className="eyebrow">Overall Score</p>
                  <p className="score-value">{formatScore(scores?.overall_score)}</p>
                  <div className="score-bar">
                    <div
                      className="score-bar-fill"
                      style={{ width: getScoreBarWidth(scores?.overall_score) }}
                    />
                  </div>
                  <p className="score-hint">High-level blend of amenity and location quality</p>
                </div>
                <div className={`score-card score-${scoreBucket(scores?.amenity_score)}`}>
                  <p className="eyebrow">Amenity Score</p>
                  <p className="score-value">{formatScore(scores?.amenity_score)}</p>
                  <div className="score-bar">
                    <div
                      className="score-bar-fill"
                      style={{ width: getScoreBarWidth(scores?.amenity_score) }}
                    />
                  </div>
                  <p className="score-hint">Internal project infra (clubhouse, water, roads…)</p>
                </div>
                <div className={`score-card score-${scoreBucket(scores?.location_score)}`}>
                  <p className="eyebrow">Location Score</p>
                  <p className="score-value">{formatScore(scores?.location_score)}</p>
                  <div className="score-bar">
                    <div
                      className="score-bar-fill"
                      style={{ width: getScoreBarWidth(scores?.location_score) }}
                    />
                  </div>
                  <p className="score-hint">Nearby schools, hospitals, daily needs</p>
                </div>
              </div>
            </section>

            <section className="detail-section">
              <div className="section-header">
                <h4>On-site Amenities</h4>
                <p className="eyebrow">Based on RERA / builder disclosures</p>
              </div>
              {onsiteAmenities.length > 0 ? (
                <div className="amenity-table">
                  <div className="amenity-row amenity-row-header">
                    <span>Amenity</span>
                    <span>Progress</span>
                    <span>Status</span>
                    <span>RERA Preview</span>
                  </div>
                  {onsiteAmenities.map((amenity) => {
                    const statusText = progressStatus(amenity.progress);
                    const images = amenities?.onsite_images?.[amenity.name] || [];
                    const nearestImage = images[0];

                    return (
                      <div key={amenity.name} className="amenity-row">
                        <span className="amenity-name">{amenity.name}</span>
                        <span className="amenity-progress">
                          {amenity.progress != null ? `${Math.round(amenity.progress * 100)}%` : "—"}
                        </span>
                        <span>
                          <span className={`status-tag status-${statusText.replace(/\s+/g, "-").toLowerCase()}`}>
                            {statusText}
                          </span>
                        </span>
                        <span>
                          {nearestImage ? (
                            <a
                              href={nearestImage}
                              target="_blank"
                              rel="noreferrer"
                              className="eyebrow"
                              aria-label={`Preview ${amenity.name}`}
                            >
                              Preview
                            </a>
                          ) : (
                            <span className="eyebrow">—</span>
                          )}
                        </span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="eyebrow">No amenity list available.</p>
              )}
              {amenities?.onsite_counts && (
                <p className="eyebrow amenity-counts">
                  Total: {amenities.onsite_counts.total ?? "—"} | Primary: {amenities.onsite_counts.primary ?? "—"} |
                  Secondary: {amenities.onsite_counts.secondary ?? "—"}
                </p>
              )}
            </section>

            <section className="detail-section">
              <div className="section-header">
                <h4>Location Context</h4>
                <p className="eyebrow">Counts and distances are indicative and may be approximate.</p>
              </div>
              <div className="location-grid">
                {locationHighlights.map((item) => (
                  <div key={item.key} className="location-card">
                    <p className="eyebrow">{item.label}</p>
                    <strong className="location-count">{item.count ?? "—"}</strong>
                    <p className="eyebrow">Nearest: {item.nearest ? `${item.nearest.toFixed(1)} km` : "—"}</p>
                  </div>
                ))}
              </div>

              {nearbySummaryEntries.length > 0 ? (
                <div className="definition-grid compact-grid">
                  {nearbySummaryEntries.map(([category, summary]) => (
                    <div key={category} className="definition">
                      <span className="eyebrow">{category}</span>
                      <strong>
                        {summary.count ?? "—"} nearby
                        {summary.avg_distance_km ? ` · avg ${summary.avg_distance_km.toFixed(1)} km` : ""}
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
                      <p className="eyebrow">Closest {category}</p>
                      <ul>
                        {items.map((item, idx) => (
                          <li key={`${category}-${idx}`}>
                            {item.name || "Unknown"}{" "}
                            {item.distance_km ? `(${item.distance_km.toFixed(1)} km)` : ""}
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
      </div>
    </aside>
  );
};

export default ProjectDetailPanel;
