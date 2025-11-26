import type { Filters } from "../../types/filters";

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

export function FiltersSidebar({ filters, onFiltersChange, onResetFilters, resultsCount }: Props) {
    return (
        <aside className="filters-sidebar">
            <div className="filters-header">
                <h3>Filters</h3>
                <button className="text-button" onClick={onResetFilters}>
                    Clear all
                </button>
            </div>

            <div className="filter-section">
                <label className="filter-label">Location</label>
                <select
                    className="filter-select"
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

            <div className="filter-section">
                <label className="filter-label">Budget (₹)</label>
                <div className="budget-inputs">
                    <input
                        type="number"
                        placeholder="Min"
                        value={filters.minPrice || ""}
                        onChange={(e) =>
                            onFiltersChange({ minPrice: e.target.value ? Number(e.target.value) : undefined })
                        }
                        className="filter-input"
                    />
                    <span className="separator">-</span>
                    <input
                        type="number"
                        placeholder="Max"
                        value={filters.maxPrice || ""}
                        onChange={(e) =>
                            onFiltersChange({ maxPrice: e.target.value ? Number(e.target.value) : undefined })
                        }
                        className="filter-input"
                    />
                </div>
            </div>

            <div className="filter-section">
                <label className="filter-label">Project Type</label>
                <div className="checkbox-group">
                    {projectTypeOptions.map((opt) => (
                        <label key={opt.value} className="checkbox-label">
                            <input
                                type="checkbox"
                                checked={filters.projectTypes.includes(opt.value)}
                                onChange={(e) => {
                                    const newTypes = e.target.checked
                                        ? [...filters.projectTypes, opt.value]
                                        : filters.projectTypes.filter((t) => t !== opt.value);
                                    onFiltersChange({ projectTypes: newTypes });
                                }}
                            />
                            {opt.label}
                        </label>
                    ))}
                </div>
            </div>

            <div className="filter-section">
                <label className="filter-label">Status</label>
                <div className="checkbox-group">
                    {statusOptions.map((opt) => (
                        <label key={opt.value} className="checkbox-label">
                            <input
                                type="checkbox"
                                checked={filters.statuses.includes(opt.value)}
                                onChange={(e) => {
                                    const newStatuses = e.target.checked
                                        ? [...filters.statuses, opt.value]
                                        : filters.statuses.filter((s) => s !== opt.value);
                                    onFiltersChange({ statuses: newStatuses });
                                }}
                            />
                            {opt.label}
                        </label>
                    ))}
                </div>
            </div>

            <div className="filter-section">
                <label className="filter-label">
                    Min Score: {filters.minOverallScore.toFixed(1)}
                </label>
                <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.1}
                    value={filters.minOverallScore}
                    onChange={(e) => onFiltersChange({ minOverallScore: Number(e.target.value) })}
                    className="filter-range"
                />
            </div>

            {resultsCount !== undefined && (
                <div className="filters-footer">
                    <p className="muted">{resultsCount} projects found</p>
                </div>
            )}
        </aside>
    );
}
