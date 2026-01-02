
import { useEffect, useMemo, useState } from 'react';
import {
    LayoutGrid,
    List,
    CheckCircle,
    Ban,
    HelpCircle,
    Search,
    Filter,
    Home,
    Sparkles,
    BarChart3,
    Maximize2,
} from 'lucide-react';
import { getProjectInventory } from '../../api/projectsApi';
import type { ProjectInventoryResponse, UnitResponse } from '../../types/projects';

interface Props {
    projectId: number;
}

export function InventorySection({ projectId }: Props) {
    const [data, setData] = useState<ProjectInventoryResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
    const [filterStatus, setFilterStatus] = useState<string>('all');
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedUnit, setSelectedUnit] = useState<UnitResponse | null>(null);
    const [showExplorer, setShowExplorer] = useState(false);
    const [selectedGroup, setSelectedGroup] = useState<{
        title: string;
        badge?: string;
        description?: string;
        units: UnitResponse[];
    } | null>(null);

    useEffect(() => {
        if (!projectId) return;

        let isMounted = true;
        setLoading(true);

        getProjectInventory(projectId)
            .then(res => {
                if (isMounted) setData(res);
            })
            .catch(err => console.error(err))
            .finally(() => {
                if (isMounted) setLoading(false);
            });

        return () => { isMounted = false; };
    }, [projectId]);

    const units = useMemo(() => data?.units ?? [], [data]);

    const enrichedUnits = useMemo(() => {
        if (!units.length) return [] as UnitResponse[];
        return units.map((u) => {
            const carpetSqft = u.carpet_area_sqft ?? (u.carpet_area_sqm ? Math.round(u.carpet_area_sqm * 10.7639) : undefined);
            return { ...u, carpet_area_sqft: carpetSqft };
        });
    }, [units]);

    const filteredUnits = useMemo(() => {
        if (!enrichedUnits.length) return [];
        return enrichedUnits.filter(u => {
            const matchesSearch = !searchTerm ||
                u.unit_no?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                u.block_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                u.unit_type?.toLowerCase().includes(searchTerm.toLowerCase());

            const s = (u.status || '').toLowerCase();
            const matchesStatus = filterStatus === 'all' ||
                (filterStatus === 'available' && s === 'available') ||
                (filterStatus === 'booked' && (s === 'booked' || s === 'sold')) ||
                (filterStatus === 'unknown' && !u.status);

            return matchesSearch && matchesStatus;
        });
    }, [enrichedUnits, searchTerm, filterStatus]);

    const unitTypeSummary = useMemo(() => {
        if (!enrichedUnits.length) return [] as Array<{
            key: string;
            label: string;
            available: number;
            total: number;
            sold: number;
            minSqft?: number;
            maxSqft?: number;
        }>;

        const map = new Map<string, {
            key: string;
            label: string;
            available: number;
            total: number;
            sold: number;
            minSqft?: number;
            maxSqft?: number;
        }>();

        enrichedUnits.forEach((u) => {
            const key = u.unit_type || 'Uncategorized';
            const rec = map.get(key) ?? {
                key,
                label: key,
                available: 0,
                total: 0,
                sold: 0,
                minSqft: undefined,
                maxSqft: undefined,
            };

            rec.total += 1;
            const s = (u.status || '').toLowerCase();
            if (s === 'available') rec.available += 1;
            if (s === 'booked' || s === 'sold') rec.sold += 1;
            if (u.carpet_area_sqft) {
                rec.minSqft = rec.minSqft ? Math.min(rec.minSqft, u.carpet_area_sqft) : u.carpet_area_sqft;
                rec.maxSqft = rec.maxSqft ? Math.max(rec.maxSqft, u.carpet_area_sqft) : u.carpet_area_sqft;
            }

            map.set(key, rec);
        });

        return Array.from(map.values()).sort((a, b) => b.available - a.available || b.total - a.total);
    }, [enrichedUnits]);

    const getQuantile = (values: number[], q: number) => {
        if (!values.length) return undefined;
        const sorted = [...values].sort((a, b) => a - b);
        const pos = (sorted.length - 1) * q;
        const base = Math.floor(pos);
        const rest = pos - base;
        const next = sorted[base + 1];
        return next !== undefined ? sorted[base] + rest * (next - sorted[base]) : sorted[base];
    };

    const sizeBands = useMemo(() => {
        const areas = enrichedUnits.map(u => u.carpet_area_sqft).filter((v): v is number => Boolean(v));
        if (!areas.length) return [] as Array<{
            key: string;
            label: string;
            range: [number, number];
            units: UnitResponse[];
        }>;

        const min = Math.min(...areas);
        const max = Math.max(...areas);

        if (min === max) {
            return [{
                key: 'single-band',
                label: 'Single size band',
                range: [min, max],
                units: enrichedUnits,
            }];
        }

        const lower = getQuantile(areas, 0.33) ?? min;
        const upper = getQuantile(areas, 0.67) ?? max;

        const bands = [
            { key: 'compact', label: 'Compact', range: [min, lower] as [number, number] },
            { key: 'mid', label: 'Mid-size', range: [lower, upper] as [number, number] },
            { key: 'spacious', label: 'Spacious', range: [upper, max] as [number, number] },
        ].filter((band, idx, arr) => band.range[0] <= band.range[1] && (idx === 0 || band.range[0] !== arr[idx - 1].range[1] || band.range[1] !== arr[idx - 1].range[0]));

        return bands.map((band) => ({
            ...band,
            units: enrichedUnits.filter((u) => {
                const sqft = u.carpet_area_sqft;
                if (!sqft) return false;
                const [start, end] = band.range;
                return sqft >= start && sqft <= end;
            }),
        })).filter((band) => band.units.length > 0);
    }, [enrichedUnits]);

    if (loading) return (
        <div className="py-12 flex justify-center items-center text-slate-400 animate-pulse">
            <span className="flex items-center gap-2">
                Loading inventory live status...
            </span>
        </div>
    );

    if (!data || data.units.length === 0) return null;

    const formatArea = (unit: UnitResponse) => {
        if (unit.carpet_area_sqft) return `${unit.carpet_area_sqft} sqft`;
        if (unit.carpet_area_sqm) return `${unit.carpet_area_sqm} sqm`;
        return '-';
    };

    // Helper for status colors
    const getStatusColor = (status: string | undefined) => {
        const s = (status || '').toLowerCase();
        if (s === 'available') return 'bg-emerald-500 hover:bg-emerald-400 text-white';
        if (s === 'booked' || s === 'sold') return 'bg-rose-500 hover:bg-rose-400 text-white';
        return 'bg-slate-300 hover:bg-slate-400 text-slate-600';
    };

    // Helper for status badge
    const getStatusBadge = (status: string | undefined) => {
        const s = (status || '').toLowerCase();
        if (s === 'available') return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">Available</span>;
        if (s === 'booked' || s === 'sold') return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-rose-100 text-rose-700">Sold</span>;
        return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600">Unknown</span>;
    };

    return (
        <div className="detail-section inventory-section mt-8 animate-fade-in-up">
            <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4">
                <div>
                    <h3 className="section-title flex items-center gap-2 text-xl font-bold text-slate-800">
                        <LayoutGrid className="text-indigo-600" size={24} />
                        Inventory & Availability
                    </h3>
                    <p className="text-sm text-slate-500 mt-1">
                        Real-time availability across {data.stats.total_units} units
                    </p>
                </div>

                <div className="flex gap-2 bg-slate-100 p-1 rounded-lg self-start md:self-auto">
                    <button
                        onClick={() => setViewMode('grid')}
                        className={`p-2 rounded-md transition-all ${viewMode === 'grid' ? 'bg-white shadow text-indigo-600' : 'text-slate-500 hover:text-indigo-600'}`}
                    >
                        <LayoutGrid size={18} />
                    </button>
                    <button
                        onClick={() => setViewMode('list')}
                        className={`p-2 rounded-md transition-all ${viewMode === 'list' ? 'bg-white shadow text-indigo-600' : 'text-slate-500 hover:text-indigo-600'}`}
                    >
                        <List size={18} />
                    </button>
                </div>
            </div>

            {/* Stats Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                    <div className="p-3 bg-indigo-50 rounded-full text-indigo-600">
                        <Home size={24} />
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-slate-800">{data.stats.total_units}</div>
                        <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Total Units</div>
                    </div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-emerald-100 bg-emerald-50/30 shadow-sm flex items-center gap-4">
                    <div className="p-3 bg-emerald-100 rounded-full text-emerald-600">
                        <CheckCircle size={24} />
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-emerald-700">{data.stats.available_units}</div>
                        <div className="text-xs text-emerald-600 uppercase tracking-wider font-semibold">Available</div>
                    </div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-rose-100 bg-rose-50/30 shadow-sm flex items-center gap-4">
                    <div className="p-3 bg-rose-100 rounded-full text-rose-600">
                        <Ban size={24} />
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-rose-700">{data.stats.booked_units}</div>
                        <div className="text-xs text-rose-600 uppercase tracking-wider font-semibold">Sold/Booked</div>
                    </div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                    <div className="p-3 bg-slate-100 rounded-full text-slate-500">
                        <HelpCircle size={24} />
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-slate-700">{data.stats.unknown_units}</div>
                        <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Status Unknown</div>
                    </div>
                </div>
            </div>

            {/* Smart summaries */}
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-5 mb-6">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div>
                        <div className="flex items-center gap-2 text-indigo-600 font-semibold text-xs uppercase tracking-wide">
                            <Sparkles size={16} />
                            Smart unit mix
                        </div>
                        <div className="text-lg font-bold text-slate-800 mt-1">{data.stats.available_units} flats currently available</div>
                        <p className="text-sm text-slate-500 mt-1">Tap a size band or typology to open flat-level detail without flooding the page.</p>
                    </div>
                    <button
                        onClick={() => setShowExplorer(!showExplorer)}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-indigo-200 text-indigo-700 bg-indigo-50 hover:bg-indigo-100 text-sm font-semibold"
                    >
                        <Maximize2 size={16} /> {showExplorer ? 'Hide detailed explorer' : 'Open detailed explorer'}
                    </button>
                </div>

                {unitTypeSummary.length > 0 && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 mt-4">
                        {unitTypeSummary.map((t) => (
                            <div key={t.key} className="border border-slate-100 rounded-lg p-4 bg-slate-50/70 hover:bg-white transition-all shadow-sm">
                                <div className="flex items-center justify-between">
                                    <div className="text-sm font-semibold text-slate-800">{t.label}</div>
                                    <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700">{t.available} available</span>
                                </div>
                                <div className="text-xs text-slate-500 mt-1">{t.total} total · {t.sold} sold/booked</div>
                                <div className="text-sm text-slate-600 mt-2">
                                    {t.minSqft && t.maxSqft ? `${Math.round(t.minSqft)} - ${Math.round(t.maxSqft)} sqft` : 'Area on file soon'}
                                </div>
                                <button
                                    className="mt-3 inline-flex items-center gap-2 text-indigo-600 text-sm font-semibold hover:underline"
                                    onClick={() => setSelectedGroup({
                                        title: `${t.label} flats`,
                                        badge: `${t.available} open / ${t.total} total`,
                                        description: t.minSqft && t.maxSqft ? `${Math.round(t.minSqft)} - ${Math.round(t.maxSqft)} sqft band` : undefined,
                                        units: enrichedUnits.filter(u => (u.unit_type || 'Uncategorized') === t.key),
                                    })}
                                >
                                    View flats
                                    <BarChart3 size={16} />
                                </button>
                            </div>
                        ))}
                    </div>
                )}

                {sizeBands.length > 0 && (
                    <div className="mt-6">
                        <div className="text-xs uppercase tracking-wide text-slate-500 font-semibold">Sizes by sqft</div>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
                            {sizeBands.map((band) => {
                                const available = band.units.filter((u) => (u.status || '').toLowerCase() === 'available');
                                return (
                                    <button
                                        key={band.key}
                                        onClick={() => setSelectedGroup({
                                            title: `${band.label} flats`,
                                            badge: `${available.length} available` + (band.units.length ? ` · ${band.units.length} total` : ''),
                                            description: `${Math.round(band.range[0])} - ${Math.round(band.range[1])} sqft`,
                                            units: band.units,
                                        })}
                                        className="flex flex-col items-start gap-2 p-4 text-left rounded-lg border border-indigo-100 bg-indigo-50 hover:bg-indigo-100 transition-all shadow-sm"
                                    >
                                        <div className="text-sm font-semibold text-slate-800">{band.label}</div>
                                        <div className="text-lg font-bold text-indigo-700">{Math.round(band.range[0])} - {Math.round(band.range[1])} sqft</div>
                                        <div className="text-xs text-slate-600">{available.length} available · {band.units.length} total</div>
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>

            {/* Filters Bar */}
            {showExplorer && (
            <div className="flex flex-col md:flex-row gap-4 mb-6 bg-white p-4 rounded-lg border border-slate-200 shadow-sm items-center">
                <div className="relative flex-1 w-full">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                    <input
                        type="text"
                        placeholder="Search unit number, block, or type..."
                        className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="flex items-center gap-2 w-full md:w-auto">
                    <Filter className="text-slate-400" size={18} />
                    <select
                        className="flex-1 md:w-48 py-2 px-3 border border-slate-200 rounded-lg bg-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                    >
                        <option value="all">All Statuses</option>
                        <option value="available">Available Only</option>
                        <option value="booked">Sold/Booked</option>
                        <option value="unknown">Unknown</option>
                    </select>
                </div>
            </div>
            )}

            {/* Content Area */}
            {showExplorer && (viewMode === 'grid' ? (
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                    {filteredUnits.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                            {filteredUnits.map((u) => (
                                <div
                                    key={u.id}
                                    onClick={() => setSelectedUnit(u)}
                                    className={`
                                        w-10 h-10 rounded-md flex items-center justify-center text-xs font-bold cursor-pointer transition-all transform hover:scale-110 shadow-sm
                                        ${getStatusColor(u.status)}
                                    `}
                                    title={`Unit ${u.unit_no} (${u.block_name || 'Block ?'}) - ${u.status}`}
                                >
                                    {u.unit_no?.replace(/[^\d]/g, '').slice(-3) || u.unit_no?.slice(0, 3)}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-12 text-slate-400">No units match your filters</div>
                    )}

                    {/* Legend */}
                    <div className="mt-6 pt-4 border-t border-slate-100 flex gap-6 text-sm text-slate-600 justify-center">
                        <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-emerald-500"></div> Available</div>
                        <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-rose-500"></div> Sold/Booked</div>
                        <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-slate-300"></div> Unknown</div>
                    </div>
                </div>
            ) : (
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                                <tr>
                                    <th className="px-6 py-3">Block</th>
                                    <th className="px-6 py-3">Unit No</th>
                                    <th className="px-6 py-3">Type</th>
                                    <th className="px-6 py-3">Floor</th>
                                    <th className="px-6 py-3">Carpet Area</th>
                                    <th className="px-6 py-3">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {filteredUnits.map((u) => (
                                    <tr key={u.id} className="hover:bg-slate-50 transition-colors cursor-pointer" onClick={() => setSelectedUnit(u)}>
                                        <td className="px-6 py-3 text-slate-800 font-medium">{u.block_name || "-"}</td>
                                        <td className="px-6 py-3 text-indigo-600 font-bold">{u.unit_no}</td>
                                        <td className="px-6 py-3 text-slate-600">{u.unit_type || "-"}</td>
                                        <td className="px-6 py-3 text-slate-600">{u.floor_no || "-"}</td>
                                        <td className="px-6 py-3 text-slate-600">{formatArea(u)}</td>
                                        <td className="px-6 py-3">
                                            {getStatusBadge(u.status)}
                                        </td>
                                    </tr>
                                ))}
                                {filteredUnits.length === 0 && (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-8 text-center text-slate-400">
                                            No units available
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            ))}

            {/* Quick Detail Modal/Overlay (Optional enhancement if I had more time, for now simple details below) */}
            {selectedUnit && (
                <div className="mt-4 p-4 bg-indigo-50 border border-indigo-100 rounded-lg animate-fade-in flex flex-wrap gap-6 items-center justify-between">
                    <div>
                        <div className="text-xs text-indigo-500 font-semibold uppercase tracking-wide">Selected Unit</div>
                        <div className="text-xl font-bold text-indigo-900">
                            {selectedUnit.block_name ? `${selectedUnit.block_name} - ` : ''}{selectedUnit.unit_no}
                        </div>
                    </div>
                    <div className="flex gap-8 text-sm">
                        <div>
                            <span className="block text-slate-400 text-xs">Type</span>
                            <span className="font-medium text-slate-700">{selectedUnit.unit_type || "N/A"}</span>
                        </div>
                        <div>
                            <span className="block text-slate-400 text-xs">Carpet Area</span>
                            <span className="font-medium text-slate-700">{selectedUnit.carpet_area_sqft ? `${selectedUnit.carpet_area_sqft} sqft` : selectedUnit.carpet_area_sqm ? `${selectedUnit.carpet_area_sqm} m²` : "N/A"}</span>
                        </div>
                        <div>
                            <span className="block text-slate-400 text-xs">Floor</span>
                            <span className="font-medium text-slate-700">{selectedUnit.floor_no || "N/A"}</span>
                        </div>
                    </div>
                    <div>
                        {getStatusBadge(selectedUnit.status)}
                    </div>
                    <button
                        onClick={() => setSelectedUnit(null)}
                        className="text-slate-400 hover:text-slate-600"
                    >
                        ✕
                    </button>
                </div>
            )}

            {selectedGroup && (
                <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-50 px-4">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[80vh] overflow-hidden border border-slate-200">
                        <div className="flex items-start justify-between p-5 border-b border-slate-100">
                            <div>
                                <div className="text-xs uppercase tracking-wide text-indigo-500 font-semibold">Flat details</div>
                                <div className="text-xl font-bold text-slate-900 mt-1">{selectedGroup.title}</div>
                                {selectedGroup.description && <div className="text-sm text-slate-500">{selectedGroup.description}</div>}
                                {selectedGroup.badge && <div className="text-sm text-emerald-600 font-semibold mt-1">{selectedGroup.badge}</div>}
                            </div>
                            <button
                                onClick={() => setSelectedGroup(null)}
                                className="text-slate-400 hover:text-slate-600 text-xl leading-none"
                            >
                                ✕
                            </button>
                        </div>
                        <div className="overflow-auto max-h-[65vh]">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                                    <tr>
                                        <th className="px-5 py-3">Block</th>
                                        <th className="px-5 py-3">Unit No</th>
                                        <th className="px-5 py-3">Type</th>
                                        <th className="px-5 py-3">Floor</th>
                                        <th className="px-5 py-3">Carpet Area</th>
                                        <th className="px-5 py-3">Status</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {selectedGroup.units.map((u) => (
                                        <tr key={u.id} className="hover:bg-slate-50 transition-colors">
                                            <td className="px-5 py-3 text-slate-800 font-medium">{u.block_name || '-'}</td>
                                            <td className="px-5 py-3 text-indigo-600 font-bold">{u.unit_no}</td>
                                            <td className="px-5 py-3 text-slate-600">{u.unit_type || '-'}</td>
                                            <td className="px-5 py-3 text-slate-600">{u.floor_no || '-'}</td>
                                            <td className="px-5 py-3 text-slate-600">{formatArea(u)}</td>
                                            <td className="px-5 py-3">{getStatusBadge(u.status)}</td>
                                        </tr>
                                    ))}
                                    {selectedGroup.units.length === 0 && (
                                        <tr>
                                            <td colSpan={6} className="px-5 py-6 text-center text-slate-400">No flats in this band</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
