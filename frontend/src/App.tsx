import { useEffect, useMemo, useState } from "react";
import { searchProjects, getProject, getProjectsForMap } from "./api/projectsApi";
import { FiltersSidebar } from "./components/search/FiltersSidebar";
import { ProjectListHeader } from "./components/search/ProjectListHeader";
import ProjectCard from "./components/ProjectCard";
import ProjectMapView from "./components/ProjectMapView";
import ProjectDetailPanel from "./components/ProjectDetailPanel";
import ShortlistPanel from "./components/ShortlistPanel";
import CompareModal from "./components/CompareModal";
import ProjectInspector from "./components/ProjectInspector";
import { BottomNav } from "./components/mobile/BottomNav";
import { ComplianceProgress } from "./components/mobile/ComplianceProgress";
import { AIChatAssistant } from "./components/ai/AIChatAssistant";
import useDebouncedValue from "./hooks/useDebouncedValue";
import { Button } from "./components/ui/Button";
import type { Filters } from "./types/filters";
import type { BBox, ProjectDetail, ProjectMapPin, ProjectSummary } from "./types/projects";

const DEFAULT_SORT_BY = "overall_score" as const;
const DEFAULT_SORT_DIR = "desc" as const;
const PAGE_SIZE = 20;

const DEFAULT_FILTERS: Filters = {
  district: "",
  minOverallScore: 0,
  nameQuery: "",
  projectTypes: [],
  statuses: [],
  sortBy: DEFAULT_SORT_BY,
  sortDir: DEFAULT_SORT_DIR,
  tags: [],
  tagsMatchAll: false,
  reraVerifiedOnly: false,
};

const DEFAULT_BOUNDS: BBox = {
  minLat: 17.5,
  minLon: 80.0,
  maxLat: 24.5,
  maxLon: 84.5,
};

function App() {
  const [filters, setFilters] = useState<Filters>({ ...DEFAULT_FILTERS });
  const debouncedFilters = useDebouncedValue(filters, 300);
  const [searchResults, setSearchResults] = useState<ProjectSummary[]>([]);
  const [searchMeta, setSearchMeta] = useState<{ total: number; page: number; pageSize: number }>(
    { total: 0, page: 1, pageSize: PAGE_SIZE },
  );
  const [searchLoading, setSearchLoading] = useState(false);

  const [mapPins, setMapPins] = useState<ProjectMapPin[]>([]);
  const [mapBounds, setMapBounds] = useState<BBox | null>(DEFAULT_BOUNDS);
  const [mapLoading, setMapLoading] = useState(false);
  const [mapFocus, setMapFocus] = useState<{ lat: number; lon: number; zoom?: number; timestamp?: number } | null>(null);

  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [selectedProject, setSelectedProject] = useState<ProjectDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [hoveredProjectId, setHoveredProjectId] = useState<number | null>(null);

  const [shortlist, setShortlist] = useState<ProjectSummary[]>([]);
  const [isShortlistOpen, setIsShortlistOpen] = useState(false);
  const [compareSelection, setCompareSelection] = useState<number[]>([]);
  const [compareWarning, setCompareWarning] = useState<string | null>(null);

  const [compareProjects, setCompareProjects] = useState<ProjectDetail[]>([]);
  const [compareOpen, setCompareOpen] = useState(false);
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState<string | null>(null);

  const [showInspector, setShowInspector] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Mobile State
  const [activeTab, setActiveTab] = useState<'home' | 'check' | 'compare' | 'saved'>('home');
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const [isChecking, setIsChecking] = useState(false);

  // Use shortlistIds to avoid unused variable warning and for cleaner checks
  const shortlistIds = useMemo(() => shortlist.map((item) => Number(item.project_id)), [shortlist]);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const handleFiltersChange = (next: Partial<Filters>) => {
    setFilters((prev) => ({ ...prev, ...next }));
    setSearchMeta((prev) => ({ ...prev, page: 1 }));
  };

  const handleResetFilters = () => {
    setFilters({ ...DEFAULT_FILTERS });
    setSearchMeta((prev) => ({ ...prev, page: 1 }));
  };

  const handlePageChange = (nextPage: number) => {
    setSearchMeta((prev) => ({ ...prev, page: nextPage }));
  };

  useEffect(() => {
    const saved = localStorage.getItem("realmap_shortlist");
    if (saved) {
      try {
        const parsed = JSON.parse(saved) as ProjectSummary[];
        setShortlist(parsed);
        setCompareSelection((prev) => prev.filter((id) => parsed.some((p) => p.project_id === id)));
      } catch (err) {
        console.error("Failed to read shortlist", err);
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("realmap_shortlist", JSON.stringify(shortlist));
    setCompareSelection((prev) => prev.filter((id) => shortlist.some((p) => p.project_id === id)));
  }, [shortlist]);

  useEffect(() => {
    let active = true;
    setSearchLoading(true);
    setError(null);

    searchProjects({
      ...debouncedFilters,
      page: searchMeta.page,
      page_size: searchMeta.pageSize,
    })
      .then((res) => {
        if (!active) return;
        setSearchResults(res.items);
        setSearchMeta((prev) => ({ ...prev, total: res.total }));
      })
      .catch((err) => {
        if (!active) return;
        console.error("Search failed", err);
        setError("Failed to load projects. Please try again.");
      })
      .finally(() => {
        if (active) setSearchLoading(false);
      });

    return () => {
      active = false;
    };
  }, [debouncedFilters, searchMeta.page, searchMeta.pageSize]);

  useEffect(() => {
    if (!mapBounds) return;
    let active = true;
    setMapLoading(true);

    getProjectsForMap({ bbox: mapBounds })
      .then((res) => {
        if (!active) return;
        setMapPins(res.items);
      })
      .catch((err) => {
        console.error("Map load failed", err);
      })
      .finally(() => {
        if (active) setMapLoading(false);
      });

    return () => {
      active = false;
    };
  }, [mapBounds]);

  useEffect(() => {
    if (!selectedProjectId) {
      setSelectedProject(null);
      return;
    }
    setDetailLoading(true);
    getProject(selectedProjectId)
      .then(setSelectedProject)
      .catch((err) => console.error("Detail load failed", err))
      .finally(() => setDetailLoading(false));
  }, [selectedProjectId]);

  useEffect(() => {
    if (hoveredProjectId) {
      const el = document.getElementById(`project-card-${hoveredProjectId}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    }
  }, [hoveredProjectId]);

  const handleSelectProject = (id: number) => {
    setSelectedProjectId(id);
  };

  const handleCloseDetail = () => {
    setSelectedProjectId(null);
  };

  const handleToggleShortlist = (project: ProjectSummary, wasShortlisted: boolean) => {
    if (wasShortlisted) {
      setShortlist((prev) => prev.filter((p) => Number(p.project_id) !== Number(project.project_id)));
    } else {
      setShortlist((prev) => [...prev, project]);
    }
  };

  const handleToggleCompare = (id: number) => {
    setCompareSelection((prev) => {
      if (prev.includes(id)) {
        setCompareWarning(null);
        return prev.filter((pid) => pid !== id);
      }
      if (prev.length >= 3) {
        setCompareWarning("You can compare up to 3 projects.");
        setTimeout(() => setCompareWarning(null), 3000);
        return prev;
      }
      setCompareWarning(null);
      return [...prev, id];
    });
  };

  const handleOpenCompare = async () => {
    if (compareSelection.length < 2) {
      setCompareWarning("Select at least 2 projects to compare.");
      setTimeout(() => setCompareWarning(null), 3000);
      return;
    }
    setCompareOpen(true);
    setCompareLoading(true);
    setCompareError(null);
    try {
      const details = await Promise.all(compareSelection.map((id) => getProject(id)));
      setCompareProjects(details.filter((d): d is ProjectDetail => !!d));
    } catch (err) {
      console.error("Compare load failed", err);
      setCompareError("Failed to load comparison data.");
    } finally {
      setCompareLoading(false);
    }
  };

  const handleLocateProject = (coords: { lat: number; lon: number }) => {
    setMapFocus({ ...coords, zoom: 16, timestamp: Date.now() });
  };

  const handleCheckCompliance = () => {
    setIsChecking(true);
  };

  const handleCheckComplete = () => {
    setIsChecking(false);
    setActiveTab('check');
  };

  // Mobile Tab Content Rendering
  const renderMobileContent = () => {
    switch (activeTab) {
      case 'home':
        return (
          <div className="flex flex-col h-full bg-slate-50 overflow-hidden">
            <div className="p-4 bg-white shadow-sm border-b border-slate-100 z-10 sticky top-0">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-lg font-bold text-slate-900">Discover</h2>
                <Button variant="ghost" size="sm" onClick={() => {/* Toggle filters modal? */ }}>
                  Filters
                </Button>
              </div>
              <div className="overflow-x-auto pb-2">
                <ProjectListHeader
                  filters={filters}
                  onFiltersChange={handleFiltersChange}
                  total={searchMeta.total}
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-4 pb-24 space-y-4">
              {searchLoading ? (
                <div className="flex items-center justify-center h-40">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500"></div>
                </div>
              ) : (
                searchResults.map((p) => (
                  <div key={p.project_id} id={`mobile-project-card-${p.project_id}`}>
                    <ProjectCard
                      project={p}
                      selected={selectedProjectId === p.project_id}
                      onSelect={handleSelectProject}
                      hovered={hoveredProjectId === p.project_id}
                      onHover={setHoveredProjectId}
                      isShortlisted={shortlistIds.includes(Number(p.project_id))}
                      onToggleShortlist={handleToggleShortlist}
                    />
                  </div>
                ))
              )}
            </div>

            <button
              onClick={handleCheckCompliance}
              className="fixed bottom-20 right-4 bg-sky-500 text-white rounded-full p-4 shadow-lg shadow-sky-500/30 flex items-center justify-center z-30"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mr-0"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
            </button>
          </div>
        );
      case 'check':
        return (
          <div className="h-[calc(100vh-60px)] relative">
            <ProjectMapView
              pins={mapPins}
              selectedProjectId={selectedProjectId}
              hoveredProjectId={hoveredProjectId}
              onSelectProject={handleSelectProject}
              onHoverProject={setHoveredProjectId}
              onBoundsChange={setMapBounds}
              loading={mapLoading}
              initialBounds={DEFAULT_BOUNDS}
              focus={mapFocus}
            />
          </div>
        );
      case 'compare':
        return (
          <div className="p-4 pt-16 h-full overflow-y-auto bg-slate-50">
            <h2 className="text-2xl font-bold mb-4">Compare Projects</h2>
            <ShortlistPanel
              open={true}
              shortlist={shortlist}
              onRemove={(id) => handleToggleShortlist({ project_id: id } as any, true)}
              onSelectProject={handleSelectProject}
              onClose={() => { }}
              compareSelection={compareSelection}
              onToggleCompareSelection={handleToggleCompare}
              onOpenCompare={handleOpenCompare}
              warning={compareWarning}
            />
          </div>
        );
      case 'saved':
        return (
          <div className="p-4 pt-16 h-full overflow-y-auto bg-slate-50 pb-24">
            <h2 className="text-2xl font-bold mb-6">Saved Projects</h2>
            <div className="grid grid-cols-1 gap-4">
              {shortlist.map((p) => (
                <ProjectCard
                  key={p.project_id}
                  project={p}
                  selected={selectedProjectId === p.project_id}
                  onSelect={handleSelectProject}
                  isShortlisted={true}
                  onToggleShortlist={handleToggleShortlist}
                />
              ))}
              {shortlist.length === 0 && <p className="text-slate-500 italic">No saved projects yet.</p>}
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-slate-50 font-sans text-slate-900">
      <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-slate-200 shadow-sm transition-all duration-300">
        <div className="container mx-auto px-4 max-w-screen-2xl h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-sky-500 to-indigo-600 rounded-lg flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-sky-500/20">
              R
            </div>
            <div>
              <h1 className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-700 leading-tight">RealMap</h1>
              <p className="text-[10px] text-slate-500 font-medium hidden sm:block uppercase tracking-wider">CG-RERA Analytics</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {!isMobile && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsShortlistOpen(true)}
                  className="hidden md:inline-flex"
                >
                  Shortlist ({shortlist.length})
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowInspector(!showInspector)}
                  className="hidden md:inline-flex"
                >
                  {showInspector ? "Hide Inspector" : "Inspector"}
                </Button>
              </>
            )}
          </div>
        </div>
      </header>

      {error && (
        <div className="container mx-auto px-4 mt-4 max-w-screen-2xl">
          <div className="bg-red-50 text-red-700 px-4 py-3 rounded-xl border border-red-100 flex items-center gap-3 shadow-sm">
            <svg className="w-5 h-5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" /></svg>
            <span className="font-medium">{error}</span>
          </div>
        </div>
      )}

      {isChecking && <ComplianceProgress onComplete={handleCheckComplete} />}

      <main className="flex-1 container mx-auto px-4 py-6 max-w-screen-2xl overflow-hidden flex flex-col">
        {isMobile ? (
          <>
            {renderMobileContent()}
            <BottomNav activeTab={activeTab} onTabChange={setActiveTab} />
          </>
        ) : (
          <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-140px)] min-h-[600px]">
            {/* Sidebar */}
            <aside className="w-full lg:w-80 shrink-0 h-full hidden lg:block">
              <FiltersSidebar
                filters={filters}
                onFiltersChange={handleFiltersChange}
                onResetFilters={handleResetFilters}
                resultsCount={searchMeta.total}
              />
            </aside>

            {/* Results */}
            <div className="flex-1 flex flex-col min-w-0 h-full">
              <ProjectListHeader
                filters={filters}
                onFiltersChange={handleFiltersChange}
                total={searchMeta.total}
              />

              <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-5 gap-6 h-full overflow-hidden">
                {/* List Column */}
                <div className="xl:col-span-3 h-full overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-slate-200 scrollbar-track-transparent">
                  {searchLoading ? (
                    <div className="flex items-center justify-center p-12">
                      <div className="w-8 h-8 rounded-full border-4 border-slate-200 border-t-sky-500 animate-spin"></div>
                    </div>
                  ) : (
                    <>
                      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 pb-12">
                        {searchResults.map((p) => (
                          <div
                            key={p.project_id}
                            id={`project-card-${p.project_id}`}
                            className="bg-white rounded-xl h-full"
                          >
                            <ProjectCard
                              project={p}
                              selected={selectedProjectId === p.project_id}
                              onSelect={handleSelectProject}
                              hovered={hoveredProjectId === p.project_id}
                              onHover={setHoveredProjectId}
                              isShortlisted={shortlistIds.includes(Number(p.project_id))}
                              onToggleShortlist={handleToggleShortlist}
                            />
                          </div>
                        ))}
                      </div>

                      {searchResults.length === 0 && !searchLoading && (
                        <div className="flex flex-col items-center justify-center text-center p-12 border-2 border-dashed border-slate-200 rounded-2xl bg-slate-50/50">
                          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                          </div>
                          <h3 className="text-lg font-bold text-slate-900 mb-1">No projects found</h3>
                          <p className="text-slate-500 max-w-xs">We couldn't find any projects matching your current filters. Try adjusting them.</p>
                          <Button variant="secondary" onClick={handleResetFilters} className="mt-4">
                            Clear Filters
                          </Button>
                        </div>
                      )}

                      {/* Pagination Controls */}
                      {searchResults.length > 0 && (
                        <div className="flex justify-center items-center gap-4 mt-auto py-6 border-t border-slate-100">
                          <Button
                            variant="secondary"
                            disabled={searchMeta.page <= 1}
                            onClick={() => handlePageChange(searchMeta.page - 1)}
                            className="w-24"
                          >
                            Previous
                          </Button>
                          <span className="text-sm font-medium text-slate-600">
                            Page {searchMeta.page} of {Math.ceil(searchMeta.total / searchMeta.pageSize)}
                          </span>
                          <Button
                            variant="secondary"
                            disabled={searchMeta.page * searchMeta.pageSize >= searchMeta.total}
                            onClick={() => handlePageChange(searchMeta.page + 1)}
                            className="w-24"
                          >
                            Next
                          </Button>
                        </div>
                      )}
                    </>
                  )}
                </div>

                {/* Map Column */}
                <div className="xl:col-span-2 hidden xl:block h-full rounded-2xl overflow-hidden border border-slate-200 shadow-sm relative bg-slate-100 group">
                  <div className="absolute inset-0 z-0">
                    <ProjectMapView
                      pins={mapPins}
                      selectedProjectId={selectedProjectId}
                      hoveredProjectId={hoveredProjectId}
                      onSelectProject={handleSelectProject}
                      onHoverProject={setHoveredProjectId}
                      onBoundsChange={setMapBounds}
                      loading={mapLoading}
                      initialBounds={DEFAULT_BOUNDS}
                      focus={mapFocus}
                    />
                  </div>
                  {/* Sticky Map Header/Legend could go here */}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Slide-overs / Modals */}
      {selectedProject && (
        <ProjectDetailPanel
          project={selectedProject}
          onClose={handleCloseDetail}
          loading={detailLoading}
          onCenterOnProject={handleLocateProject}
        />
      )}

      {isShortlistOpen && !isMobile && (
        <ShortlistPanel
          open={isShortlistOpen}
          shortlist={shortlist}
          onRemove={(id) => handleToggleShortlist({ project_id: id } as any, true)}
          onSelectProject={handleSelectProject}
          onClose={() => setIsShortlistOpen(false)}
          compareSelection={compareSelection}
          onToggleCompareSelection={handleToggleCompare}
          onOpenCompare={handleOpenCompare}
          warning={compareWarning}
        />
      )}

      {compareError && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[100] bg-red-50 text-red-800 px-6 py-3 rounded-full shadow-lg border border-red-200 font-medium animate-in slide-in-from-bottom-4 duration-300">
          {compareError}
        </div>
      )}

      {compareOpen && (
        <CompareModal
          open={compareOpen}
          projects={compareProjects}
          loading={compareLoading}
          onClose={() => setCompareOpen(false)}
          selectionCount={compareSelection.length}
        />
      )}

      {showInspector && !isMobile && (
        <ProjectInspector
          onBack={() => setShowInspector(false)}
        />
      )}

      {/* Feature 6: AI Chat Assistant */}
      <AIChatAssistant onSelectProject={handleSelectProject} />
    </div>
  );
}

export default App;
