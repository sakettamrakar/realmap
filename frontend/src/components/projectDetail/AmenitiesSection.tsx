import { Dumbbell, LayoutGrid, Palmtree, ShieldCheck, Zap } from "lucide-react";
import type { ProjectDetail } from "../../types/projects";

interface Props {
    amenities: ProjectDetail["amenities"];
}

const CATEGORIES: Record<string, { icons: any, keywords: string[] }> = {
    "Leisure": {
        icons: Palmtree,
        keywords: ["Club House", "Park", "Garden", "Community Hall", "Party Area"]
    },
    "Sports": {
        icons: Dumbbell,
        keywords: ["Gym", "Swimming Pool", "Jogging Track", "Sports Court", "Play Area"]
    },
    "Safety": {
        icons: ShieldCheck,
        keywords: ["CCTV", "Security", "Fire Safety", "Gated Community"]
    },
    "Essentials": {
        icons: Zap,
        keywords: ["Power Backup", "Water Supply", "Lift", "Parking", "Sewage Treatment"]
    },
};

export function AmenitiesSection({ amenities }: Props) {
    if (!amenities?.onsite_list || amenities.onsite_list.length === 0) {
        return (
            <div className="detail-section">
                <h3 className="section-title">
                    <LayoutGrid size={20} className="text-indigo-600" />
                    Amenities
                </h3>
                <p className="py-4 text-center text-sm text-slate-400 italic">No amenity information available.</p>
            </div>
        );
    }

    const progress = amenities.onsite_progress || {};

    // Group amenities
    const grouped: Record<string, string[]> = {};
    const uncategorized: string[] = [];

    amenities.onsite_list.forEach(a => {
        let found = false;
        for (const [cat, data] of Object.entries(CATEGORIES)) {
            if (data.keywords.some(k => a.toLowerCase().includes(k.toLowerCase()))) {
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
        <div className="detail-section amenities-section">
            <h3 className="section-title">
                <LayoutGrid size={20} className="text-indigo-600" />
                Amenities
            </h3>

            <div className="amenities-grid grid grid-cols-1 sm:grid-cols-2 gap-6">
                {Object.entries(grouped).map(([category, items]) => {
                    const CatIcon = (CATEGORIES[category] || { icons: LayoutGrid }).icons;
                    return (
                        <div key={category} className="amenity-category bg-slate-50 p-4 rounded-xl border border-slate-100">
                            <h4 className="flex items-center gap-2 mb-3 text-sm font-bold text-slate-700 uppercase tracking-wider">
                                <CatIcon size={16} className="text-indigo-500" />
                                {category}
                            </h4>
                            <ul className="amenity-list flex flex-col gap-2">
                                {items.map(item => (
                                    <li key={item} className="flex items-center justify-between group">
                                        <div className="flex items-center gap-2">
                                            <div className="w-1 h-1 bg-indigo-300 rounded-full" />
                                            <span className="text-sm text-slate-600 font-medium group-hover:text-slate-900 transition-colors">{item}</span>
                                        </div>
                                        {progress[item] !== undefined && (
                                            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md ${progress[item] === 100 ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-600'}`}>
                                                {progress[item] === 100 ? "Ready" : `${progress[item]}%`}
                                            </span>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
