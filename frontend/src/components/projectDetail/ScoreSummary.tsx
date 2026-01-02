import { CheckCircle2, XCircle, BarChart3, Info, MapPin, Gauge } from "lucide-react";
import type { ProjectDetail } from "../../types/projects";

interface Props {
    scores: ProjectDetail["scores"];
    explanation?: ProjectDetail["score_explanation"];
}

/**
 * Parses and structures raw reason strings into visual components.
 * Patterns handled: 
 * - "7 school within 1 km"
 * - "Nearest is 0.6 km"
 */
function StructuredReason({ text }: { text: string }) {
    // Pattern 1: "X Category within Y km"
    const pattern1 = /^(\d+)\s+(.+?)\s+within\s+([\d.]+)\s*km$/i;
    // Pattern 2: "Nearest is X km"
    const pattern2 = /^Nearest\s+is\s+([\d.]+)\s*km$/i;

    let match;

    if ((match = text.match(pattern1))) {
        const [, count, category, distance] = match;
        return (
            <div className="flex items-center gap-2 py-0.5">
                <div className="flex items-center justify-center w-6 h-6 rounded bg-slate-100 text-[10px] font-bold text-slate-700">
                    {count}
                </div>
                <span className="text-sm font-medium text-slate-700 capitalize">
                    {category}
                </span>
                <span className="flex items-center gap-1 text-[10px] bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded border border-indigo-100 font-bold">
                    <MapPin size={8} />
                    {distance} km
                </span>
            </div>
        );
    }

    if ((match = text.match(pattern2))) {
        const [, distance] = match;
        return (
            <div className="flex items-center gap-2 py-0.5">
                <span className="text-xs text-slate-500 italic">Proximity:</span>
                <span className="flex items-center gap-1 text-xs font-bold text-indigo-700 bg-indigo-50/50 px-2 py-0.5 rounded-full border border-indigo-100/50">
                    <Gauge size={10} />
                    {distance} km to nearest
                </span>
            </div>
        );
    }

    return <span className="text-sm leading-relaxed">{text}</span>;
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
            <h3 className="section-title">
                <BarChart3 size={20} className="text-indigo-600" />
                Score Analysis
            </h3>

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
                <div className="flex items-start gap-2 p-3 mt-4 text-sm border bg-amber-50 border-amber-200 text-amber-800 rounded-xl">
                    <Info size={16} className="mt-0.5 flex-shrink-0" />
                    <div>
                        <strong>Note:</strong> Score status is {scores.score_status}.
                        {scores.score_status_reason && ` Reason: ${scores.score_status_reason}`}
                    </div>
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
                                        <h5 className="flex items-center gap-1.5 text-emerald-600 mb-3 px-1">
                                            <CheckCircle2 size={14} />
                                            Positives
                                        </h5>
                                        <ul className="flex flex-col gap-3">
                                            {positives.map((p, i) => (
                                                <li key={i} className="flex items-start gap-2.5 p-2 rounded-lg bg-emerald-50/30 border border-emerald-100/50">
                                                    <div className="mt-1 flex-shrink-0">
                                                        <CheckCircle2 size={14} className="text-emerald-500" />
                                                    </div>
                                                    <StructuredReason text={p} />
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                {negatives.length > 0 && (
                                    <div className="explanation-col negative">
                                        <h5 className="flex items-center gap-1.5 text-rose-600 mb-3 px-1">
                                            <XCircle size={14} />
                                            Negatives
                                        </h5>
                                        <ul className="flex flex-col gap-3">
                                            {negatives.map((n, i) => (
                                                <li key={i} className="flex items-start gap-2.5 p-2 rounded-lg bg-rose-50/30 border border-rose-100/50">
                                                    <div className="mt-1 flex-shrink-0">
                                                        <XCircle size={14} className="text-rose-500" />
                                                    </div>
                                                    <StructuredReason text={n} />
                                                </li>
                                            ))}
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
