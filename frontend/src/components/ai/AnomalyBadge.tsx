import { useMemo } from "react";

interface AnomalyInfo {
    field: string;
    value: string | number;
    severity: "warning" | "error";
    message: string;
}

interface Props {
    pricePerSqft?: number | null;
    carpetArea?: number | null;
    unitType?: string;
    totalPrice?: number | null;
    className?: string;
}

/**
 * Feature 5: AI-based Price & Area Anomaly Detection
 * Flags unrealistic prices or dimensions during display
 */
export const AnomalyBadge = ({ pricePerSqft, carpetArea, unitType, totalPrice, className = "" }: Props) => {
    const anomalies = useMemo(() => {
        const detected: AnomalyInfo[] = [];

        // Price per sqft anomalies
        if (pricePerSqft !== null && pricePerSqft !== undefined) {
            if (pricePerSqft < 500) {
                detected.push({
                    field: "price_per_sqft",
                    value: pricePerSqft,
                    severity: "error",
                    message: `Unusually low price: ₹${pricePerSqft}/sqft`,
                });
            } else if (pricePerSqft > 50000) {
                detected.push({
                    field: "price_per_sqft",
                    value: pricePerSqft,
                    severity: "warning",
                    message: `Premium pricing: ₹${pricePerSqft.toLocaleString()}/sqft`,
                });
            }
        }

        // Carpet area anomalies based on unit type
        if (carpetArea !== null && carpetArea !== undefined && unitType) {
            const typeLower = unitType.toLowerCase();

            // 1BHK shouldn't be > 1500 sqft
            if (typeLower.includes("1bhk") && carpetArea > 1500) {
                detected.push({
                    field: "carpet_area",
                    value: carpetArea,
                    severity: "warning",
                    message: `Large 1BHK: ${carpetArea} sqft`,
                });
            }

            // Any flat < 200 sqft is suspicious
            if (carpetArea < 200 && typeLower.includes("bhk")) {
                detected.push({
                    field: "carpet_area",
                    value: carpetArea,
                    severity: "error",
                    message: `Unusually small: ${carpetArea} sqft`,
                });
            }

            // 2BHK > 3000 sqft is unusual
            if (typeLower.includes("2bhk") && carpetArea > 3000) {
                detected.push({
                    field: "carpet_area",
                    value: carpetArea,
                    severity: "warning",
                    message: `Large 2BHK: ${carpetArea} sqft`,
                });
            }
        }

        // Total price anomalies
        if (totalPrice !== null && totalPrice !== undefined) {
            if (totalPrice < 100000) {
                detected.push({
                    field: "total_price",
                    value: totalPrice,
                    severity: "error",
                    message: `Unusually low total: ₹${totalPrice.toLocaleString()}`,
                });
            }
        }

        return detected;
    }, [pricePerSqft, carpetArea, unitType, totalPrice]);

    if (anomalies.length === 0) return null;

    const hasError = anomalies.some(a => a.severity === "error");

    return (
        <div className={`inline-flex items-center gap-1 ${className}`}>
            <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium cursor-help ${hasError
                        ? "bg-red-100 text-red-700 border border-red-200"
                        : "bg-yellow-100 text-yellow-700 border border-yellow-200"
                    }`}
                title={anomalies.map(a => a.message).join("\n")}
            >
                {hasError ? (
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                ) : (
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                )}
                {anomalies.length > 1 ? `${anomalies.length} flags` : "Flagged"}
            </span>
        </div>
    );
};
