/**
 * Landmark Links Component (Point 26)
 * 
 * Displays nearby landmarks with distances.
 * Enables entity linking for SEO and navigation.
 */
import './LandmarkLinks.css';

export interface LandmarkWithDistance {
  id: number;
  slug: string;
  name: string;
  category: string;
  lat: number;
  lon: number;
  city?: string | null;
  image_url?: string | null;
  distance_km: number;
  driving_time_mins?: number | null;
  walking_time_mins?: number | null;
  is_highlighted: boolean;
  display_label?: string | null;
}

export interface LandmarksByCategory {
  category: string;
  category_label: string;
  landmarks: LandmarkWithDistance[];
}

export interface ProjectLandmarksResponse {
  project_id: number;
  categories: LandmarksByCategory[];
  highlighted: LandmarkWithDistance[];
  total_count: number;
}

export interface LandmarkLinksProps {
  /** Landmarks data from API */
  landmarks?: ProjectLandmarksResponse | null;
  
  /** Maximum landmarks to show per category */
  limitPerCategory?: number;
  
  /** Show images for landmarks */
  showImages?: boolean;
  
  /** Compact mode for cards */
  compact?: boolean;
  
  /** Callback when landmark is clicked */
  onLandmarkClick?: (landmark: LandmarkWithDistance) => void;
  
  /** Additional class name */
  className?: string;
}

const CATEGORY_ICONS: Record<string, string> = {
  mall: '🛍️',
  tech_park: '🏢',
  metro_station: '🚇',
  railway_station: '🚂',
  airport: '✈️',
  hospital: '🏥',
  school: '🎓',
  bus_stand: '🚌',
  park: '🌳',
  restaurant: '🍽️',
};

function formatDistance(km: number): string {
  if (km < 1) {
    return `${Math.round(km * 1000)}m`;
  }
  return `${km.toFixed(1)} km`;
}

function formatTime(mins: number | null | undefined): string | null {
  if (!mins) return null;
  if (mins < 60) return `${mins} min`;
  const hours = Math.floor(mins / 60);
  const remaining = mins % 60;
  return remaining > 0 ? `${hours}h ${remaining}m` : `${hours}h`;
}

export function LandmarkLinks({
  landmarks,
  limitPerCategory = 3,
  showImages = false,
  compact = false,
  onLandmarkClick,
  className = '',
}: LandmarkLinksProps) {
  if (!landmarks || landmarks.total_count === 0) {
    return null;
  }
  
  const handleClick = (landmark: LandmarkWithDistance) => {
    if (onLandmarkClick) {
      onLandmarkClick(landmark);
    }
  };
  
  return (
    <div className={`landmark-links ${compact ? 'landmark-links--compact' : ''} ${className}`}>
      {/* Highlighted landmarks */}
      {landmarks.highlighted.length > 0 && !compact && (
        <div className="landmark-links__highlighted">
          <h4 className="landmark-links__section-title">Key Nearby Places</h4>
          <div className="landmark-links__highlight-grid">
            {landmarks.highlighted.slice(0, 4).map((landmark) => (
              <HighlightedLandmarkCard
                key={landmark.id}
                landmark={landmark}
                showImage={showImages}
                onClick={() => handleClick(landmark)}
              />
            ))}
          </div>
        </div>
      )}
      
      {/* Categories */}
      <div className="landmark-links__categories">
        {landmarks.categories.map((cat) => (
          <div key={cat.category} className="landmark-category">
            <h5 className="landmark-category__title">
              <span className="landmark-category__icon">
                {CATEGORY_ICONS[cat.category] || '📍'}
              </span>
              {cat.category_label}
            </h5>
            
            <ul className="landmark-category__list">
              {cat.landmarks.slice(0, limitPerCategory).map((landmark) => (
                <LandmarkListItem
                  key={landmark.id}
                  landmark={landmark}
                  compact={compact}
                  onClick={() => handleClick(landmark)}
                />
              ))}
            </ul>
            
            {cat.landmarks.length > limitPerCategory && (
              <button className="landmark-category__more">
                +{cat.landmarks.length - limitPerCategory} more
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

interface HighlightedLandmarkCardProps {
  landmark: LandmarkWithDistance;
  showImage: boolean;
  onClick: () => void;
}

function HighlightedLandmarkCard({ 
  landmark, 
  showImage, 
  onClick 
}: HighlightedLandmarkCardProps) {
  return (
    <button className="highlight-card" onClick={onClick}>
      {showImage && landmark.image_url && (
        <div className="highlight-card__image">
          <img src={landmark.image_url} alt={landmark.name} />
        </div>
      )}
      <div className="highlight-card__content">
        <span className="highlight-card__category-icon">
          {CATEGORY_ICONS[landmark.category] || '📍'}
        </span>
        <div className="highlight-card__info">
          <span className="highlight-card__name">{landmark.name}</span>
          <span className="highlight-card__distance">
            {formatDistance(landmark.distance_km)}
            {landmark.driving_time_mins && (
              <span className="highlight-card__time">
                • {formatTime(landmark.driving_time_mins)} drive
              </span>
            )}
          </span>
        </div>
      </div>
    </button>
  );
}

interface LandmarkListItemProps {
  landmark: LandmarkWithDistance;
  compact: boolean;
  onClick: () => void;
}

function LandmarkListItem({ 
  landmark, 
  compact,
  onClick 
}: LandmarkListItemProps) {
  return (
    <li className="landmark-item">
      <button className="landmark-item__link" onClick={onClick}>
        <span className="landmark-item__name">{landmark.name}</span>
        <span className="landmark-item__meta">
          <span className="landmark-item__distance">
            {formatDistance(landmark.distance_km)}
          </span>
          {!compact && landmark.driving_time_mins && (
            <span className="landmark-item__time">
              {formatTime(landmark.driving_time_mins)}
            </span>
          )}
        </span>
      </button>
    </li>
  );
}

/**
 * Compact inline display for project cards
 */
export function NearbyHighlights({ 
  landmarks,
  limit = 2,
  className = '',
}: { 
  landmarks?: ProjectLandmarksResponse | null;
  limit?: number;
  className?: string;
}) {
  if (!landmarks || landmarks.highlighted.length === 0) {
    return null;
  }
  
  const displayed = landmarks.highlighted.slice(0, limit);
  
  return (
    <div className={`nearby-highlights ${className}`}>
      {displayed.map((landmark) => (
        <span key={landmark.id} className="nearby-highlight">
          <span className="nearby-highlight__icon">
            {CATEGORY_ICONS[landmark.category] || '📍'}
          </span>
          <span className="nearby-highlight__text">
            {formatDistance(landmark.distance_km)} from {landmark.name}
          </span>
        </span>
      ))}
    </div>
  );
}

export default LandmarkLinks;
