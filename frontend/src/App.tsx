import { useEffect, useState } from "react";
import { searchProjects, getProject, getProjectsForMap } from "./api/projectsApi";
import ProjectSearchPanel from "./components/ProjectSearchPanel";
import ProjectMapView from "./components/ProjectMapView";
import ProjectDetailPanel from "./components/ProjectDetailPanel";
import useDebouncedValue from "./hooks/useDebouncedValue";
import type { Filters } from "./types/filters";
import type { BBox, ProjectDetail, ProjectMapPin, ProjectSummary } from "./types/projects";

const DEFAULT_FILTERS: Filters = {
  district: "",
  minOverallScore: 0,
  nameQuery: "",
};

const DEFAULT_BOUNDS: BBox = {
  minLat: 17.5,
  minLon: 80.0,
  maxLat: 24.5,
  maxLon: 84.5,
};

function App() {
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const debouncedFilters = useDebouncedValue(filters, 300);
  const [searchResults, setSearchResults] = useState<ProjectSummary[]>([]);
  const [searchMeta, setSearchMeta] = useState<{ total: number; page: number }>(
    { total: 0, page: 1 },
  );
  const [searchLoading, setSearchLoading] = useState(false);

  const [mapPins, setMapPins] = useState<ProjectMapPin[]>([]);
  const [mapBounds, setMapBounds] = useState<BBox | null>(DEFAULT_BOUNDS);
  const [mapLoading, setMapLoading] = useState(false);

  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [selectedProject, setSelectedProject] = useState<ProjectDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const handleFiltersChange = (next: Partial<Filters>) =>
    setFilters((prev) => ({ ...prev, ...next }));

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setSearchLoading(true);
      try {
        const data = await searchProjects({
          district: debouncedFilters.district || undefined,
          min_overall_score: debouncedFilters.minOverallScore || undefined,
          name_contains: debouncedFilters.nameQuery || undefined,
          page: 1,
          page_size: 50,
        });
        if (cancelled) return;
        setSearchResults(data.items);
        setSearchMeta({ total: data.total, page: data.page });
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
  }, [debouncedFilters]);

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
        <div>
          <p className="eyebrow">CG RERA Explorer</p>
          <h1>Projects overview</h1>
        </div>
        <div className="pill pill-muted">Phase 6 backend live</div>
      </header>

      {error && <div className="banner banner-error">{error}</div>}

      <main className="layout">
        <section className="column column-left">
          <ProjectSearchPanel
            filters={filters}
            onFiltersChange={handleFiltersChange}
            projects={searchResults}
            loading={searchLoading}
            onSelectProject={setSelectedProjectId}
            selectedProjectId={selectedProjectId}
            total={searchMeta.total}
          />
        </section>

        <section className="column column-right">
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
      </main>
    </div>
  );
}

export default App;
