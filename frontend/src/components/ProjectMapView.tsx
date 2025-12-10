import { useEffect, useMemo, useRef } from "react";
import {
  MapContainer,
  Marker,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import L, { LatLngBounds } from "leaflet";
import type { BBox, ProjectMapPin } from "../types/projects";

interface Props {
  pins: ProjectMapPin[];
  selectedProjectId: number | null;
  hoveredProjectId: number | null;
  onSelectProject: (projectId: number) => void;
  onHoverProject: (projectId: number | null) => void;
  onBoundsChange: (bbox: BBox) => void;
  loading?: boolean;
  initialBounds: BBox;
  focus?: { lat: number; lon: number; zoom?: number; timestamp?: number } | null;
}

const scoreBucket = (score?: number) => {
  if (score === undefined || score === null) return "unknown";
  const val = score <= 1 ? score * 10 : score > 10 ? score / 10 : score;

  if (val >= 8) return "excellent";
  if (val >= 6) return "good";
  if (val >= 4) return "average";
  return "weak";
};

const isExactLocation = (pin: ProjectMapPin) =>
  pin.geo_precision === "exact" || pin.geo_source === "rera_pin";

const toBBox = (bounds: LatLngBounds): BBox => {
  const southWest = bounds.getSouthWest();
  const northEast = bounds.getNorthEast();
  return {
    minLat: southWest.lat,
    minLon: southWest.lng,
    maxLat: northEast.lat,
    maxLon: northEast.lng,
  };
};

const MapEvents = ({ onBoundsChange }: { onBoundsChange: (bbox: BBox) => void }) => {
  const map = useMapEvents({
    moveend: () => onBoundsChange(toBBox(map.getBounds())),
    zoomend: () => onBoundsChange(toBBox(map.getBounds())),
  });

  useEffect(() => {
    onBoundsChange(toBBox(map.getBounds()));
  }, [map, onBoundsChange]);

  return null;
};

// Icon cache for performance - avoids creating new icons on every render
const iconCache = new Map<string, L.DivIcon>();

const formatPrice = (price?: number) => {
  if (!price) return null;
  if (price >= 10000000) return `₹${(price / 10000000).toFixed(1)}Cr`;
  if (price >= 100000) return `₹${(price / 100000).toFixed(1)}L`;
  return `₹${price.toLocaleString()}`;
};

const getIcon = (
  bucket: string,
  price: number | undefined,
  options: { precision: "exact" | "approximate"; isSelected: boolean; isHovered: boolean },
): L.DivIcon => {
  const priceText = formatPrice(price);
  const isPill = !!priceText;

  const cacheKey = `${bucket}-${options.precision}-${options.isSelected}-${options.isHovered}-${priceText || 'noprice'}`;
  let icon = iconCache.get(cacheKey);

  if (!icon) {
    // Generate Tailwind colors for markers manually since Leaflet doesn't parse Tailwind classes from stringHTML
    let bgColor = "#64748b"; // slate-500 default
    let borderColor = "#cbd5e1"; // slate-300

    if (bucket === 'excellent') { bgColor = "#10b981"; borderColor = "#34d399"; } // emerald-500
    else if (bucket === 'good') { bgColor = "#0ea5e9"; borderColor = "#38bdf8"; } // sky-500
    else if (bucket === 'average') { bgColor = "#f97316"; borderColor = "#fb923c"; } // orange-500
    else if (bucket === 'weak') { bgColor = "#f43f5e"; borderColor = "#fb7185"; } // rose-500

    // Override for approximate
    if (options.precision === 'approximate') {
      borderColor = bgColor;
      bgColor = "#ffffff";
    }

    // Selected/Hovered state
    if (options.isSelected) { bgColor = "#0f172a"; borderColor = "#0f172a"; } // slate-900

    const style = `
      background-color: ${bgColor}; 
      border: 2px solid ${borderColor}; 
      color: ${options.precision === 'approximate' && !options.isSelected ? '#0f172a' : 'white'};
      ${options.isHovered ? 'transform: scale(1.1); box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);' : ''}
    `;

    const html = isPill
      ? `<div class="flex items-center justify-center rounded-full font-bold text-[11px] px-2 shadow-sm transition-transform" style="${style} min-width: 44px; height: 24px;">${priceText}</div>`
      : `<div class="rounded-full shadow-sm transition-transform" style="${style} width: 14px; height: 14px;"></div>`;

    icon = L.divIcon({
      className: "bg-transparent border-none", // Remove default leaflet styles
      html: html,
      iconSize: isPill ? [60, 24] : [14, 14],
      iconAnchor: isPill ? [30, 24] : [7, 7],
    });
    iconCache.set(cacheKey, icon);
  }
  return icon;
};

const createClusterIcon = (cluster: any) => {
  const count = cluster.getChildCount();
  const size = count < 10 ? 32 : count < 50 ? 38 : 46;

  return L.divIcon({
    html: `<div class="flex items-center justify-center bg-sky-500 text-white rounded-full border-2 border-white shadow-lg font-bold text-sm" style="width: ${size}px; height: ${size}px;">${count}</div>`,
    className: "bg-transparent border-none",
    iconSize: L.point(size, size, true),
  });
};

const PinsLayer = ({
  pins,
  onSelectProject,
  selectedProjectId,
  hoveredProjectId,
  onHoverProject,
  initialBounds,
}: {
  pins: ProjectMapPin[];
  onSelectProject: (projectId: number) => void;
  selectedProjectId: number | null;
  hoveredProjectId: number | null;
  onHoverProject: (projectId: number | null) => void;
  initialBounds: BBox;
}) => {
  const map = useMap();
  const hasFit = useRef(false);

  useEffect(() => {
    hasFit.current = false;
  }, [pins.length, initialBounds]);

  useEffect(() => {
    if (hasFit.current) return;
    if (pins.length === 0) {
      const defaultBounds = L.latLngBounds([
        [initialBounds.minLat, initialBounds.minLon],
        [initialBounds.maxLat, initialBounds.maxLon],
      ]);
      map.fitBounds(defaultBounds, { padding: [24, 24] });
      hasFit.current = true;
      return;
    }
    const bounds = L.latLngBounds(pins.map((pin) => [pin.lat, pin.lon]));
    map.fitBounds(bounds, { padding: [24, 24] });
    hasFit.current = true;
  }, [pins, map, initialBounds]);

  return (
    <MarkerClusterGroup
      chunkedLoading
      spiderfyOnMaxZoom
      showCoverageOnHover={false}
      iconCreateFunction={createClusterIcon}
    >
      {pins.map((pin) => {
        const bucket = scoreBucket(pin.overall_score);
        const precision = isExactLocation(pin) ? "exact" : "approximate";
        const icon = getIcon(bucket, pin.min_price_total, {
          precision,
          isSelected: selectedProjectId === pin.project_id,
          isHovered: hoveredProjectId === pin.project_id,
        });

        const zIndexOffset = (selectedProjectId === pin.project_id || hoveredProjectId === pin.project_id) ? 1000 : 0;

        return (
          <Marker
            key={pin.project_id}
            position={[pin.lat, pin.lon]}
            icon={icon}
            zIndexOffset={zIndexOffset}
            eventHandlers={{
              click: () => onSelectProject(pin.project_id),
              mouseover: () => onHoverProject(pin.project_id),
              mouseout: () => onHoverProject(null),
            }}
          />
        );
      })}
    </MarkerClusterGroup>
  );
};

const RecenterOnFocus = ({ focus }: { focus?: { lat: number; lon: number; zoom?: number; timestamp?: number } | null }) => {
  const map = useMap();
  const prevFocusRef = useRef<{ lat: number; lon: number; zoom?: number; timestamp?: number } | null>(null);

  useEffect(() => {
    if (
      !focus ||
      (
        prevFocusRef.current &&
        prevFocusRef.current.lat === focus.lat &&
        prevFocusRef.current.lon === focus.lon &&
        prevFocusRef.current.zoom === focus.zoom &&
        prevFocusRef.current.timestamp === focus.timestamp
      )
    ) {
      return;
    }
    map.flyTo([focus.lat, focus.lon], focus.zoom ?? Math.max(map.getZoom(), 14));
    prevFocusRef.current = focus;
  }, [focus?.lat, focus?.lon, focus?.zoom, focus?.timestamp, map]);

  return null;
};

const ProjectMapView = ({
  pins,
  selectedProjectId,
  hoveredProjectId,
  onSelectProject,
  onHoverProject,
  onBoundsChange,
  loading,
  initialBounds,
  focus,
}: Props) => {
  const mapCenter: [number, number] = [
    (initialBounds.maxLat + initialBounds.minLat) / 2,
    (initialBounds.maxLon + initialBounds.minLon) / 2,
  ];

  const bounds = useMemo(
    () =>
      L.latLngBounds([
        [initialBounds.minLat, initialBounds.minLon],
        [initialBounds.maxLat, initialBounds.maxLon],
      ]),
    [initialBounds],
  );

  return (
    <div className="h-full w-full flex flex-col relative bg-slate-100 rounded-2xl overflow-hidden">
      {/* Floating Header */}
      <div className="absolute top-4 left-4 right-4 z-[450] bg-white/90 backdrop-blur-sm rounded-xl p-3 shadow-md border border-slate-200">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="font-bold text-slate-900 text-sm">Map View</h3>
            <p className="text-xs text-slate-500">
              {pins.length} projects in view
            </p>
          </div>
          {loading && (
            <span className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded-full font-medium animate-pulse">
              Updating...
            </span>
          )}
        </div>
      </div>

      <MapContainer
        center={mapCenter}
        zoom={7}
        bounds={bounds}
        className="flex-1 w-full h-full z-0"
        scrollWheelZoom
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapEvents onBoundsChange={onBoundsChange} />
        <RecenterOnFocus focus={focus} />
        <PinsLayer
          pins={pins}
          onSelectProject={onSelectProject}
          selectedProjectId={selectedProjectId}
          hoveredProjectId={hoveredProjectId}
          onHoverProject={onHoverProject}
          initialBounds={initialBounds}
        />
      </MapContainer>

      {/* Legend */}
      <div className="absolute bottom-6 right-6 z-[450] bg-white/90 backdrop-blur-sm p-3 rounded-xl shadow-lg border border-slate-200 max-w-[200px]">
        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Score</h4>
        <div className="flex flex-wrap gap-2 mb-3">
          <div className="w-3 h-3 rounded-full bg-emerald-500 ring-2 ring-emerald-200" title="Excellent" />
          <div className="w-3 h-3 rounded-full bg-sky-500 ring-2 ring-sky-200" title="Good" />
          <div className="w-3 h-3 rounded-full bg-orange-500 ring-2 ring-orange-200" title="Average" />
          <div className="w-3 h-3 rounded-full bg-rose-500 ring-2 ring-rose-200" title="Weak" />
        </div>

        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Accuracy</h4>
        <div className="space-y-1.5 text-xs text-slate-700">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-slate-500 border-2 border-slate-300" />
            <span>Exact</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-white border-2 border-slate-500" />
            <span>Approximate</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectMapView;


