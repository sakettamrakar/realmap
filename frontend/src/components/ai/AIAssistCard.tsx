import { useEffect, useState } from "react";
import { getProjectScore } from "../../api/aiApi";
import type { AIScoreResponse } from "../../types/ai";

interface Props {
    projectId: number;
}

export const AIAssistCard = ({ projectId }: Props) => {
    const [scoreData, setScoreData] = useState<AIScoreResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [expanded, setExpanded] = useState(false);

    useEffect(() => {
        let mounted = true;

        async function fetchScore() {
            if (!projectId) return;

            setLoading(true);
            setError(null);

            try {
                const data = await getProjectScore(projectId);
                if (mounted) {
                    setScoreData(data);
                }
            } catch (err) {
                if (mounted) {
                    // Silent fail or show error?
                    // Showing discrete error state for "Assist" card
                    setError("AI Analysis unavailable at the moment.");
                }
            } finally {
                if (mounted) {
                    setLoading(false);
                }
            }
        }

        fetchScore();

        return () => {
            mounted = false;
        };
    }, [projectId]);

    if (loading) {
        return (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
                <div className="h-10 bg-gray-200 rounded w-full"></div>
            </div>
        );
    }

    if (error) {
        // Optional: don't render anything if unavailable, or render a disabled state
        return null;
    }

    if (!scoreData) return null;

    // Determine color based on score
    const getScoreColor = (score: number) => {
        if (score >= 80) return "text-green-600 bg-green-50 border-green-200";
        if (score >= 50) return "text-yellow-600 bg-yellow-50 border-yellow-200";
        return "text-red-600 bg-red-50 border-red-200";
    };

    const scoreColorClass = getScoreColor(scoreData.score_value);

    return (
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden mb-4">
            {/* Header */}
            <div className="bg-gradient-to-r from-indigo-50 to-white p-4 border-b border-indigo-100 flex justify-between items-center">
                <div className="flex items-center gap-2">
                    <span className="text-indigo-600">✨</span>
                    <h3 className="font-semibold text-gray-800">AI Assist</h3>
                </div>
                <div className={`px-3 py-1 rounded-full text-sm font-bold border ${scoreColorClass}`}>
                    {scoreData.score_value.toFixed(0)} / 100
                </div>
            </div>

            {/* Content */}
            <div className="p-4">
                <p className="text-gray-600 text-sm leading-relaxed mb-3">
                    {scoreData.explanation}
                </p>

                {/* Expandable Details */}
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="text-xs text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1"
                >
                    {expanded ? "Hide Details" : "View Details"}
                    <span>{expanded ? "▲" : "▼"}</span>
                </button>

                {expanded && (
                    <div className="mt-3 pt-3 border-t border-gray-100 text-xs">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <span className="block font-semibold text-green-700 mb-1">Strengths</span>
                                <ul className="list-disc pl-4 text-gray-600 space-y-1">
                                    {(scoreData.strengths || ["Location Analysis", "Amenity Coverage"]).map((s, i) => (
                                        <li key={i}>{s}</li>
                                    ))}
                                </ul>
                            </div>
                            <div>
                                <span className="block font-semibold text-red-700 mb-1">Risks</span>
                                <ul className="list-disc pl-4 text-gray-600 space-y-1">
                                    {(scoreData.risks || ["Delay Risk", "Market Volatility"]).map((r, i) => (
                                        <li key={i}>{r}</li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                        <div className="mt-3 text-gray-400 text-[10px] text-right">
                            Confidence: {(scoreData.confidence * 100).toFixed(0)}% • Model: {scoreData.model_name}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
