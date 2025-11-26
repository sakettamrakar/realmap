import { MapContainer, TileLayer, Marker } from 'react-leaflet';
import L from 'leaflet';
import type { ProjectDetail } from "../../types/projects";

interface Props {
    location: ProjectDetail["location"];
    amenities: ProjectDetail["amenities"];
}

export function LocationSection({ location, amenities }: Props) {
    const nearby = amenities?.nearby_summary || {};
    const hasLocation = location?.lat && location?.lon;

    const icon = L.divIcon({
        className: "map-pin pin-medium",
        iconSize: [18, 18],
    });

    return (
        <div className="detail-section">
            <h3 className="section-title">Location Context</h3>

            {hasLocation && (
                <div className="location-map-container" style={{ height: '240px', marginBottom: '16px', borderRadius: '8px', overflow: 'hidden', border: '1px solid #e2e8f0' }}>
                    <MapContainer
                        center={[location.lat!, location.lon!]}
                        zoom={14}
                        style={{ height: '100%', width: '100%' }}
                        scrollWheelZoom={false}
                        dragging={false} // Disable dragging to prevent interfering with scroll
                        zoomControl={false} // Cleaner look
                    >
                        <TileLayer
                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        />
                        <Marker position={[location.lat!, location.lon!]} icon={icon} />
                    </MapContainer>
                </div>
            )}

            {location?.address && <p className="location-address" style={{ fontSize: '14px', color: '#64748b', marginBottom: '16px' }}>{location.address}</p>}

            <div className="location-stats-grid">
                {Object.entries(nearby).map(([type, stats]) => (
                    <div key={type} className="location-stat-card">
                        <div className="stat-header">
                            <span className="stat-type">{type.replace(/_/g, ' ')}</span>
                            <span className="stat-count">{stats.count}</span>
                        </div>
                        <div className="stat-detail">
                            within {stats.avg_distance_km?.toFixed(1)} km
                        </div>
                    </div>
                ))}

                {Object.keys(nearby).length === 0 && (
                    <p className="muted" style={{ fontSize: '13px', color: '#94a3b8', fontStyle: 'italic' }}>No nearby places data available.</p>
                )}
            </div>
        </div>
    );
}
