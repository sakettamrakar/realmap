import type { Filters } from "../../types/filters";
import { Button } from "../ui/Button";

interface Props {
    filters: Filters;
    onFiltersChange: (next: Partial<Filters>) => void;
    onResetFilters: () => void;
    resultsCount?: number;
}

const districtOptions = [
    "",
    "Raipur",
    "Durg",
    "Bilaspur",
    "Korba",
    "Rajnandgaon",
    "Raigarh",
    "Dhamtari",
    "Surguja",
    "Bastar",
    "Kanker",
];

const projectTypeOptions = [
    { value: "Residential", label: "Residential" },
    { value: "Commercial", label: "Commercial" },
    { value: "Mixed", label: "Mixed" },
    { value: "Plotted", label: "Plotted" },
];

const statusOptions = [
    { value: "Ongoing", label: "Ongoing" },
    { value: "Completed", label: "Completed" },
    { value: "New", label: "New" },
    { value: "Withdrawn", label: "Withdrawn" },
];

export function FiltersSidebar({
    filters,
    onFiltersChange,
    onResetFilters,
    resultsCount,
}: Props) {
    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 h-full overflow-y-auto w-full">
            <div className="flex items-center justify-between mb-6">
                <h3 className="font-bold text-slate-900 text-lg flex items-center gap-2">
                    <svg
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
                    </svg>
                    Filters
                </h3>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={onResetFilters}
                    className="text-slate-500 hover:text-red-600 hover:bg-red-50"
                >
                    Clear all
                </Button>
            </div>

            <div className="space-y-6">
                {/* Location */}
                <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700">Location</label>
                    <select
                        className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 transition-all"
                        value={filters.district}
                        onChange={(e) => onFiltersChange({ district: e.target.value })}
                    >
                        <option value="">All Districts</option>
                        {districtOptions.map((d) => (
                            <option key={d || "all"} value={d}>
                                {d}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Budget */}
                <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700">Budget (₹)</label>
                    <div className="flex items-center gap-2">
                        <input
                            type="number"
                            placeholder="Min"
                            value={filters.minPrice || ""}
                            onChange={(e) =>
                                onFiltersChange({
                                    minPrice: e.target.value ? Number(e.target.value) : undefined,
                                })
                            }
                            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 transition-all"
                        />
                        <span className="text-slate-400 font-medium">-</span>
                        <input
                            type="number"
                            placeholder="Max"
                            value={filters.maxPrice || ""}
                            onChange={(e) =>
                                onFiltersChange({
                                    maxPrice: e.target.value ? Number(e.target.value) : undefined,
                                })
                            }
                            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 transition-all"
                        />
                    </div>
                </div>

                {/* Project Type */}
                <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700">Project Type</label>
                    <div className="space-y-2">
                        {projectTypeOptions.map((opt) => (
                            <label key={opt.value} className="flex items-center gap-3 cursor-pointer group">
                                <input
                                    type="checkbox"
                                    className="w-4 h-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
                                    checked={filters.projectTypes.includes(opt.value)}
                                    onChange={(e) => {
                                        const newTypes = e.target.checked
                                            ? [...filters.projectTypes, opt.value]
                                            : filters.projectTypes.filter((t) => t !== opt.value);
                                        onFiltersChange({ projectTypes: newTypes });
                                    }}
                                />
                                <span className="text-sm text-slate-600 group-hover:text-slate-900 transition-colors">
                                    {opt.label}
                                </span>
                            </label>
                        ))}
                    </div>
                </div>

                {/* Status */}
                <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700">Status</label>
                    <div className="space-y-2">
                        {statusOptions.map((opt) => (
                            <label key={opt.value} className="flex items-center gap-3 cursor-pointer group">
                                <input
                                    type="checkbox"
                                    className="w-4 h-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
                                    checked={filters.statuses.includes(opt.value)}
                                    onChange={(e) => {
                                        const newStatuses = e.target.checked
                                            ? [...filters.statuses, opt.value]
                                            : filters.statuses.filter((s) => s !== opt.value);
                                        onFiltersChange({ statuses: newStatuses });
                                    }}
                                />
                                <span className="text-sm text-slate-600 group-hover:text-slate-900 transition-colors">
                                    {opt.label}
                                </span>
                            </label>
                        ))}
                    </div>
                </div>

                {/* Min Score */}
                <div className="space-y-3">
                    <div className="flex justify-between items-center text-sm">
                        <label className="font-semibold text-slate-700">Min Score</label>
                        <span className="font-bold text-sky-600">{filters.minOverallScore.toFixed(1)}</span>
                    </div>
                    <input
                        type="range"
                        min={0}
                        max={1}
                        step={0.1}
                        value={filters.minOverallScore}
                        onChange={(e) =>
                            onFiltersChange({ minOverallScore: Number(e.target.value) })
                        }
                        className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-sky-500"
                    />
                </div>

                {/* Advanced Options */}
                <div className="space-y-3 pt-4 border-t border-slate-100">
                    <label className="text-sm font-semibold text-slate-700">Advanced Options</label>
                    <div className="space-y-3">
                        <label className="flex items-center gap-3 cursor-pointer group">
                            <input
                                type="checkbox"
                                className="w-4 h-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
                                checked={filters.groupByParent}
                                onChange={(e) => onFiltersChange({ groupByParent: e.target.checked })}
                            />
                            <div className="flex flex-col">
                                <span className="text-sm text-slate-700 font-medium group-hover:text-slate-900 transition-colors">
                                    Group by Project
                                </span>
                                <span className="text-xs text-slate-500">
                                    Consolidate multiple RERA phases
                                </span>
                            </div>
                        </label>

                        <label className="flex items-center gap-3 cursor-pointer group">
                            <input
                                type="checkbox"
                                className="w-4 h-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
                                checked={filters.reraVerifiedOnly}
                                onChange={(e) => onFiltersChange({ reraVerifiedOnly: e.target.checked })}
                            />
                            <div className="flex flex-col">
                                <span className="text-sm text-slate-700 font-medium group-hover:text-slate-900 transition-colors">
                                    RERA Verified Only
                                </span>
                                <span className="text-xs text-slate-500">
                                    Show only trust-verified listings
                                </span>
                            </div>
                        </label>
                    </div>
                </div>
            </div>

            {resultsCount !== undefined && (
                <div className="mt-8 pt-6 border-t border-slate-100">
                    <p className="text-sm text-slate-500 font-medium text-center">
                        Found <span className="text-slate-900 font-bold">{resultsCount}</span> projects
                    </p>
                </div>
            )}
        </div>
    );
}
