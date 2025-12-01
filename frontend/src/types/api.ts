/**
 * TypeScript interfaces for 7-Point API Standard (Points 11-17).
 *
 * Matches the Pydantic schemas in schemas_api.py
 */

// =============================================================================
// Generic Response Envelope (Point 16)
// =============================================================================

export interface PaginationLinks {
  self: string;
  next: string | null;
  prev: string | null;
  first: string;
  last: string | null;
}

export interface ResponseMeta {
  api_version: string;
  timestamp: string;
  request_id?: string;
  limit?: number;
  offset?: number;
  total_count?: number;
  page?: number;
  page_size?: number;
  total_pages?: number;
}

export interface EnvelopedResponse<T> {
  data: T;
  meta: ResponseMeta;
  links?: PaginationLinks;
}

export interface EnvelopedListResponse<T> {
  data: T[];
  meta: ResponseMeta;
  links: PaginationLinks;
}

// =============================================================================
// Data Provenance (Point 17)
// =============================================================================

export type ExtractionMethod = 'scraper' | 'manual' | 'feed' | 'api' | 'ocr';

export interface DataProvenance {
  last_updated_at: string | null;
  source_domain: string | null;
  extraction_method: ExtractionMethod | null;
  confidence_score: number | null;
  data_quality_score: number | null;
  raw_source_url: string | null;
  last_verified_at: string | null;
}

// =============================================================================
// Unified Project Identity (Point 11)
// =============================================================================

export interface UnitSummary {
  id: number;
  floor_number: number | null;
  unit_number: string | null;
  status: string | null;
  carpet_area_sqft: number | null;
  builtup_area_sqft: number | null;
  super_builtup_area_sqft: number | null;
  price_total: number | null;
}

export interface TowerHierarchy {
  id: number;
  building_name: string;
  building_type: string | null;
  number_of_floors: number | null;
  total_units: number | null;
  status: string | null;
  units: UnitSummary[];
}

export interface ProjectHierarchy {
  id: number;
  rera_id: string;
  state_code: string;
  name: string;
  status: string | null;
  registration_date: string | null;
  expected_completion: string | null;
  district: string | null;
  tehsil: string | null;
  address: string | null;
  lat: number | null;
  lon: number | null;
  developer_id: number | null;
  developer_name: string | null;
  towers: TowerHierarchy[];
  unit_types: Record<string, unknown>[];
  provenance: DataProvenance | null;
}

// =============================================================================
// Rich Media & Asset Management (Point 12)
// =============================================================================

export type MediaType =
  | 'gallery'
  | 'floorplan'
  | 'masterplan'
  | 'brochure'
  | 'video'
  | 'virtual_tour'
  | 'elevation'
  | 'amenity';

export type LicenseType =
  | 'proprietary'
  | 'public_domain'
  | 'creative_commons'
  | 'rera_official';

export interface MediaAsset {
  id: number;
  type: MediaType;
  url: string;
  thumbnail_url: string | null;
  width_px: number | null;
  height_px: number | null;
  filesize_kb: number | null;
  file_format: string | null;
  mime_type: string | null;
  license_type: LicenseType;
  attribution: string | null;
  unit_type_id: number | null;
  unit_type_label: string | null;
  title: string | null;
  description: string | null;
  sort_order: number;
  is_primary: boolean;
  source_url: string | null;
  captured_at: string | null;
}

export interface ProjectMediaResponse {
  project_id: number;
  project_name: string;
  gallery: MediaAsset[];
  floorplans: MediaAsset[];
  masterplans: MediaAsset[];
  brochures: MediaAsset[];
  videos: MediaAsset[];
  total_count: number;
}

// =============================================================================
// Price Trends & Analytics (Point 13)
// =============================================================================

export type Timeframe = '1M' | '3M' | '6M' | '1Y' | '2Y' | '5Y' | 'ALL';
export type Granularity = 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
export type EntityType = 'project' | 'locality' | 'district' | 'developer';

export interface PriceTrendDataPoint {
  period: string;
  period_start: string;
  period_end: string;
  avg_price_per_sqft: number | null;
  min_price_per_sqft: number | null;
  max_price_per_sqft: number | null;
  median_price_per_sqft: number | null;
  avg_total_price: number | null;
  min_total_price: number | null;
  max_total_price: number | null;
  transaction_volume: number | null;
  inventory_count: number | null;
  change_pct: number | null;
  change_abs: number | null;
  sample_size: number | null;
  confidence_level: string | null;
}

export interface PriceTrendRequest {
  entity_id: number;
  entity_type?: EntityType;
  timeframe?: Timeframe;
  granularity?: Granularity;
  unit_type?: string;
  area_type?: string;
}

export interface PriceTrendResponse {
  entity_id: number;
  entity_type: EntityType;
  entity_name: string;
  timeframe: Timeframe;
  granularity: Granularity;
  trend_data: PriceTrendDataPoint[];
  current_avg_price: number | null;
  period_high: number | null;
  period_low: number | null;
  overall_change_pct: number | null;
  data_points_count: number;
  earliest_date: string | null;
  latest_date: string | null;
  provenance: DataProvenance | null;
}

export interface LocalityTrendComparison {
  localities: PriceTrendResponse[];
  benchmark_locality: string | null;
}

// =============================================================================
// Gated Brochure Access (Point 14)
// =============================================================================

export interface BrochureAccessRequest {
  project_id: number;
  document_id?: number;
  email?: string;
  phone?: string;
  name?: string;
  marketing_consent?: boolean;
  privacy_consent?: boolean;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  referrer_url?: string;
}

export interface SignedUrlResponse {
  download_url: string;
  expires_at: string;
  expires_in_seconds: number;
  document_id: number;
  filename: string;
  file_format: string;
  filesize_kb: number | null;
  access_token: string;
  download_limit: number;
}

export interface BrochureAccessResponse {
  success: boolean;
  signed_url: SignedUrlResponse | null;
  lead_id: string | null;
  error_code: string | null;
  error_message: string | null;
}

// =============================================================================
// JSON-LD SEO (Point 15)
// =============================================================================

export interface SchemaOrgOffer {
  '@type': 'Offer';
  priceCurrency: string;
  price: number | null;
  priceRange: string | null;
  availability: string | null;
  validFrom: string | null;
}

export interface SchemaOrgAggregateRating {
  '@type': 'AggregateRating';
  ratingValue: number;
  bestRating: number;
  worstRating: number;
  ratingCount: number | null;
  reviewCount: number | null;
}

export interface SchemaOrgGeoCoordinates {
  '@type': 'GeoCoordinates';
  latitude: number;
  longitude: number;
}

export interface SchemaOrgAddress {
  '@type': 'PostalAddress';
  streetAddress: string | null;
  addressLocality: string | null;
  addressRegion: string | null;
  postalCode: string | null;
  addressCountry: string;
}

export interface SchemaOrgOrganization {
  '@type': 'Organization';
  name: string;
  url: string | null;
  logo: string | null;
}

export interface SchemaOrgProduct {
  '@context': 'https://schema.org';
  '@type': 'Product' | 'Residence';
  name: string;
  description: string | null;
  sku: string | null;
  productID: string | null;
  image: string[] | null;
  url: string | null;
  geo: SchemaOrgGeoCoordinates | null;
  address: SchemaOrgAddress | null;
  brand: SchemaOrgOrganization | null;
  manufacturer: SchemaOrgOrganization | null;
  offers: SchemaOrgOffer | null;
  aggregateRating: SchemaOrgAggregateRating | null;
  additionalProperty: Record<string, unknown>[] | null;
}

export interface JsonLdWrapper {
  schema_org: SchemaOrgProduct;
  breadcrumb?: Record<string, unknown>;
  faq?: Record<string, unknown>;
}

// =============================================================================
// API Discovery (Point 16)
// =============================================================================

export interface ResourceEndpoint {
  name: string;
  path: string;
  methods: string[];
  description: string | null;
  requires_auth: boolean;
  deprecated: boolean;
  version: string;
}

export interface ApiMetaResponse {
  api_name: string;
  api_version: string;
  base_url: string;
  documentation_url: string | null;
  resources: ResourceEndpoint[];
  rate_limit: number | null;
  status: string;
  uptime_seconds: number | null;
}

// =============================================================================
// Enhanced Project Detail (Combines all enhancements)
// =============================================================================

export interface ProjectDetailV3 {
  project: ProjectHierarchy;
  location: Record<string, unknown>;
  scores: Record<string, unknown>;
  amenities: Record<string, unknown>;
  pricing: Record<string, unknown> | null;
  qa: Record<string, unknown>;
  score_explanation: Record<string, unknown> | null;
  schema_org: SchemaOrgProduct | null;
  provenance: DataProvenance | null;
  media_summary: Record<string, number> | null;
}

// =============================================================================
// API Client Helper Types
// =============================================================================

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface ApiEndpoint {
  path: string;
  method: HttpMethod;
}

export const API_ENDPOINTS = {
  // Project endpoints
  PROJECT_SEARCH: { path: '/projects/search', method: 'GET' } as ApiEndpoint,
  PROJECT_DETAIL: { path: '/projects/{identifier}', method: 'GET' } as ApiEndpoint,
  PROJECT_MEDIA: { path: '/projects/{id}/media', method: 'GET' } as ApiEndpoint,
  
  // Analytics
  PRICE_TRENDS: { path: '/analytics/price-trends', method: 'GET' } as ApiEndpoint,
  
  // Access
  BROCHURE_ACCESS: { path: '/access/brochure', method: 'POST' } as ApiEndpoint,
  
  // Discovery
  API_META: { path: '/api/meta', method: 'GET' } as ApiEndpoint,
  HEALTH: { path: '/health', method: 'GET' } as ApiEndpoint,
} as const;
