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
import useDebouncedValue from "./hooks/useDebouncedValue";
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
          <div className="mobile-home-view animate-fade-in">
            <div className="filters-section" style={{ padding: '16px', background: 'white', marginBottom: '16px' }}>
              <FiltersSidebar
                filters={filters}
                onFiltersChange={handleFiltersChange}
                onResetFilters={handleResetFilters}
                resultsCount={searchMeta.total}
              />
            </div>
            <div className="project-list" style={{ padding: '0 16px 80px' }}>
              <ProjectListHeader
                filters={filters}
                onFiltersChange={handleFiltersChange}
                total={searchMeta.total}
              />
              {searchLoading ? (
                <div className="loading-state">Loading projects...</div>
              ) : (
                <div className="results-grid" style={{ gridTemplateColumns: '1fr' }}>
                  {searchResults.map((p) => (
                    <div key={p.project_id} className="animate-slide-up">
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
              )}
            </div>
            <button
              onClick={handleCheckCompliance}
              style={{
                position: 'fixed',
                bottom: '80px',
                right: '16px',
                background: 'var(--color-primary)',
                color: 'white',
                border: 'none',
                borderRadius: '999px',
                padding: '12px 20px',
                fontWeight: 600,
                boxShadow: '0 4px 12px rgba(14, 165, 233, 0.4)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                zIndex: 900
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
              Check Compliance
            </button>
          </div>
        );
      case 'check':
        return (
          <div className="mobile-check-view animate-fade-in" style={{ height: 'calc(100vh - 120px)' }}>
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
          <div className="mobile-compare-view animate-fade-in" style={{ padding: '16px' }}>
            <h2>Compare Projects</h2>
            <p>Select projects to compare from the Home tab.</p>
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
          <div className="mobile-saved-view animate-fade-in" style={{ padding: '16px' }}>
            <h2>Saved Projects</h2>
            <div className="results-grid" style={{ gridTemplateColumns: '1fr', gap: '16px' }}>
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
              {shortlist.length === 0 && <p className="muted">No saved projects yet.</p>}
            </div>
            <button
              onClick={handleCheckCompliance}
              style={{
                position: 'fixed',
                bottom: '80px',
                right: '16px',
                background: 'var(--color-primary)',
                color: 'white',
                border: 'none',
                borderRadius: '999px',
                padding: '12px 20px',
                fontWeight: 600,
                boxShadow: '0 4px 12px rgba(14, 165, 233, 0.4)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                zIndex: 900
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
              Check Compliance
            </button>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="container header-content">
          <div>
            <h1>RealMap</h1>
            <p className="text-on-dark">CG-RERA Compliance & Analytics Platform</p>
          </div>
          <div className="header-actions">
            {!isMobile && (
              <>
                <button className="header-pill" onClick={() => setIsShortlistOpen(true)}>
                  Shortlist ({shortlist.length})
                </button>
                <button className="header-pill" onClick={() => setShowInspector(!showInspector)}>
                  {showInspector ? "Hide Inspector" : "Inspector"}
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {error && (
        <div className="container banner banner-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {isChecking && <ComplianceProgress onComplete={handleCheckComplete} />}

      <main className="app-main container">
        {isMobile ? (
          <>
            {renderMobileContent()}
            <BottomNav activeTab={activeTab} onTabChange={setActiveTab} />
          </>
        ) : (
          <div className="new-layout">
            <aside className="filters-sidebar">
              <FiltersSidebar
                filters={filters}
                onFiltersChange={handleFiltersChange}
                onResetFilters={handleResetFilters}
                resultsCount={searchMeta.total}
              />
            </aside>

            <div className="results-pane">
              <div className="project-list-header">
                <ProjectListHeader
                  filters={filters}
                  onFiltersChange={handleFiltersChange}
                  total={searchMeta.total}
                />
              </div>

              <div className="results-grid">
                <div className="list-column">
                  {searchLoading && <div className="loading-state">Loading projects...</div>}
                  {searchResults.map((p) => (
                    <div key={p.project_id} className="animate-slide-up">
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
                  {searchResults.length === 0 && !searchLoading && (
                    <div className="empty-state">
                      No projects found matching your criteria.
                    </div>
                  )}

                  <div className="pagination-controls">
                    <button
                      className="action-btn secondary"
                      disabled={searchMeta.page <= 1}
                      onClick={() => handlePageChange(searchMeta.page - 1)}
                    >
                      Previous
                    </button>
                    <span>
                      Page {searchMeta.page} of {Math.ceil(searchMeta.total / searchMeta.pageSize)}
                    </span>
                    <button
                      className="action-btn secondary"
                      disabled={searchMeta.page * searchMeta.pageSize >= searchMeta.total}
                      onClick={() => handlePageChange(searchMeta.page + 1)}
                    >
                      Next
                    </button>
                  </div>
                </div>

                <div className="map-column">
                  <div className="sticky-map">
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
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

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
        <div className="container banner banner-error" style={{ position: 'fixed', bottom: '20px', left: '50%', transform: 'translateX(-50%)', zIndex: 2000 }}>
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
    </div>
  );
}

export default App;
