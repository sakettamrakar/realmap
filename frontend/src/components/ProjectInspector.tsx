/**
 * Project Inspector - Admin view for debugging/validating projects.
 * Displays comprehensive project information for internal review.
 */
import { useState } from "react";
import { getProjectFullDebug, searchProjectByRera } from "../api/adminApi";
import type { ProjectFullDebug, FileArtifact, DbArtifact } from "../types/admin";
import "./ProjectInspector.css";

interface Props {
  onBack: () => void;
}

export default function ProjectInspector({ onBack }: Props) {
  const [projectIdInput, setProjectIdInput] = useState("");
  const [reraInput, setReraInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ProjectFullDebug | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    core: true,
    promoters: false,
    scores: true,
    geo: false,
    amenities: false,
    pricing: false,
    artifacts: false,
    rawData: false,
  });

  const toggleSection = (key: string) => {
    setExpandedSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const loadByProjectId = async () => {
    const id = parseInt(projectIdInput, 10);
    if (!id || isNaN(id)) {
      setError("Please enter a valid project ID.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await getProjectFullDebug(id);
      setData(result);
    } catch (err: any) {
      setError(err?.message || "Failed to load project.");
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const loadByRera = async () => {
    if (!reraInput.trim()) {
      setError("Please enter a RERA number.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const searchResult = await searchProjectByRera(reraInput.trim());
      const result = await getProjectFullDebug(searchResult.project_id);
      setData(result);
      setProjectIdInput(String(searchResult.project_id));
    } catch (err: any) {
      setError(err?.message || "Failed to find project.");
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (value: unknown): string => {
    if (value === null || value === undefined) return "—";
    if (typeof value === "number") return value.toFixed(2);
    if (typeof value === "boolean") return value ? "Yes" : "No";
    return String(value);
  };

  const renderScoreBadge = (score: number | null, label: string) => {
    if (score === null) return <span className="inspector-badge badge-na">{label}: —</span>;
    let colorClass = "badge-poor";
    if (score >= 70) colorClass = "badge-good";
    else if (score >= 50) colorClass = "badge-fair";
    return (
      <span className={`inspector-badge ${colorClass}`}>
        {label}: {score.toFixed(1)}
      </span>
    );
  };

  const renderFileArtifacts = (files: FileArtifact[], type: string) => {
    if (!files || files.length === 0) {
      return <p className="inspector-empty">No {type} files found.</p>;
    }
    return (
      <ul className="inspector-file-list">
        {files.map((f, i) => (
          <li key={`${type}-${i}`}>
            <code className="inspector-path">{f.path}</code>
            <span className="inspector-meta">
              Run: {f.run} • {(f.size_bytes / 1024).toFixed(1)} KB
            </span>
          </li>
        ))}
      </ul>
    );
  };

  const renderDbArtifacts = (artifacts: DbArtifact[]) => {
    if (!artifacts || artifacts.length === 0) {
      return <p className="inspector-empty">No database artifacts found.</p>;
    }
    return (
      <table className="inspector-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Category</th>
            <th>Type</th>
            <th>Path</th>
            <th>Format</th>
            <th>Preview</th>
          </tr>
        </thead>
        <tbody>
          {artifacts.map((a) => (
            <tr key={a.id}>
              <td>{a.id}</td>
              <td>{a.category || "—"}</td>
              <td>{a.artifact_type || "—"}</td>
              <td><code>{a.file_path || "—"}</code></td>
              <td>{a.file_format || "—"}</td>
              <td>{a.is_preview ? "Yes" : "No"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  return (
    <div className="project-inspector">
      <header className="inspector-header">
        <button className="inspector-back-btn" onClick={onBack}>
          ← Back to Explorer
        </button>
        <h1>Project Inspector</h1>
        <span className="inspector-warning">⚠️ Internal/Admin View</span>
      </header>

      <section className="inspector-search">
        <div className="inspector-search-group">
          <label>Project ID:</label>
          <input
            type="text"
            value={projectIdInput}
            onChange={(e) => setProjectIdInput(e.target.value)}
            placeholder="e.g. 123"
            onKeyDown={(e) => e.key === "Enter" && loadByProjectId()}
          />
          <button onClick={loadByProjectId} disabled={loading}>
            Load by ID
          </button>
        </div>
        <div className="inspector-search-divider">or</div>
        <div className="inspector-search-group">
          <label>RERA Number:</label>
          <input
            type="text"
            value={reraInput}
            onChange={(e) => setReraInput(e.target.value)}
            placeholder="e.g. PCGRERA240218000002"
            onKeyDown={(e) => e.key === "Enter" && loadByRera()}
          />
          <button onClick={loadByRera} disabled={loading}>
            Search by RERA
          </button>
        </div>
      </section>

      {loading && <div className="inspector-loading">Loading project data...</div>}
      {error && <div className="inspector-error">{error}</div>}

      {data && (
        <div className="inspector-content">
          {/* Core Info Section */}
          <section className="inspector-section">
            <h2 className="inspector-section-header" onClick={() => toggleSection("core")}>
              {expandedSections.core ? "▼" : "▶"} Core Project Info
            </h2>
            {expandedSections.core && (
              <div className="inspector-section-body">
                <dl className="inspector-dl">
                  <dt>ID</dt><dd>{data.core.id}</dd>
                  <dt>State Code</dt><dd>{data.core.state_code}</dd>
                  <dt>RERA Number</dt><dd><code>{data.core.rera_registration_number}</code></dd>
                  <dt>Name</dt><dd>{data.core.project_name}</dd>
                  <dt>Status</dt><dd>{formatValue(data.core.status)}</dd>
                  <dt>District</dt><dd>{formatValue(data.core.district)}</dd>
                  <dt>Tehsil</dt><dd>{formatValue(data.core.tehsil)}</dd>
                  <dt>Village/Locality</dt><dd>{formatValue(data.core.village_or_locality)}</dd>
                  <dt>Full Address</dt><dd>{formatValue(data.core.full_address)}</dd>
                  <dt>Normalized Address</dt><dd>{formatValue(data.core.normalized_address)}</dd>
                  <dt>Pincode</dt><dd>{formatValue(data.core.pincode)}</dd>
                  <dt>Approved Date</dt><dd>{formatValue(data.core.approved_date)}</dd>
                  <dt>Proposed End Date</dt><dd>{formatValue(data.core.proposed_end_date)}</dd>
                  <dt>Extended End Date</dt><dd>{formatValue(data.core.extended_end_date)}</dd>
                  <dt>Data Quality Score</dt><dd>{formatValue(data.core.data_quality_score)}</dd>
                  <dt>Scraped At</dt><dd>{formatValue(data.core.scraped_at)}</dd>
                  <dt>Last Parsed At</dt><dd>{formatValue(data.core.last_parsed_at)}</dd>
                </dl>
              </div>
            )}
          </section>

          {/* Promoters Section */}
          <section className="inspector-section">
            <h2 className="inspector-section-header" onClick={() => toggleSection("promoters")}>
              {expandedSections.promoters ? "▼" : "▶"} Promoters ({data.promoters.length})
            </h2>
            {expandedSections.promoters && (
              <div className="inspector-section-body">
                {data.promoters.length === 0 ? (
                  <p className="inspector-empty">No promoters recorded.</p>
                ) : (
                  data.promoters.map((p, i) => (
                    <div key={i} className="inspector-card">
                      <strong>{p.name || "Unknown"}</strong>
                      <dl className="inspector-dl-inline">
                        <dt>Type</dt><dd>{formatValue(p.type)}</dd>
                        <dt>Email</dt><dd>{formatValue(p.email)}</dd>
                        <dt>Phone</dt><dd>{formatValue(p.phone)}</dd>
                        <dt>Website</dt><dd>{formatValue(p.website)}</dd>
                        <dt>Address</dt><dd>{formatValue(p.address)}</dd>
                      </dl>
                    </div>
                  ))
                )}
              </div>
            )}
          </section>

          {/* Scores & Value Section */}
          <section className="inspector-section">
            <h2 className="inspector-section-header" onClick={() => toggleSection("scores")}>
              {expandedSections.scores ? "▼" : "▶"} Scores & Value
            </h2>
            {expandedSections.scores && (
              <div className="inspector-section-body">
                <div className="inspector-badges">
                  {renderScoreBadge(data.debug.scores_detail.overall_score, "Overall")}
                  {renderScoreBadge(data.debug.scores_detail.amenity_score, "Amenity")}
                  {renderScoreBadge(data.debug.scores_detail.location_score, "Location")}
                  {renderScoreBadge(data.debug.scores_detail.value_score, "Value")}
                </div>
                <dl className="inspector-dl">
                  <dt>Connectivity Score</dt><dd>{formatValue(data.debug.scores_detail.connectivity_score)}</dd>
                  <dt>Daily Needs Score</dt><dd>{formatValue(data.debug.scores_detail.daily_needs_score)}</dd>
                  <dt>Social Infra Score</dt><dd>{formatValue(data.debug.scores_detail.social_infra_score)}</dd>
                  <dt>Score Status</dt><dd>{formatValue(data.debug.scores_detail.score_status)}</dd>
                  <dt>Status Reason</dt><dd>{formatValue(data.debug.scores_detail.score_status_reason)}</dd>
                  <dt>Score Version</dt><dd>{formatValue(data.debug.scores_detail.score_version)}</dd>
                  <dt>Last Computed</dt><dd>{formatValue(data.debug.scores_detail.last_computed_at)}</dd>
                </dl>
              </div>
            )}
          </section>

          {/* Geo Section */}
          <section className="inspector-section">
            <h2 className="inspector-section-header" onClick={() => toggleSection("geo")}>
              {expandedSections.geo ? "▼" : "▶"} Geo/Location ({data.debug.geo_detail.candidate_locations.length} candidates)
            </h2>
            {expandedSections.geo && (
              <div className="inspector-section-body">
                <h4>Primary Location</h4>
                <dl className="inspector-dl">
                  <dt>Coordinates</dt>
                  <dd>
                    {data.debug.geo_detail.primary.lat !== null && data.debug.geo_detail.primary.lon !== null
                      ? `${data.debug.geo_detail.primary.lat.toFixed(6)}, ${data.debug.geo_detail.primary.lon.toFixed(6)}`
                      : "—"}
                  </dd>
                  <dt>Geocoding Status</dt><dd>{formatValue(data.debug.geo_detail.primary.geocoding_status)}</dd>
                  <dt>Geocoding Source</dt><dd>{formatValue(data.debug.geo_detail.primary.geocoding_source)}</dd>
                  <dt>Geo Source</dt><dd>{formatValue(data.debug.geo_detail.primary.geo_source)}</dd>
                  <dt>Precision</dt><dd>{formatValue(data.debug.geo_detail.primary.geo_precision)}</dd>
                  <dt>Confidence</dt><dd>{formatValue(data.debug.geo_detail.primary.geo_confidence)}</dd>
                  <dt>Normalized Address</dt><dd>{formatValue(data.debug.geo_detail.primary.geo_normalized_address)}</dd>
                  <dt>Formatted Address</dt><dd>{formatValue(data.debug.geo_detail.primary.geo_formatted_address)}</dd>
                </dl>

                <h4>Candidate Locations</h4>
                {data.debug.geo_detail.candidate_locations.length === 0 ? (
                  <p className="inspector-empty">No candidate locations.</p>
                ) : (
                  <table className="inspector-table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Source</th>
                        <th>Lat</th>
                        <th>Lon</th>
                        <th>Precision</th>
                        <th>Confidence</th>
                        <th>Active</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.debug.geo_detail.candidate_locations.map((loc) => (
                        <tr key={loc.id} className={loc.is_active ? "inspector-row-active" : ""}>
                          <td>{loc.id}</td>
                          <td>{loc.source_type}</td>
                          <td>{loc.lat.toFixed(6)}</td>
                          <td>{loc.lon.toFixed(6)}</td>
                          <td>{formatValue(loc.precision_level)}</td>
                          <td>{formatValue(loc.confidence_score)}</td>
                          <td>{loc.is_active ? "✓" : ""}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </section>

          {/* Amenities Section */}
          <section className="inspector-section">
            <h2 className="inspector-section-header" onClick={() => toggleSection("amenities")}>
              {expandedSections.amenities ? "▼" : "▶"} Amenities ({data.debug.amenities_detail.onsite.length} onsite, {data.debug.amenities_detail.nearby.length} nearby)
            </h2>
            {expandedSections.amenities && (
              <div className="inspector-section-body">
                <h4>On-site Amenities</h4>
                {data.debug.amenities_detail.onsite.length === 0 ? (
                  <p className="inspector-empty">No on-site amenities recorded.</p>
                ) : (
                  <table className="inspector-table">
                    <thead>
                      <tr>
                        <th>Type</th>
                        <th>Available</th>
                        <th>Details</th>
                        <th>Provider</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.debug.amenities_detail.onsite.map((a, i) => (
                        <tr key={i} className={a.onsite_available ? "inspector-row-active" : ""}>
                          <td>{a.amenity_type}</td>
                          <td>{a.onsite_available ? "✓" : "—"}</td>
                          <td>{formatValue(a.onsite_details)}</td>
                          <td>{formatValue(a.provider_snapshot)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                <h4>Nearby Amenities</h4>
                {data.debug.amenities_detail.nearby.length === 0 ? (
                  <p className="inspector-empty">No nearby amenities recorded.</p>
                ) : (
                  <table className="inspector-table">
                    <thead>
                      <tr>
                        <th>Type</th>
                        <th>Radius (km)</th>
                        <th>Count</th>
                        <th>Nearest (km)</th>
                        <th>Computed</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.debug.amenities_detail.nearby.map((a, i) => (
                        <tr key={i}>
                          <td>{a.amenity_type}</td>
                          <td>{formatValue(a.radius_km)}</td>
                          <td>{formatValue(a.nearby_count)}</td>
                          <td>{formatValue(a.nearby_nearest_km)}</td>
                          <td>{formatValue(a.last_computed_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </section>

          {/* Pricing Section */}
          <section className="inspector-section">
            <h2 className="inspector-section-header" onClick={() => toggleSection("pricing")}>
              {expandedSections.pricing ? "▼" : "▶"} Pricing ({data.debug.pricing_detail.snapshots.length} snapshots)
            </h2>
            {expandedSections.pricing && (
              <div className="inspector-section-body">
                {data.debug.pricing_detail.snapshots.length === 0 ? (
                  <p className="inspector-empty">No pricing snapshots recorded.</p>
                ) : (
                  <table className="inspector-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Unit Type</th>
                        <th>Min Total</th>
                        <th>Max Total</th>
                        <th>Min/sqft</th>
                        <th>Max/sqft</th>
                        <th>Source</th>
                        <th>Active</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.debug.pricing_detail.snapshots.map((s) => (
                        <tr key={s.id} className={s.is_active ? "inspector-row-active" : ""}>
                          <td>{s.snapshot_date}</td>
                          <td>{formatValue(s.unit_type_label)}</td>
                          <td>{s.min_price_total ? `₹${(s.min_price_total / 100000).toFixed(1)}L` : "—"}</td>
                          <td>{s.max_price_total ? `₹${(s.max_price_total / 100000).toFixed(1)}L` : "—"}</td>
                          <td>{s.min_price_per_sqft ? `₹${s.min_price_per_sqft.toFixed(0)}` : "—"}</td>
                          <td>{s.max_price_per_sqft ? `₹${s.max_price_per_sqft.toFixed(0)}` : "—"}</td>
                          <td>{formatValue(s.source_type)}</td>
                          <td>{s.is_active ? "✓" : ""}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </section>

          {/* Artifacts Section */}
          <section className="inspector-section">
            <h2 className="inspector-section-header" onClick={() => toggleSection("artifacts")}>
              {expandedSections.artifacts ? "▼" : "▶"} Raw Artifacts
            </h2>
            {expandedSections.artifacts && (
              <div className="inspector-section-body">
                <h4>Scraped JSON</h4>
                {renderFileArtifacts(data.debug.file_artifacts.scraped_json, "scraped JSON")}

                <h4>Raw HTML</h4>
                {renderFileArtifacts(data.debug.file_artifacts.raw_html, "raw HTML")}

                <h4>Raw Extracted</h4>
                {renderFileArtifacts(data.debug.file_artifacts.raw_extracted, "raw extracted")}

                <h4>Previews</h4>
                {renderFileArtifacts(data.debug.file_artifacts.previews, "preview")}

                <h4>Database Artifacts</h4>
                {renderDbArtifacts(data.debug.db_artifacts.db_artifacts)}
              </div>
            )}
          </section>

          {/* Raw Data JSON Section */}
          <section className="inspector-section">
            <h2 className="inspector-section-header" onClick={() => toggleSection("rawData")}>
              {expandedSections.rawData ? "▼" : "▶"} Raw Data JSON
            </h2>
            {expandedSections.rawData && (
              <div className="inspector-section-body">
                {data.raw_data_json ? (
                  <pre className="inspector-json">
                    {JSON.stringify(data.raw_data_json, null, 2)}
                  </pre>
                ) : (
                  <p className="inspector-empty">No raw data JSON stored.</p>
                )}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
