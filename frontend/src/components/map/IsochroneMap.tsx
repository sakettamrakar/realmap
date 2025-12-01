/**
 * IsochroneMap Component (Point 22)
 * 
 * Interactive intelligence map with:
 * - Isochrone overlays showing travel time polygons (15-min drive time)
 * - POI List sidebar with social_infrastructure
 * - Distance lines on hover
 * - Layer toggles for different POI categories
 * 
 * Built on top of react-leaflet for the existing map infrastructure.
 */

import React, { useState, useCallback, useMemo } from 'react';
import { 
  MapContainer, 
  TileLayer, 
  Marker, 
  Popup, 
  Polygon, 
  Polyline,
  useMap 
} from 'react-leaflet';
import L from 'leaflet';
import './IsochroneMap.css';

// ====================
// Types
// ====================

export interface GeoCoordinate {
  lat: number;
  lng: number;
}

export interface IsochronePolygon {
  /** Travel time in minutes */
  time_minutes: number;
  /** Polygon coordinates */
  coordinates: GeoCoordinate[];
  /** Travel mode */
  mode: 'drive' | 'walk' | 'transit';
  /** Color for display */
  color?: string;
}

export interface PointOfInterest {
  /** Unique ID */
  id: string;
  /** POI name */
  name: string;
  /** Category */
  category: POICategory;
  /** Location */
  coordinates: GeoCoordinate;
  /** Distance from project in meters */
  distance_meters: number;
  /** Travel time in minutes (by default mode) */
  travel_time_minutes?: number;
  /** Sub-category for more specific classification */
  subcategory?: string;
  /** Rating (if available) */
  rating?: number;
  /** Additional metadata */
  metadata?: Record<string, string | number>;
}

export type POICategory = 
  | 'school'
  | 'hospital'
  | 'metro'
  | 'mall'
  | 'park'
  | 'temple'
  | 'bank'
  | 'restaurant'
  | 'grocery'
  | 'other';

export interface IsochroneMapProps {
  /** Project location (center point) */
  projectLocation: GeoCoordinate;
  /** Project name for display */
  projectName: string;
  /** Isochrone polygons to display */
  isochrones?: IsochronePolygon[];
  /** Points of interest */
  pois: PointOfInterest[];
  /** Initial zoom level */
  initialZoom?: number;
  /** Map height */
  height?: string;
  /** Callback when POI is selected */
  onPOISelect?: (poi: PointOfInterest) => void;
  /** Show isochrone controls */
  showIsochroneControls?: boolean;
  /** Show POI sidebar */
  showPOISidebar?: boolean;
}

// ====================
// Constants
// ====================

const POI_CATEGORY_CONFIG: Record<POICategory, {
  label: string;
  icon: string;
  color: string;
}> = {
  school: { label: 'Schools', icon: '🏫', color: '#3b82f6' },
  hospital: { label: 'Healthcare', icon: '🏥', color: '#ef4444' },
  metro: { label: 'Metro Stations', icon: '🚇', color: '#8b5cf6' },
  mall: { label: 'Shopping', icon: '🛒', color: '#f59e0b' },
  park: { label: 'Parks', icon: '🌳', color: '#22c55e' },
  temple: { label: 'Places of Worship', icon: '🛕', color: '#ec4899' },
  bank: { label: 'Banks & ATMs', icon: '🏦', color: '#06b6d4' },
  restaurant: { label: 'Restaurants', icon: '🍽️', color: '#f97316' },
  grocery: { label: 'Grocery', icon: '🛍️', color: '#84cc16' },
  other: { label: 'Other', icon: '📍', color: '#6b7280' },
};

const ISOCHRONE_COLORS: Record<number, string> = {
  5: '#22c55e',   // 5 min - green
  10: '#84cc16',  // 10 min - lime
  15: '#eab308',  // 15 min - yellow
  20: '#f97316',  // 20 min - orange
  30: '#ef4444',  // 30 min - red
};

// ====================
// Utility Functions
// ====================

/**
 * Format distance for display
 */
export function formatDistance(meters: number): string {
  if (meters < 1000) {
    return `${Math.round(meters)} m`;
  }
  return `${(meters / 1000).toFixed(1)} km`;
}

/**
 * Format travel time
 */
export function formatTravelTime(minutes?: number): string {
  if (!minutes) return '';
  if (minutes < 60) {
    return `${Math.round(minutes)} min`;
  }
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  return `${hours}h ${mins}m`;
}

/**
 * Create custom marker icon
 */
function createPOIIcon(category: POICategory): L.DivIcon {
  const config = POI_CATEGORY_CONFIG[category];
  return L.divIcon({
    className: 'poi-marker',
    html: `<div class="poi-marker-inner" style="background: ${config.color}">${config.icon}</div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
  });
}

/**
 * Create project marker icon
 */
function createProjectIcon(): L.DivIcon {
  return L.divIcon({
    className: 'project-marker',
    html: `<div class="project-marker-inner">🏠</div>`,
    iconSize: [40, 40],
    iconAnchor: [20, 40],
  });
}

// ====================
// Sub-Components
// ====================

interface POISidebarProps {
  pois: PointOfInterest[];
  activePOI: string | null;
  enabledCategories: Set<POICategory>;
  onPOIHover: (poi: PointOfInterest | null) => void;
  onPOIClick: (poi: PointOfInterest) => void;
  onCategoryToggle: (category: POICategory) => void;
}

/**
 * Sidebar listing POIs by category
 */
function POISidebar({
  pois,
  activePOI,
  enabledCategories,
  onPOIHover,
  onPOIClick,
  onCategoryToggle,
}: POISidebarProps) {
  // Group POIs by category
  const poisByCategory = useMemo(() => {
    const grouped: Record<POICategory, PointOfInterest[]> = {} as Record<POICategory, PointOfInterest[]>;
    for (const category of Object.keys(POI_CATEGORY_CONFIG) as POICategory[]) {
      grouped[category] = [];
    }
    for (const poi of pois) {
      if (!grouped[poi.category]) {
        grouped[poi.category] = [];
      }
      grouped[poi.category].push(poi);
    }
    // Sort by distance within each category
    for (const category of Object.keys(grouped) as POICategory[]) {
      grouped[category].sort((a, b) => a.distance_meters - b.distance_meters);
    }
    return grouped;
  }, [pois]);

  return (
    <div className="poi-sidebar">
      <div className="sidebar-header">
        <h4>📍 Nearby Places</h4>
        <span className="poi-count">{pois.length} found</span>
      </div>

      <div className="category-filters">
        {(Object.keys(POI_CATEGORY_CONFIG) as POICategory[]).map(category => {
          const config = POI_CATEGORY_CONFIG[category];
          const count = poisByCategory[category]?.length || 0;
          if (count === 0) return null;
          
          return (
            <button
              key={category}
              className={`category-filter ${enabledCategories.has(category) ? 'active' : ''}`}
              onClick={() => onCategoryToggle(category)}
              style={{ '--category-color': config.color } as React.CSSProperties}
            >
              <span className="filter-icon">{config.icon}</span>
              <span className="filter-label">{config.label}</span>
              <span className="filter-count">{count}</span>
            </button>
          );
        })}
      </div>

      <div className="poi-list">
        {(Object.keys(POI_CATEGORY_CONFIG) as POICategory[]).map(category => {
          const categoryPois = poisByCategory[category];
          if (!categoryPois?.length || !enabledCategories.has(category)) return null;
          
          const config = POI_CATEGORY_CONFIG[category];
          
          return (
            <div key={category} className="poi-category-group">
              <div className="category-header">
                <span className="category-icon">{config.icon}</span>
                <span className="category-name">{config.label}</span>
              </div>
              <ul className="poi-items">
                {categoryPois.slice(0, 5).map(poi => (
                  <li
                    key={poi.id}
                    className={`poi-item ${activePOI === poi.id ? 'active' : ''}`}
                    onMouseEnter={() => onPOIHover(poi)}
                    onMouseLeave={() => onPOIHover(null)}
                    onClick={() => onPOIClick(poi)}
                  >
                    <div className="poi-name">{poi.name}</div>
                    <div className="poi-details">
                      <span className="poi-distance">{formatDistance(poi.distance_meters)}</span>
                      {poi.travel_time_minutes && (
                        <span className="poi-time">• {formatTravelTime(poi.travel_time_minutes)}</span>
                      )}
                      {poi.rating && (
                        <span className="poi-rating">★ {poi.rating.toFixed(1)}</span>
                      )}
                    </div>
                  </li>
                ))}
                {categoryPois.length > 5 && (
                  <li className="poi-more">
                    +{categoryPois.length - 5} more
                  </li>
                )}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface IsochroneControlsProps {
  availableTimes: number[];
  enabledTimes: Set<number>;
  mode: 'drive' | 'walk' | 'transit';
  onTimeToggle: (time: number) => void;
  onModeChange: (mode: 'drive' | 'walk' | 'transit') => void;
}

/**
 * Controls for isochrone display
 */
function IsochroneControls({
  availableTimes,
  enabledTimes,
  mode,
  onTimeToggle,
  onModeChange,
}: IsochroneControlsProps) {
  return (
    <div className="isochrone-controls">
      <div className="control-group">
        <label>Travel Mode</label>
        <div className="mode-buttons">
          <button
            className={mode === 'drive' ? 'active' : ''}
            onClick={() => onModeChange('drive')}
          >
            🚗 Drive
          </button>
          <button
            className={mode === 'walk' ? 'active' : ''}
            onClick={() => onModeChange('walk')}
          >
            🚶 Walk
          </button>
          <button
            className={mode === 'transit' ? 'active' : ''}
            onClick={() => onModeChange('transit')}
          >
            🚇 Transit
          </button>
        </div>
      </div>

      <div className="control-group">
        <label>Travel Time</label>
        <div className="time-toggles">
          {availableTimes.map(time => (
            <button
              key={time}
              className={`time-toggle ${enabledTimes.has(time) ? 'active' : ''}`}
              onClick={() => onTimeToggle(time)}
              style={{ 
                '--time-color': ISOCHRONE_COLORS[time] || '#6b7280' 
              } as React.CSSProperties}
            >
              {time} min
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

interface MapEventsHandlerProps {
  activePOI: PointOfInterest | null;
  projectLocation: GeoCoordinate;
}

/**
 * Component to handle map events and fly to POI
 */
function MapEventsHandler({ activePOI, projectLocation }: MapEventsHandlerProps) {
  const map = useMap();

  React.useEffect(() => {
    if (activePOI) {
      // Calculate bounds to include both project and POI
      const bounds = L.latLngBounds(
        [projectLocation.lat, projectLocation.lng],
        [activePOI.coordinates.lat, activePOI.coordinates.lng]
      );
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 16 });
    }
  }, [activePOI, projectLocation, map]);

  return null;
}

// ====================
// Main Component
// ====================

export function IsochroneMap({
  projectLocation,
  projectName,
  isochrones = [],
  pois,
  initialZoom = 14,
  height = '500px',
  onPOISelect,
  showIsochroneControls = true,
  showPOISidebar = true,
}: IsochroneMapProps) {
  // State
  const [hoveredPOI, setHoveredPOI] = useState<PointOfInterest | null>(null);
  const [selectedPOI, setSelectedPOI] = useState<PointOfInterest | null>(null);
  const [enabledCategories, setEnabledCategories] = useState<Set<POICategory>>(
    new Set(Object.keys(POI_CATEGORY_CONFIG) as POICategory[])
  );
  const [enabledTimes, setEnabledTimes] = useState<Set<number>>(new Set([15]));
  const [travelMode, setTravelMode] = useState<'drive' | 'walk' | 'transit'>('drive');

  // Memoized values
  const projectIcon = useMemo(() => createProjectIcon(), []);
  
  const availableTimes = useMemo(
    () => [...new Set(isochrones.map(i => i.time_minutes))].sort((a, b) => a - b),
    [isochrones]
  );

  const visibleIsochrones = useMemo(
    () => isochrones.filter(i => enabledTimes.has(i.time_minutes) && i.mode === travelMode),
    [isochrones, enabledTimes, travelMode]
  );

  const visiblePOIs = useMemo(
    () => pois.filter(poi => enabledCategories.has(poi.category)),
    [pois, enabledCategories]
  );

  // Handlers
  const handleCategoryToggle = useCallback((category: POICategory) => {
    setEnabledCategories(prev => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  }, []);

  const handleTimeToggle = useCallback((time: number) => {
    setEnabledTimes(prev => {
      const next = new Set(prev);
      if (next.has(time)) {
        next.delete(time);
      } else {
        next.add(time);
      }
      return next;
    });
  }, []);

  const handlePOIHover = useCallback((poi: PointOfInterest | null) => {
    setHoveredPOI(poi);
  }, []);

  const handlePOIClick = useCallback((poi: PointOfInterest) => {
    setSelectedPOI(poi);
    onPOISelect?.(poi);
  }, [onPOISelect]);

  const activePOI = hoveredPOI || selectedPOI;

  return (
    <div className="isochrone-map-container" style={{ height }}>
      {showIsochroneControls && availableTimes.length > 0 && (
        <IsochroneControls
          availableTimes={availableTimes}
          enabledTimes={enabledTimes}
          mode={travelMode}
          onTimeToggle={handleTimeToggle}
          onModeChange={setTravelMode}
        />
      )}

      <div className="map-wrapper">
        <MapContainer
          center={[projectLocation.lat, projectLocation.lng]}
          zoom={initialZoom}
          style={{ height: '100%', width: '100%' }}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapEventsHandler 
            activePOI={activePOI} 
            projectLocation={projectLocation} 
          />

          {/* Isochrone polygons */}
          {visibleIsochrones.map((isochrone, index) => (
            <Polygon
              key={`isochrone-${isochrone.time_minutes}-${index}`}
              positions={isochrone.coordinates.map(c => [c.lat, c.lng])}
              pathOptions={{
                color: isochrone.color || ISOCHRONE_COLORS[isochrone.time_minutes] || '#6b7280',
                fillColor: isochrone.color || ISOCHRONE_COLORS[isochrone.time_minutes] || '#6b7280',
                fillOpacity: 0.15,
                weight: 2,
              }}
            />
          ))}

          {/* Distance line to active POI */}
          {activePOI && (
            <Polyline
              positions={[
                [projectLocation.lat, projectLocation.lng],
                [activePOI.coordinates.lat, activePOI.coordinates.lng],
              ]}
              pathOptions={{
                color: POI_CATEGORY_CONFIG[activePOI.category].color,
                weight: 3,
                dashArray: '10, 10',
              }}
            />
          )}

          {/* Project marker */}
          <Marker
            position={[projectLocation.lat, projectLocation.lng]}
            icon={projectIcon}
          >
            <Popup>
              <div className="project-popup">
                <strong>{projectName}</strong>
                <span>Project Location</span>
              </div>
            </Popup>
          </Marker>

          {/* POI markers */}
          {visiblePOIs.map(poi => (
            <Marker
              key={poi.id}
              position={[poi.coordinates.lat, poi.coordinates.lng]}
              icon={createPOIIcon(poi.category)}
              eventHandlers={{
                mouseover: () => handlePOIHover(poi),
                mouseout: () => handlePOIHover(null),
                click: () => handlePOIClick(poi),
              }}
            >
              <Popup>
                <div className="poi-popup">
                  <strong>{poi.name}</strong>
                  <span className="poi-category">
                    {POI_CATEGORY_CONFIG[poi.category].icon} {POI_CATEGORY_CONFIG[poi.category].label}
                  </span>
                  <span className="poi-distance-popup">
                    {formatDistance(poi.distance_meters)}
                    {poi.travel_time_minutes && ` • ${formatTravelTime(poi.travel_time_minutes)}`}
                  </span>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        {showPOISidebar && (
          <POISidebar
            pois={pois}
            activePOI={activePOI?.id || null}
            enabledCategories={enabledCategories}
            onPOIHover={handlePOIHover}
            onPOIClick={handlePOIClick}
            onCategoryToggle={handleCategoryToggle}
          />
        )}
      </div>

      {/* Distance info bar */}
      {activePOI && (
        <div className="distance-info-bar">
          <span className="distance-icon">
            {POI_CATEGORY_CONFIG[activePOI.category].icon}
          </span>
          <span className="distance-name">{activePOI.name}</span>
          <span className="distance-value">{formatDistance(activePOI.distance_meters)}</span>
          {activePOI.travel_time_minutes && (
            <span className="distance-time">
              🚗 {formatTravelTime(activePOI.travel_time_minutes)}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

// ====================
// Exports
// ====================

export { POI_CATEGORY_CONFIG, ISOCHRONE_COLORS };
export default IsochroneMap;
