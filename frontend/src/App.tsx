import { useEffect, useMemo, useState } from "react";
import { searchProjects, getProject, getProjectsForMap } from "./api/projectsApi";
import ProjectSearchPanel from "./components/ProjectSearchPanel";
import ProjectMapView from "./components/ProjectMapView";
import ProjectDetailPanel from "./components/ProjectDetailPanel";
import ShortlistPanel from "./components/ShortlistPanel";
import CompareModal from "./components/CompareModal";
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

  const [error, setError] = useState<string | null>(null);

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

  const shortlistIds = useMemo(() => shortlist.map((item) => item.project_id), [shortlist]);

  const toggleShortlist = (project: ProjectSummary, isShortlisted: boolean) => {
    setShortlist((prev) => {
      if (isShortlisted) {
        return prev.filter((item) => item.project_id !== project.project_id);
      }
      const existing = prev.find((item) => item.project_id === project.project_id);
      if (existing) return prev;
      return [...prev, project];
    });
  };

  const toggleCompareSelection = (projectId: number) => {
    setCompareWarning(null);
    setCompareSelection((prev) => {
      if (prev.includes(projectId)) {
        return prev.filter((id) => id !== projectId);
      }
      if (prev.length >= 3) {
        setCompareWarning("You can compare up to 3 projects at a time.");
        return prev;
      }
      return [...prev, projectId];
    });
  };

  const handleOpenCompare = async () => {
    if (compareSelection.length < 2) return;
    setCompareOpen(true);
    setCompareLoading(true);
    setCompareError(null);
    try {
      const details = await Promise.all(compareSelection.map((id) => getProject(id)));
      setCompareProjects(details.filter((item): item is ProjectDetail => Boolean(item)));
    } catch (err: any) {
      setCompareError(err?.message || "Unable to load projects to compare.");
    } finally {
      setCompareLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setSearchLoading(true);
      try {
        const data = await searchProjects({
          district: debouncedFilters.district || undefined,
          min_overall_score: debouncedFilters.minOverallScore || undefined,
          min_price: debouncedFilters.minPrice || undefined,
          max_price: debouncedFilters.maxPrice || undefined,
          q: debouncedFilters.nameQuery || undefined,
          sort_by: debouncedFilters.sortBy,
          sort_dir: debouncedFilters.sortDir,
          page: searchMeta.page,
          page_size: PAGE_SIZE,
        });
        if (cancelled) return;
        setSearchResults(data.items);
        setSearchMeta({
          total: data.total,
          page: data.page,
          pageSize: data.page_size ?? PAGE_SIZE,
        });
        setError(null);
      } catch (err: any) {
        if (cancelled) return;
        setError(err?.message || "Unable to load projects.");
        setSearchResults([]);
      } finally {
        if (!cancelled) setSearchLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [debouncedFilters, searchMeta.page]);

  useEffect(() => {
    if (!mapBounds) return;
    let cancelled = false;
    const load = async () => {
      setMapLoading(true);
      try {
        const data = await getProjectsForMap({
          bbox: mapBounds,
          min_overall_score: debouncedFilters.minOverallScore || undefined,
        });
        if (cancelled) return;
        setMapPins(data.items);
      } catch (err: any) {
        if (cancelled) return;
        setError(err?.message || "Unable to load map pins.");
      } finally {
        if (!cancelled) setMapLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [mapBounds, debouncedFilters.minOverallScore]);

  useEffect(() => {
    if (!selectedProjectId) {
      setSelectedProject(null);
      return;
    }
    let cancelled = false;
    const load = async () => {
      setDetailLoading(true);
      try {
        const data = await getProject(selectedProjectId);
        if (cancelled) return;
        setSelectedProject(data);
        setError(null);
      } catch (err: any) {
        if (cancelled) return;
        setSelectedProject(null);
        setError(err?.message || "Unable to load project details.");
      } finally {
        if (!cancelled) setDetailLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [selectedProjectId]);

  return (
    <div className="app">
      <header className="app-header">
        <div className="container header-content">
          <div>
            <p className="eyebrow text-on-dark">CG RERA Explorer</p>
            <h1>Projects • Scores • Location</h1>
            <p className="muted text-on-dark">
              Internal view of registered projects with quality scores and map context.
            </p>
          </div>
          <div className="header-actions">
            <div className="header-pill">Data refreshed daily</div>
            <button className="pill" onClick={() => setIsShortlistOpen(true)} type="button">
              Shortlist ({shortlist.length})
            </button>
          </div>
        </div>
      </header>

      {error && <div className="banner banner-error container">{error}</div>}

      <main className="app-main container">
        <div className="layout-grid">
          <section className="pane pane-left">
            <ProjectSearchPanel
              filters={filters}
              onFiltersChange={handleFiltersChange}
              projects={searchResults}
              loading={searchLoading}
              onSelectProject={setSelectedProjectId}
              onHoverProject={setHoveredProjectId}
              selectedProjectId={selectedProjectId}
              hoveredProjectId={hoveredProjectId}
              total={searchMeta.total}
              page={searchMeta.page}
              pageSize={searchMeta.pageSize}
              onPageChange={handlePageChange}
              onResetFilters={handleResetFilters}
              defaultFilters={DEFAULT_FILTERS}
              shortlistIds={shortlistIds}
              onToggleShortlist={toggleShortlist}
            />
          </section>

          <section className="pane pane-right">
            <div className="map-wrapper">
              <ProjectMapView
                pins={mapPins}
                selectedProjectId={selectedProjectId}
                onSelectProject={setSelectedProjectId}
                hoveredProjectId={hoveredProjectId}
                onHoverProject={setHoveredProjectId}
                onBoundsChange={setMapBounds}
                loading={mapLoading}
                initialBounds={DEFAULT_BOUNDS}
                focus={mapFocus}
              />
              <ProjectDetailPanel
                project={selectedProject}
                loading={detailLoading}
                onClose={() => setSelectedProjectId(null)}
                onCenterOnProject={(coords) => setMapFocus({ ...coords, zoom: 15, timestamp: Date.now() })}
              />
            </div>
          </section>
        </div>
      </main>

      <ShortlistPanel
        open={isShortlistOpen}
        shortlist={shortlist}
        onClose={() => setIsShortlistOpen(false)}
        onSelectProject={(id) => {
          setSelectedProjectId(id);
          setIsShortlistOpen(false);
        }}
        onRemove={(id) => {
          const project = shortlist.find((item) => item.project_id === id);
          if (project) {
            toggleShortlist(project, true);
          }
        }}
        compareSelection={compareSelection}
        onToggleCompareSelection={toggleCompareSelection}
        onOpenCompare={handleOpenCompare}
        warning={compareWarning}
      />

      <CompareModal
        open={compareOpen}
        projects={compareProjects}
        loading={compareLoading}
        onClose={() => setCompareOpen(false)}
        selectionCount={compareSelection.length}
      />

      {compareError && <div className="banner banner-error container">{compareError}</div>}
    </div>
  );
}

export default App;
