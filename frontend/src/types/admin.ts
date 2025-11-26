/**
 * Types for admin/debug endpoints.
 */

/** File artifact found in outputs directory */
export interface FileArtifact {
  path: string;
  full_path: string;
  run: string;
  size_bytes: number;
}

/** File artifacts organized by type */
export interface FileArtifacts {
  scraped_json: FileArtifact[];
  raw_html: FileArtifact[];
  raw_extracted: FileArtifact[];
  previews: FileArtifact[];
  listings: FileArtifact[];
}

/** Artifact stored in database */
export interface DbArtifact {
  id: number;
  category: string | null;
  artifact_type: string | null;
  file_path: string | null;
  source_url: string | null;
  file_format: string | null;
  is_preview: boolean;
}

/** Score details for debugging */
export interface ScoreDetails {
  amenity_score: number | null;
  location_score: number | null;
  connectivity_score: number | null;
  daily_needs_score: number | null;
  social_infra_score: number | null;
  overall_score: number | null;
  value_score: number | null;
  score_status: string | null;
  score_status_reason: string | null;
  score_version: number | null;
  last_computed_at: string | null;
}

/** Geo location candidate */
export interface GeoCandidate {
  id: number;
  source_type: string;
  lat: number;
  lon: number;
  precision_level: string | null;
  confidence_score: number | null;
  is_active: boolean;
  meta_data: Record<string, unknown> | null;
  created_at: string | null;
}

/** Primary geo information */
export interface GeoPrimary {
  lat: number | null;
  lon: number | null;
  geocoding_status: string | null;
  geocoding_source: string | null;
  geo_source: string | null;
  geo_precision: string | null;
  geo_confidence: number | null;
  geo_normalized_address: string | null;
  geo_formatted_address: string | null;
}

/** Geo details for debugging */
export interface GeoDetails {
  primary: GeoPrimary;
  candidate_locations: GeoCandidate[];
}

/** Amenity stat entry */
export interface AmenityStatEntry {
  amenity_type: string;
  radius_km: number | null;
  nearby_count: number | null;
  nearby_nearest_km: number | null;
  onsite_available: boolean;
  onsite_details: string | null;
  provider_snapshot: string | null;
  last_computed_at: string | null;
}

/** Amenities detail for debugging */
export interface AmenitiesDetails {
  onsite: AmenityStatEntry[];
  nearby: AmenityStatEntry[];
}

/** Pricing snapshot */
export interface PricingSnapshot {
  id: number;
  snapshot_date: string;
  unit_type_label: string | null;
  min_price_total: number | null;
  max_price_total: number | null;
  min_price_per_sqft: number | null;
  max_price_per_sqft: number | null;
  source_type: string | null;
  source_reference: string | null;
  is_active: boolean;
  raw_data: Record<string, unknown> | null;
}

/** Pricing details for debugging */
export interface PricingDetails {
  snapshots: PricingSnapshot[];
}

/** Promoter info */
export interface PromoterInfo {
  name: string | null;
  type: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  website: string | null;
}

/** Core project info */
export interface CoreProjectInfo {
  id: number;
  state_code: string;
  rera_registration_number: string;
  project_name: string;
  status: string | null;
  district: string | null;
  tehsil: string | null;
  village_or_locality: string | null;
  full_address: string | null;
  normalized_address: string | null;
  pincode: string | null;
  approved_date: string | null;
  proposed_end_date: string | null;
  extended_end_date: string | null;
  data_quality_score: number | null;
  scraped_at: string | null;
  last_parsed_at: string | null;
}

/** Debug section containing detailed breakdowns */
export interface DebugSection {
  scores_detail: ScoreDetails;
  geo_detail: GeoDetails;
  amenities_detail: AmenitiesDetails;
  pricing_detail: PricingDetails;
  db_artifacts: { db_artifacts: DbArtifact[] };
  file_artifacts: FileArtifacts;
}

/** Meta information */
export interface DebugMeta {
  endpoint: string;
  project_id: number;
  rera_number: string;
  warning: string;
}

/** Full debug response from /admin/projects/{id}/full_debug */
export interface ProjectFullDebug {
  core: CoreProjectInfo;
  promoters: PromoterInfo[];
  detail: Record<string, unknown>;
  debug: DebugSection;
  raw_data_json: Record<string, unknown> | null;
  _meta: DebugMeta;
}

/** Response from search by RERA */
export interface ReraSearchResult {
  project_id: number;
  rera_registration_number: string;
  project_name: string;
  district: string | null;
}
