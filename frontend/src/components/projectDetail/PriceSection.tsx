import { IndianRupee, LayoutList } from "lucide-react";
import type { ProjectDetail } from "../../types/projects";
import { AreaLabel, type AreaType } from "../shared/AreaLabel";
import "../shared/AreaLabel.css";

interface Props {
    pricing: ProjectDetail["pricing"];
    /** Area type for transparency (defaults to carpet for RERA compliance) */
    areaType?: AreaType;
}

export function PriceSection({ pricing, areaType = "carpet" }: Props) {
    if (!pricing) return null;

    const { min_price_total, max_price_total, unit_types } = pricing;

    const priceBand = min_price_total
        ? `₹${(min_price_total / 100000).toFixed(1)}L` +
        (max_price_total ? ` - ₹${(max_price_total / 100000).toFixed(1)}L` : "+")
        : "Price on Request";

    return (
        <div className="detail-section pricing-section">
            <h3 className="section-title">
                <IndianRupee size={20} className="text-indigo-600" />
                Pricing
            </h3>
            <div className="price-band-large flex items-center gap-2 text-2xl font-extrabold text-slate-900 mb-6 px-3 py-2 bg-indigo-50 rounded-xl border border-indigo-100">
                {priceBand}
            </div>

            {unit_types && unit_types.length > 0 ? (
                <>
                    <table className="unit-table">
                        <thead>
                            <tr>
                                <th>Unit Type</th>
                                <th>Area</th>
                                <th>Bedrooms</th>
                            </tr>
                        </thead>
                        <tbody>
                            {unit_types.map((u, i) => (
                                <tr key={i}>
                                    <td>{u.label}</td>
                                    <td>
                                        {u.area_range && (u.area_range[0] || u.area_range[1]) ? (
                                            <AreaLabel
                                                value={u.area_range[0] && u.area_range[1]
                                                    ? `${u.area_range[0]} - ${u.area_range[1]}`
                                                    : String(u.area_range[0] || u.area_range[1])}
                                                areaType={areaType}
                                                variant="inline"
                                            />
                                        ) : (
                                            "N/A"
                                        )}
                                    </td>
                                    <td>{u.bedrooms || "-"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    <div className="area-type-note">
                        <AreaLabel
                            value=""
                            areaType={areaType}
                            variant="badge"
                        />
                        <span className="note-text flex items-center gap-1.5 ml-auto text-xs text-slate-400">
                            <LayoutList size={14} className="text-indigo-400" />
                            All areas shown in {areaType === "carpet" ? "Carpet Area (RERA Standard)"
                                : areaType === "builtup" ? "Built-up Area"
                                    : "Super Built-up Area"}
                        </span>
                    </div>
                </>
            ) : (
                <p className="muted">Detailed unit pricing not available.</p>
            )}
        </div>
    );
}
