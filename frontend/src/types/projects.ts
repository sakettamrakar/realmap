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
  nearby_counts?: {
    schools?: number;
    hospitals?: number;
    transit?: number;
  };
}

export interface ProjectSearchResponse {
  page: number;
  page_size: number;
  total: number;
  items: ProjectSummary[];
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
  qa?: Record<string, unknown>;
  raw?: Record<string, unknown>;
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
  sort_by?: "overall_score" | "location_score" | "registration_date" | "name";
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
