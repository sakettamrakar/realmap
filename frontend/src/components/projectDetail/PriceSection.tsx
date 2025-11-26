import type { ProjectDetail } from "../../types/projects";

interface Props {
    pricing: ProjectDetail["pricing"];
}

export function PriceSection({ pricing }: Props) {
    if (!pricing) return null;

    const { min_price_total, max_price_total, unit_types } = pricing;

    const priceBand = min_price_total
        ? `₹${(min_price_total / 100000).toFixed(1)}L` +
        (max_price_total ? ` - ₹${(max_price_total / 100000).toFixed(1)}L` : "+")
        : "Price on Request";

    return (
        <div className="detail-section">
            <h3 className="section-title">Pricing</h3>
            <div className="price-band-large">{priceBand}</div>

            {unit_types && unit_types.length > 0 ? (
                <table className="unit-table">
                    <thead>
                        <tr>
                            <th>Unit Type</th>
                            <th>Area (Sq.ft)</th>
                            <th>Bedrooms</th>
                        </tr>
                    </thead>
                    <tbody>
                        {unit_types.map((u, i) => (
                            <tr key={i}>
                                <td>{u.label}</td>
                                <td>
                                    {u.area_range
                                        ? `${u.area_range[0] || "?"} - ${u.area_range[1] || "?"}`
                                        : "N/A"}
                                </td>
                                <td>{u.bedrooms || "-"}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            ) : (
                <p className="muted">Detailed unit pricing not available.</p>
            )}
        </div>
    );
}
