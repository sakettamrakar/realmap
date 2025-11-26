export interface ProjectSummary {
  project_id: number;
  name: string;
  district?: string;
  tehsil?: string;
  project_type?: string;
  status?: string;
  lat?: number;
  lon?: number;
  geo_quality?: string;
  overall_score?: number;
  location_score?: number;
  amenity_score?: number;
  value_score?: number;
  value_bucket?: 'excellent' | 'good' | 'fair' | 'poor' | 'unknown';
  units?: number;
  area_sqft?: number;
  registration_date?: string;
  distance_km?: number;
  highlight_amenities?: string[];
  onsite_amenity_counts?: {
    total?: number;
    primary?: number;
    secondary?: number;
  };
  score_status?: 'ok' | 'partial' | 'insufficient_data';
  score_status_reason?: string | string[] | Record<string, unknown>;
  nearby_counts?: {
    schools?: number;
    hospitals?: number;
    transit?: number;
  };
  min_price_total?: number;
  max_price_total?: number;
  min_price_per_sqft?: number;
  max_price_per_sqft?: number;
}

export interface ProjectSearchResponse {
  page: number;
  page_size: number;
  total: number;
  items: ProjectSummary[];
}

export interface UnitType {
  label: string;
  bedrooms?: number;
  area_range?: [number | null, number | null];
}

export interface ScoreFactorsDetail {
  strong?: string[];
  weak?: string[];
}

export interface ScoreExplanationFactors {
  onsite?: ScoreFactorsDetail;
  location?: ScoreFactorsDetail;
}

export interface ScoreExplanation {
  summary: string;
  positives: string[];
  negatives: string[];
  factors?: ScoreExplanationFactors;
}

export interface ProjectDetail {
  project: {
    project_id: number;
    name: string;
    rera_number?: string;
    developer?: string;
    project_type?: string;
    status?: string;
    registration_date?: string;
    expected_completion?: string;
    rera_fields?: Record<string, unknown>;
  };
  location?: {
    lat?: number;
    lon?: number;
    geo_source?: string;
    geo_confidence?: string;
    address?: string;
    district?: string;
    tehsil?: string;
  };
  scores?: {
    overall_score?: number;
    location_score?: number;
    amenity_score?: number;
    value_score?: number;
    value_bucket?: 'excellent' | 'good' | 'fair' | 'poor' | 'unknown';
    score_status?: 'ok' | 'partial' | 'insufficient_data';
    score_status_reason?: string | string[] | Record<string, unknown>;
    scoring_version?: string;
  };
  amenities?: {
    onsite_list?: string[];
    onsite_counts?: {
      total?: number;
      primary?: number;
      secondary?: number;
    };
    onsite_progress?: Record<string, number>;
    onsite_images?: Record<string, string[]>;
    nearby_summary?: Record<string, { count?: number; avg_distance_km?: number }>;
    top_nearby?: Record<string, { name?: string; distance_km?: number }[]>;
  };
  pricing?: {
    min_price_total?: number;
    max_price_total?: number;
    min_price_per_sqft?: number;
    max_price_per_sqft?: number;
    unit_types?: UnitType[];
  };
  qa?: Record<string, unknown>;
  raw?: Record<string, unknown>;
  score_explanation?: ScoreExplanation;
}

export interface ProjectMapPin {
  project_id: number;
  name: string;
  lat: number;
  lon: number;
  overall_score?: number;
  project_type?: string;
  status?: string;
  geo_source?: string;
  geo_precision?: string;
  size_hint?: {
    units?: number;
    area_sqft?: number;
  };
}

export interface SearchProjectsParams {
  district?: string;
  tehsil?: string;
  project_type?: string;
  status?: string;
  q?: string;
  min_overall_score?: number;
  min_location_score?: number;
  min_amenity_score?: number;
  min_price?: number;
  max_price?: number;
  sort_by?: "overall_score" | "location_score" | "registration_date" | "name" | "price" | "value_score";
  sort_dir?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

export interface MapPinsParams {
  bbox: BBox;
  min_overall_score?: number;
  project_type?: string;
  status?: string;
}

export interface ProjectMapResponse {
  items: ProjectMapPin[];
}

export interface BBox {
  minLat: number;
  minLon: number;
  maxLat: number;
  maxLon: number;
}
