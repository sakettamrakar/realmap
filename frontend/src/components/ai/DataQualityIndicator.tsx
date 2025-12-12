import { useMemo } from "react";

interface FieldStatus {
    field: string;
    label: string;
    hasValue: boolean;
    isImputed?: boolean;
}

interface Props {
    project: {
        project_name?: string | null;
        district?: string | null;
        status?: string | null;
        rera_registration_number?: string | null;
        latitude?: number | null;
        longitude?: number | null;
        promoter_name?: string | null;
        carpet_area_min?: number | null;
        price_min?: number | null;
        amenities?: string[] | null;
        completion_date?: string | null;
    };
    compact?: boolean;
    className?: string;
}

/**
 * Feature 4: AI-powered Missing Data Imputation Indicator
 * Shows data completeness and highlights imputed/missing fields
 */
export const DataQualityIndicator = ({ project, compact = false, className = "" }: Props) => {
    const { score, fields } = useMemo(() => {
        const checkFields: FieldStatus[] = [
            { field: "project_name", label: "Name", hasValue: !!project.project_name },
            { field: "district", label: "District", hasValue: !!project.district },
            { field: "status", label: "Status", hasValue: !!project.status },
            { field: "rera_registration_number", label: "RERA No.", hasValue: !!project.rera_registration_number },
            { field: "location", label: "Location", hasValue: !!(project.latitude && project.longitude) },
            { field: "promoter_name", label: "Promoter", hasValue: !!project.promoter_name },
            { field: "carpet_area", label: "Area", hasValue: project.carpet_area_min !== null && project.carpet_area_min !== undefined },
            { field: "price", label: "Price", hasValue: project.price_min !== null && project.price_min !== undefined },
            { field: "amenities", label: "Amenities", hasValue: !!(project.amenities && project.amenities.length > 0) },
            { field: "completion_date", label: "Completion", hasValue: !!project.completion_date },
        ];

        const filledCount = checkFields.filter(f => f.hasValue).length;
        const completenessScore = Math.round((filledCount / checkFields.length) * 100);

        return { score: completenessScore, fields: checkFields };
    }, [project]);

    const getScoreColor = (s: number) => {
        if (s >= 80) return { bg: "bg-green-100", text: "text-green-700", bar: "bg-green-500" };
        if (s >= 50) return { bg: "bg-yellow-100", text: "text-yellow-700", bar: "bg-yellow-500" };
        return { bg: "bg-red-100", text: "text-red-700", bar: "bg-red-500" };
    };

    const colors = getScoreColor(score);
    const missingFields = fields.filter(f => !f.hasValue);

    if (compact) {
        return (
            <div
                className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full ${colors.bg} ${className}`}
                title={`Data completeness: ${score}%\nMissing: ${missingFields.map(f => f.label).join(", ") || "None"}`}
            >
                <div className="w-10 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div className={`h-full ${colors.bar} transition-all`} style={{ width: `${score}%` }} />
                </div>
                <span className={`text-xs font-medium ${colors.text}`}>{score}%</span>
            </div>
        );
    }

    return (
        <div className={`bg-white border border-gray-200 rounded-lg p-3 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-sm font-medium text-gray-700">Data Quality</span>
                </div>
                <span className={`text-sm font-bold ${colors.text}`}>{score}%</span>
            </div>

            {/* Progress Bar */}
            <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden mb-3">
                <div
                    className={`h-full ${colors.bar} transition-all duration-500`}
                    style={{ width: `${score}%` }}
                />
            </div>

            {/* Field Summary */}
            <div className="grid grid-cols-5 gap-1">
                {fields.map((field) => (
                    <div
                        key={field.field}
                        className={`px-1.5 py-0.5 rounded text-[10px] text-center truncate ${field.hasValue
                                ? "bg-green-50 text-green-700"
                                : "bg-gray-100 text-gray-400"
                            }`}
                        title={`${field.label}: ${field.hasValue ? "Available" : "Missing"}`}
                    >
                        {field.label}
                    </div>
                ))}
            </div>

            {/* Missing Fields Notice */}
            {missingFields.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-100">
                    <p className="text-[10px] text-gray-400">
                        <span className="font-medium text-gray-500">Missing:</span>{" "}
                        {missingFields.map(f => f.label).join(", ")}
                    </p>
                </div>
            )}
        </div>
    );
};
