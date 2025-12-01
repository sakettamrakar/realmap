import { useEffect, useMemo, useRef } from "react";
import classNames from "classnames";
import {
  MapContainer,
  Marker,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import L, { LatLngBounds } from "leaflet";
import SectionHeader from "./SectionHeader";
import ScoreBadge from "./ScoreBadge";
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
  // Normalize if 0-1
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
    const classes = classNames("map-pin-marker", {
      "pin-selected": options.isSelected,
      "pin-hovered": options.isHovered,
      "pin-pill": isPill,
      [`pin-${bucket}`]: !isPill && bucket,
    });

    const html = isPill
      ? `<div class="${classes}"><span>${priceText}</span></div>`
      : `<div class="${classes}"></div>`;

    icon = L.divIcon({
      className: "custom-div-icon",
      html: html,
      iconSize: isPill ? [60, 28] : [14, 14],
      iconAnchor: isPill ? [30, 28] : [7, 7],
    });
    iconCache.set(cacheKey, icon);
  }
  return icon;
};

const createClusterIcon = (cluster: any) => {
  const count = cluster.getChildCount();
  const size = count < 10 ? 32 : count < 50 ? 38 : 46;

  return L.divIcon({
    html: `<div><span>${count}</span></div>`,
    className: "cluster-icon",
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

        // Bring selected/hovered pins to front
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
          >
            {/* Tooltip removed as price is now visible */}
          </Marker>
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
    <div className="map-panel">
      <SectionHeader
        eyebrow="Map View"
        title="Projects by location"
        subtitle="Click a pin to view details"
        actions={loading && <div className="pill pill-muted">Loading…</div>}
      />
      <div className="map-card">
        <MapContainer
          center={mapCenter}
          zoom={7}
          bounds={bounds}
          className="map"
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
        <div className="map-legend">
          <div className="legend-row">
            <span className="legend-title">Score</span>
            <div className="legend-items">
              <ScoreBadge score={0.8} />
              <ScoreBadge score={0.6} />
              <ScoreBadge score={0.4} />
              <ScoreBadge score={0.2} />
            </div>
          </div>
          <div className="legend-row">
            <span className="legend-title">Location quality</span>
            <div className="legend-quality">
              <span className="legend-pin legend-pin-exact" aria-hidden="true" />
              <span>● Exact location</span>
            </div>
            <div className="legend-quality">
              <span className="legend-pin legend-pin-approx" aria-hidden="true" />
              <span>○ Approximate location</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectMapView;
