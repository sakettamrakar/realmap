import type { ProjectDetail } from "../../types/projects";

interface Props {
    scores: ProjectDetail["scores"];
    explanation?: ProjectDetail["score_explanation"];
}

export function ScoreSummary({ scores, explanation }: Props) {
    if (!scores) return null;

    const scoreItems = [
        { label: "Overall", score: scores.overall_score },
        { label: "Location", score: scores.location_score },
        { label: "Amenities", score: scores.amenity_score },
        { label: "Value", score: scores.value_score },
    ];

    return (
        <div className="detail-section score-summary-section">
            <h3 className="section-title">Score Analysis</h3>

            <div className="score-grid-large">
                {scoreItems.map((item) => (
                    <div key={item.label} className="score-card-large">
                        <span className="score-label">{item.label}</span>
                        <div className="score-value-row">
                            <span className="score-number">{item.score?.toFixed(0) ?? "N/A"}</span>
                            <div className="score-bar-bg">
                                <div
                                    className="score-bar-fill"
                                    style={{ width: `${item.score || 0}%` }}
                                />
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {scores.score_status !== 'ok' && (
                <div className="score-status-warning">
                    <strong>Note:</strong> Score status is {scores.score_status}.
                    {scores.score_status_reason && ` Reason: ${scores.score_status_reason}`}
                </div>
            )}

            {(explanation || (!explanation && scores)) && (
                <div className="score-explanation">
                    <h4>Why this score?</h4>
                    {explanation?.summary && <p>{explanation.summary}</p>}

                    {(() => {
                        const positives = explanation?.positives || [];
                        const negatives = explanation?.negatives || [];

                        if (!explanation) {
                            if ((scores.location_score || 0) >= 70) positives.push("Strong location score");
                            else if ((scores.location_score || 0) < 40 && (scores.location_score || 0) > 0) negatives.push("Below average location score");

                            if ((scores.amenity_score || 0) >= 70) positives.push("Excellent amenities");
                            else if ((scores.amenity_score || 0) < 40 && (scores.amenity_score || 0) > 0) negatives.push("Limited amenities");

                            if (scores.value_bucket === 'excellent') positives.push("Excellent value for money");
                            if (scores.value_bucket === 'good') positives.push("Good value for money");
                            if (scores.value_bucket === 'poor') negatives.push("Poor value proposition");
                        }

                        if (positives.length === 0 && negatives.length === 0) return null;

                        return (
                            <div className="explanation-lists">
                                {positives.length > 0 && (
                                    <div className="explanation-col positive">
                                        <h5>Positives</h5>
                                        <ul>
                                            {positives.map((p, i) => <li key={i}>{p}</li>)}
                                        </ul>
                                    </div>
                                )}
                                {negatives.length > 0 && (
                                    <div className="explanation-col negative">
                                        <h5>Negatives</h5>
                                        <ul>
                                            {negatives.map((n, i) => <li key={i}>{n}</li>)}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        );
                    })()}
                </div>
            )}
        </div>
    );
}
