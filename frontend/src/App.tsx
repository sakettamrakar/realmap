import { useEffect, useState } from "react";
import { searchProjects, getProject, getProjectsForMap } from "./api/projectsApi";
import ProjectSearchPanel from "./components/ProjectSearchPanel";
import ProjectMapView from "./components/ProjectMapView";
import ProjectDetailPanel from "./components/ProjectDetailPanel";
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

  const [page, setPage] = useState(1);

  const [mapPins, setMapPins] = useState<ProjectMapPin[]>([]);
  const [mapBounds, setMapBounds] = useState<BBox | null>(DEFAULT_BOUNDS);
  const [mapLoading, setMapLoading] = useState(false);

  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [selectedProject, setSelectedProject] = useState<ProjectDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const handleFiltersChange = (next: Partial<Filters>) => {
    setFilters((prev) => ({ ...prev, ...next }));
    setPage(1);
  };

  const handleResetFilters = () => {
    setFilters({ ...DEFAULT_FILTERS });
    setPage(1);
  };

  const handlePageChange = (nextPage: number) => {
    setPage(nextPage);
  };

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setSearchLoading(true);
      try {
        const data = await searchProjects({
          district: debouncedFilters.district || undefined,
          min_overall_score: debouncedFilters.minOverallScore || undefined,
          name_contains: debouncedFilters.nameQuery || undefined,
          q: debouncedFilters.nameQuery || undefined,
          sort_by: debouncedFilters.sortBy,
          sort_dir: debouncedFilters.sortDir,
          page,
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
  }, [debouncedFilters, page]);

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
          <div className="header-pill">Data refreshed daily</div>
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
              selectedProjectId={selectedProjectId}
              total={searchMeta.total}
              page={searchMeta.page}
              pageSize={searchMeta.pageSize}
              onPageChange={handlePageChange}
              onResetFilters={handleResetFilters}
              defaultFilters={DEFAULT_FILTERS}
            />
          </section>

          <section className="pane pane-right">
            <div className="map-wrapper">
              <ProjectMapView
                pins={mapPins}
                selectedProjectId={selectedProjectId}
                onSelectProject={setSelectedProjectId}
                onBoundsChange={setMapBounds}
                loading={mapLoading}
                initialBounds={DEFAULT_BOUNDS}
              />
              <ProjectDetailPanel
                project={selectedProject}
                loading={detailLoading}
                onClose={() => setSelectedProjectId(null)}
              />
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

export default App;
