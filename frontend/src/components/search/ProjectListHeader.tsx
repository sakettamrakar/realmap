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
                onRemove: () =>
                    onFiltersChange({
                        projectTypes: filters.projectTypes.filter((t) => t !== type),
                    }),
            });
        });
    }

    if (filters.statuses && filters.statuses.length > 0) {
        filters.statuses.forEach((status) => {
            activeChips.push({
                key: `status-${status}`,
                label: status,
                onRemove: () =>
                    onFiltersChange({
                        statuses: filters.statuses.filter((s) => s !== status),
                    }),
            });
        });
    }

    if (filters.minPrice || filters.maxPrice) {
        const min = filters.minPrice
            ? `₹${(filters.minPrice / 100000).toFixed(1)}L`
            : "0";
        const max = filters.maxPrice
            ? `₹${(filters.maxPrice / 100000).toFixed(1)}L`
            : "Any";
        activeChips.push({
            key: "price",
            label: `${min} - ${max}`,
            onRemove: () =>
                onFiltersChange({ minPrice: undefined, maxPrice: undefined }),
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
        <div className="mb-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
                    Projects <span className="text-slate-500 font-medium text-lg ml-1">({total})</span>
                </h2>
                <div className="flex items-center gap-3">
                    <label className="text-sm font-medium text-slate-600">Sort by:</label>
                    <select
                        value={filters.sortBy}
                        onChange={(e) =>
                            handleSortChange(e.target.value as Filters["sortBy"])
                        }
                        className="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 font-medium focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 cursor-pointer shadow-sm"
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
                <div className="flex flex-wrap items-center gap-2">
                    {activeChips.map((chip) => (
                        <button
                            key={chip.key}
                            className="inline-flex items-center gap-1.5 px-3 py-1 bg-sky-50 text-sky-700 rounded-full text-sm font-semibold hover:bg-sky-100 transition-colors border border-sky-100"
                            onClick={chip.onRemove}
                        >
                            {chip.label}
                            <span className="opacity-60 hover:opacity-100">×</span>
                        </button>
                    ))}
                    <button
                        className="text-sm text-slate-500 hover:text-red-600 px-2 py-1 font-medium underline decoration-slate-300 hover:decoration-red-300 underline-offset-2 transition-all"
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
                        Clear filters
                    </button>
                </div>
            )}
        </div>
    );
}
