import type { ProjectDetail } from "../../types/projects";

interface Props {
    amenities: ProjectDetail["amenities"];
}

const CATEGORIES: Record<string, string[]> = {
    "Leisure": ["Club House", "Park", "Garden", "Community Hall", "Party Area"],
    "Sports": ["Gym", "Swimming Pool", "Jogging Track", "Sports Court", "Play Area"],
    "Safety": ["CCTV", "Security", "Fire Safety", "Gated Community"],
    "Essentials": ["Power Backup", "Water Supply", "Lift", "Parking", "Sewage Treatment"],
};

export function AmenitiesSection({ amenities }: Props) {
    if (!amenities?.onsite_list || amenities.onsite_list.length === 0) {
        return (
            <div className="detail-section">
                <h3 className="section-title">Amenities</h3>
                <p className="muted">No amenity information available.</p>
            </div>
        );
    }

    const progress = amenities.onsite_progress || {};

    // Group amenities
    const grouped: Record<string, string[]> = {};
    const uncategorized: string[] = [];

    amenities.onsite_list.forEach(a => {
        let found = false;
        for (const [cat, keywords] of Object.entries(CATEGORIES)) {
            if (keywords.some(k => a.toLowerCase().includes(k.toLowerCase()))) {
                if (!grouped[cat]) grouped[cat] = [];
                grouped[cat].push(a);
                found = true;
                break;
            }
        }
        if (!found) uncategorized.push(a);
    });

    if (uncategorized.length > 0) {
        grouped["Other"] = uncategorized;
    }

    return (
        <div className="detail-section">
            <h3 className="section-title">Amenities</h3>
            <div className="amenities-grid">
                {Object.entries(grouped).map(([category, items]) => (
                    <div key={category} className="amenity-category">
                        <h4 className="category-title">{category}</h4>
                        <ul className="amenity-list">
                            {items.map(item => (
                                <li key={item} className="amenity-item">
                                    <span className="check-icon">✓</span>
                                    <span className="amenity-name">{item}</span>
                                    {progress[item] !== undefined && (
                                        <span className="amenity-progress">
                                            {progress[item] === 100 ? "Ready" : `${progress[item]}%`}
                                        </span>
                                    )}
                                </li>
                            ))}
                        </ul>
                    </div>
                ))}
            </div>
        </div>
    );
}
