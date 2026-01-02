import { MapContainer, TileLayer, Marker } from 'react-leaflet';
import L from 'leaflet';
import { MapPin, School, Hospital, TreePine, Bus, ShoppingBag, Landmark, Coffee, Utensils, Dumbbell, Theater, Train } from "lucide-react";
import type { ProjectDetail } from "../../types/projects";

interface Props {
    location: ProjectDetail["location"];
    amenities: ProjectDetail["amenities"];
}

const CATEGORY_ICONS: Record<string, any> = {
    school: School,
    hospital: Hospital,
    park: TreePine,
    bus_station: Bus,
    metro_station: Train,
    market: ShoppingBag,
    bank: Landmark,
    atm: Landmark,
    pharmacy: Hospital,
    theatre: Theater,
    mall: ShoppingBag,
    restaurant: Utensils,
    cafe: Coffee,
    gym: Dumbbell,
};

export function LocationSection({ location, amenities }: Props) {
    const nearby = amenities?.nearby_summary || {};
    const hasLocation = location?.lat && location?.lon;

    const icon = L.divIcon({
        className: "map-pin pin-medium",
        iconSize: [18, 18],
    });

    return (
        <div className="detail-section location-section">
            <h3 className="section-title">
                <MapPin size={20} className="text-indigo-600" />
                Location Context
            </h3>

            {hasLocation && (
                <div className="location-map-container" style={{ height: '240px', marginBottom: '1.5rem', borderRadius: '1rem', overflow: 'hidden', border: '1px solid #e2e8f0', boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.05)' }}>
                    <MapContainer
                        center={[location.lat!, location.lon!]}
                        zoom={14}
                        style={{ height: '100%', width: '100%' }}
                        scrollWheelZoom={false}
                        dragging={false}
                        zoomControl={false}
                    >
                        <TileLayer
                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        />
                        <Marker position={[location.lat!, location.lon!]} icon={icon} />
                    </MapContainer>
                </div>
            )}

            {location?.address && (
                <div className="flex items-start gap-2 mb-6">
                    <MapPin size={16} className="mt-0.5 text-slate-400 flex-shrink-0" />
                    <p className="text-sm font-medium text-slate-600 leading-relaxed">{location.address}</p>
                </div>
            )}

            <div className="location-stats-grid">
                {Object.entries(nearby).map(([type, stats]) => {
                    const IconComponent = CATEGORY_ICONS[type.toLowerCase()] || MapPin;
                    return (
                        <div key={type} className="location-stat-card group hover:border-indigo-200 transition-all">
                            <div className="stat-header mb-1">
                                <span className="p-1.5 bg-slate-100 rounded-lg group-hover:bg-indigo-50 transition-colors">
                                    <IconComponent size={14} className="text-slate-500 group-hover:text-indigo-600" />
                                </span>
                                <span className="stat-count">{stats.count}</span>
                            </div>
                            <span className="stat-type truncate" title={type.replace(/_/g, ' ')}>
                                {type.replace(/_/g, ' ')}
                            </span>
                            <div className="stat-detail">
                                within {stats.avg_distance_km?.toFixed(1)} km
                            </div>
                        </div>
                    );
                })}

                {Object.keys(nearby).length === 0 && (
                    <div className="col-span-full py-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
                        <p className="text-sm text-slate-400 italic">No nearby places data available.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
