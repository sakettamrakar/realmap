import type { Filters } from "../../types/filters";

interface Props {
    filters: Filters;
    onFiltersChange: (next: Partial<Filters>) => void;
    total: number;
}

const sortOptions: {
    value: Filters["sortBy"];
    label: string;
    defaultDir: Filters["sortDir"];
}[] = [
        { value: "overall_score", label: "Best Score", defaultDir: "desc" },
        { value: "value_score", label: "Best Value", defaultDir: "desc" },
        { value: "price", label: "Lowest Price", defaultDir: "asc" },
        { value: "registration_date", label: "Newest", defaultDir: "desc" },
        { value: "name", label: "Name (A-Z)", defaultDir: "asc" },
    ];

export function ProjectListHeader({ filters, onFiltersChange, total }: Props) {
    const activeChips: { key: string; label: string; onRemove: () => void }[] = [];

    if (filters.district) {
        activeChips.push({
            key: "district",
            label: filters.district,
            onRemove: () => onFiltersChange({ district: "" }),
        });
    }

    if (filters.projectTypes && filters.projectTypes.length > 0) {
        filters.projectTypes.forEach((type) => {
            activeChips.push({
                key: `type-${type}`,
                label: type,
                onRemove: () => onFiltersChange({
                    projectTypes: filters.projectTypes.filter(t => t !== type)
                }),
            });
        });
    }

    if (filters.statuses && filters.statuses.length > 0) {
        filters.statuses.forEach((status) => {
            activeChips.push({
                key: `status-${status}`,
                label: status,
                onRemove: () => onFiltersChange({
                    statuses: filters.statuses.filter(s => s !== status)
                }),
            });
        });
    }

    if (filters.minPrice || filters.maxPrice) {
        const min = filters.minPrice ? `₹${(filters.minPrice / 100000).toFixed(1)}L` : "0";
        const max = filters.maxPrice ? `₹${(filters.maxPrice / 100000).toFixed(1)}L` : "Any";
        activeChips.push({
            key: "price",
            label: `${min} - ${max}`,
            onRemove: () => onFiltersChange({ minPrice: undefined, maxPrice: undefined }),
        });
    }
    if (filters.nameQuery) {
        activeChips.push({
            key: "search",
            label: `"${filters.nameQuery}"`,
            onRemove: () => onFiltersChange({ nameQuery: "" }),
        });
    }

    const handleSortChange = (value: Filters["sortBy"]) => {
        const option = sortOptions.find((o) => o.value === value);
        onFiltersChange({
            sortBy: value,
            sortDir: option?.defaultDir ?? "desc",
        });
    };

    return (
        <div className="project-list-header">
            <div className="header-top">
                <h2 className="list-title">
                    Projects <span className="count">({total})</span>
                </h2>
                <div className="sort-controls">
                    <label>Sort by:</label>
                    <select
                        value={filters.sortBy}
                        onChange={(e) => handleSortChange(e.target.value as Filters["sortBy"])}
                        className="sort-select"
                    >
                        {sortOptions.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                                {opt.label}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {activeChips.length > 0 && (
                <div className="active-filters">
                    {activeChips.map((chip) => (
                        <button key={chip.key} className="filter-chip" onClick={chip.onRemove}>
                            {chip.label} <span className="close">×</span>
                        </button>
                    ))}
                    <button
                        className="clear-all-btn"
                        onClick={() =>
                            onFiltersChange({
                                district: "",
                                projectTypes: [],
                                statuses: [],
                                minPrice: undefined,
                                maxPrice: undefined,
                                nameQuery: "",
                            })
                        }
                    >
                        Clear all
                    </button>
                </div>
            )}
        </div>
    );
}
