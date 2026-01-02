import type { ProjectDetail } from "../../types/projects";
import ScoreBadge from "../ScoreBadge";

interface Props {
    project: ProjectDetail;
    onShowMap: () => void;
    onShortlist: () => void;
    isShortlisted: boolean;
}

export function ProjectHero({ project, onShowMap, onShortlist, isShortlisted }: Props) {
    const { project: p, scores, pricing, location } = project;

    const priceText =
        pricing?.min_price_total && pricing?.max_price_total
            ? `₹${(pricing.min_price_total / 100000).toFixed(1)}L - ₹${(
                pricing.max_price_total / 100000
            ).toFixed(1)}L`
            : pricing?.min_price_total
                ? `₹${(pricing.min_price_total / 100000).toFixed(1)}L+`
                : "Price on Request";

    const locationText = [location?.tehsil, location?.district].filter(Boolean).join(", ");

    const valueBucket = scores?.value_bucket;
    let valueLabel = "";
    let valueClass = "";
    switch (valueBucket) {
        case "excellent":
            valueLabel = "High Value";
            valueClass = "value-excellent";
            break;
        case "good":
            valueLabel = "Good Value";
            valueClass = "value-good";
            break;
        case "fair":
            valueLabel = "Fair Value";
            valueClass = "value-fair";
            break;
        case "poor":
            valueLabel = "Low Value";
            valueClass = "value-poor";
            break;
        default:
            valueLabel = "";
    }

    return (
        <div className="project-hero">
            <div className="hero-content">
                <div>
                    <div className="hero-badges">
                        {p.status && <span className="status-pill">{p.status}</span>}
                        {valueLabel && <span className={`value-badge ${valueClass}`}>{valueLabel}</span>}
                    </div>
                    <h1 className="hero-title">{p.name}</h1>
                    <p className="hero-location">{locationText}</p>
                    <div className="hero-price">{priceText}</div>
                </div>

                <div className="hero-score">
                    <div className="score-label">Overall Score</div>
                    <ScoreBadge
                        score={scores?.overall_score}
                        status={scores?.score_status}
                        reason={scores?.score_status_reason}
                        amenityScore={scores?.amenity_score}
                        locationScore={scores?.location_score}
                        className="hero-score-badge"
                    />
                </div>
            </div>

            <div className="hero-actions">
                <button
                    className="action-btn primary"
                    onClick={() => window.open(`https://rera.cgstate.gov.in/view_project.jsp?id=${p.rera_number}`, '_blank')}
                >
                    Open RERA Page
                </button>
                <button
                    className="action-btn secondary"
                    onClick={onShowMap}
                    disabled={!location?.lat || !location?.lon}
                    title={(!location?.lat || !location?.lon) ? "Location coordinates missing" : ""}
                >
                    Show on Map
                </button>
                <button
                    className={`action-btn secondary ${isShortlisted ? 'active' : ''}`}
                    onClick={onShortlist}
                >
                    {isShortlisted ? 'Shortlisted' : 'Shortlist'}
                </button>
            </div>
        </div>
    );
}
