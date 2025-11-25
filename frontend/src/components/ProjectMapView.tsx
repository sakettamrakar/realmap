import { useEffect, useMemo, useRef } from "react";
import {
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";
import L, { LatLngBounds } from "leaflet";
import SectionHeader from "./SectionHeader";
import ScoreBadge from "./ScoreBadge";
import type { BBox, ProjectMapPin } from "../types/projects";

interface Props {
  pins: ProjectMapPin[];
  selectedProjectId: number | null;
  onSelectProject: (projectId: number) => void;
  onBoundsChange: (bbox: BBox) => void;
  loading?: boolean;
  initialBounds: BBox;
  focus?: { lat: number; lon: number; zoom?: number } | null;
}

const scoreBucket = (score?: number) => {
  if (score === undefined || score === null) return "unknown";
  if (score >= 0.75) return "high";
  if (score >= 0.5) return "medium";
  return "low";
};

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

const createIcon = (bucket: string, isSelected: boolean) =>
  L.divIcon({
    className: `map-pin pin-${bucket} ${isSelected ? "pin-selected" : ""}`,
    iconSize: [16, 16],
  });

const PinsLayer = ({
  pins,
  onSelectProject,
  selectedProjectId,
}: {
  pins: ProjectMapPin[];
  onSelectProject: (projectId: number) => void;
  selectedProjectId: number | null;
}) => {
  const map = useMap();
  const hasFit = useRef(false);

  useEffect(() => {
    hasFit.current = false;
  }, [pins.length]);

  useEffect(() => {
    if (pins.length === 0 || hasFit.current) return;
    const bounds = L.latLngBounds(pins.map((pin) => [pin.lat, pin.lon]));
    map.fitBounds(bounds, { padding: [24, 24] });
    hasFit.current = true;
  }, [pins, map]);

  return (
    <>
      {pins.map((pin) => {
        const bucket = scoreBucket(pin.overall_score);
        const icon = createIcon(bucket, selectedProjectId === pin.project_id);
        return (
          <Marker
            key={pin.project_id}
            position={[pin.lat, pin.lon]}
            icon={icon}
            eventHandlers={{
              click: () => onSelectProject(pin.project_id),
            }}
          >
            <Popup>
              <div className="popup">
                <strong>{pin.name}</strong>
                <div className="eyebrow">
                  Score: {pin.overall_score != null ? pin.overall_score.toFixed(2) : "—"}
                </div>
              </div>
            </Popup>
          </Marker>
        );
      })}
    </>
  );
};

const RecenterOnFocus = ({ focus }: { focus?: { lat: number; lon: number; zoom?: number } | null }) => {
  const map = useMap();

  useEffect(() => {
    if (!focus) return;
    map.flyTo([focus.lat, focus.lon], focus.zoom ?? Math.max(map.getZoom(), 14));
  }, [focus, map]);

  return null;
};

const ProjectMapView = ({
  pins,
  selectedProjectId,
  onSelectProject,
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
          />
        </MapContainer>
        <div className="map-legend">
          <span className="legend-title">Score Legend</span>
          <div className="legend-items">
            <ScoreBadge score={0.8} />
            <ScoreBadge score={0.6} />
            <ScoreBadge score={0.3} />
            <ScoreBadge score={null} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectMapView;
