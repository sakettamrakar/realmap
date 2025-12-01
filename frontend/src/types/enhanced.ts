/**
 * Enhanced TypeScript interfaces for the 10-Point Enhancement Standard.
 * 
 * This file contains NEW types to match the enhanced data model.
 * Import alongside existing types/projects.ts.
 */

// =============================================================================
// Enums (Mirror of backend enums)
// =============================================================================

export type AreaUnit = 'SQFT' | 'SQM';

export type ProjectPhase = 
  | 'PRE_LAUNCH'
  | 'UNDER_CONSTRUCTION'
  | 'READY_TO_MOVE'
  | 'COMPLETED';

export type UnitStatus = 
  | 'AVAILABLE'
  | 'BOOKED'
  | 'SOLD'
  | 'UNDER_CONSTRUCTION'
  | 'READY';

export type AmenityCategoryType = 
  | 'HEALTH'
  | 'LEISURE'
  | 'CONVENIENCE'
  | 'CONNECTIVITY'
  | 'SECURITY'
  | 'ENVIRONMENT'
  | 'SOCIAL';

// =============================================================================
// Enhancement #1: Developer Identity
// =============================================================================

export interface Developer {
  id: number;
  name: string;
  state_code?: string;
  legal_name?: string;
  estd_year?: number;
  /** Trust score 0-10 based on delivery history */
  trust_score?: number;
  total_delivered_sqft?: number;
  total_projects_completed?: number;
  total_projects_ongoing?: number;
  headquarters_city?: string;
  website?: string;
  logo_url?: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface DeveloperSummary {
  id: number;
  name: string;
  trust_score?: number;
  total_projects_completed?: number;
  logo_url?: string;
}

export interface DeveloperCreate {
  name: string;
  state_code?: string;
  legal_name?: string;
  estd_year?: number;
  trust_score?: number;
  total_delivered_sqft?: number;
  headquarters_city?: string;
  website?: string;
}

// =============================================================================
// Enhancement #2: Unit Hierarchy (Project > Tower > Unit)
// =============================================================================

export interface Unit {
  id: number;
  building_id: number;
  unit_type_id?: number;
  unit_number: string;
  floor_number?: number;
  wing?: string;
  
  // Area measurements
  carpet_area_sqft?: number;
  builtup_area_sqft?: number;
  super_builtup_area_sqft?: number;
  
  // Status
  status?: UnitStatus;
  is_corner_unit?: boolean;
  facing_direction?: string;
  
  // Pricing
  base_price?: number;
  price_per_sqft_carpet?: number;
  price_per_sqft_sbua?: number;
  
  created_at?: string;
  updated_at?: string;
}

export interface UnitSummary {
  id: number;
  unit_number: string;
  floor_number?: number;
  status?: string;
  carpet_area_sqft?: number;
  base_price?: number;
}

export interface UnitCreate {
  building_id: number;
  unit_type_id?: number;
  unit_number: string;
  floor_number?: number;
  wing?: string;
  carpet_area_sqft?: number;
  builtup_area_sqft?: number;
  super_builtup_area_sqft?: number;
  status?: UnitStatus;
  base_price?: number;
}

export interface TowerWithUnits {
  id: number;
  building_name: string;
  building_type?: string;
  number_of_floors?: number;
  total_units?: number;
  status?: string;
  units: UnitSummary[];
}

export interface ProjectHierarchy {
  project_id: number;
  project_name: string;
  towers: TowerWithUnits[];
}

// =============================================================================
// Enhancement #3: Explicit Area Normalization
// =============================================================================

export interface NormalizedArea {
  carpet_area?: number;
  builtup_area?: number;
  super_builtup_area?: number;
  unit: AreaUnit;
}

// =============================================================================
// Enhancement #4: Price Per Sqft by Area Type
// =============================================================================

export interface PricingByAreaType {
  // Generic (backward compatible)
  min_price_total?: number;
  max_price_total?: number;
  min_price_per_sqft?: number;
  max_price_per_sqft?: number;
  
  // Per area type (Enhancement #4)
  price_per_sqft_carpet_min?: number;
  price_per_sqft_carpet_max?: number;
  price_per_sqft_sbua_min?: number;
  price_per_sqft_sbua_max?: number;
}

// =============================================================================
// Enhancement #5: Structured Possession Timeline
// =============================================================================

export interface PossessionTimeline {
  id: number;
  project_id: number;
  building_id?: number;
  
  /** Date promised by sales/marketing team */
  marketing_target?: string;
  /** Legal deadline per local regulations */
  regulatory_deadline?: string;
  /** RERA registered completion date */
  rera_deadline?: string;
  /** Actual completion date (if completed) */
  actual_completion?: string;
  
  phase?: ProjectPhase;
  phase_start_date?: string;
  
  /** Calculated delay from original RERA deadline */
  delay_months?: number;
  delay_reason?: string;
  notes?: string;
  
  created_at?: string;
  updated_at?: string;
}

export interface PossessionTimelineCreate {
  project_id: number;
  building_id?: number;
  marketing_target?: string;
  regulatory_deadline?: string;
  rera_deadline?: string;
  phase?: ProjectPhase;
}

// =============================================================================
// Enhancement #7: Amenities Taxonomy
// =============================================================================

export interface AmenityCategory {
  id: number;
  code: string;
  name: string;
  description?: string;
  icon?: string;
  display_order?: number;
  /** Weight for lifestyle score calculation (0-10) */
  lifestyle_weight?: number;
}

export interface Amenity {
  id: number;
  category_id: number;
  code: string;
  name: string;
  description?: string;
  icon?: string;
  /** Points contributed to lifestyle score when present */
  lifestyle_points?: number;
}

export interface AmenityType {
  id: number;
  amenity_id: number;
  variant_code: string;
  variant_name: string;
  description?: string;
  /** Multiplier for lifestyle points (e.g., 1.5x for premium variants) */
  premium_multiplier?: number;
}

export interface ProjectAmenity {
  id: number;
  project_id: number;
  amenity_type_id: number;
  is_available: boolean;
  is_chargeable?: boolean;
  monthly_fee?: number;
  quantity?: number;
  size_sqft?: number;
  details?: string;
  images?: string[];
  created_at?: string;
}

export interface AmenityTaxonomyFlat {
  category_code: string;
  category_name: string;
  amenity_code: string;
  amenity_name: string;
  type_code: string;
  type_name: string;
  lifestyle_points?: number;
  premium_multiplier?: number;
}

// =============================================================================
// Enhancement #8: Enhanced Unit Types
// =============================================================================

export interface EnhancedUnitType {
  id: number;
  project_id: number;
  unit_label?: string;
  bedrooms?: number;
  bathrooms?: number;
  /** Enhancement #8: Balcony count */
  balcony_count?: number;
  
  // Enhancement #3: Normalized areas
  carpet_area_min_sqft?: number;
  carpet_area_max_sqft?: number;
  builtup_area_min_sqft?: number;
  builtup_area_max_sqft?: number;
  super_builtup_area_min_sqft?: number;
  super_builtup_area_max_sqft?: number;
  canonical_area_unit?: AreaUnit;
  
  // Enhancement #8: Maintenance
  maintenance_fee_monthly?: number;
  maintenance_fee_per_sqft?: number;
  
  is_active?: boolean;
  created_at?: string;
}

// =============================================================================
// Enhancement #9: Transaction Registry
// =============================================================================

export interface Transaction {
  id: number;
  project_id: number;
  building_id?: number;
  unit_id?: number;
  
  // Registry details
  registry_date?: string;
  registry_number?: string;
  sub_registrar_office?: string;
  
  // Amounts
  /** Amount declared in registry */
  declared_amount?: number;
  stamp_duty_paid?: number;
  registration_fee?: number;
  
  // Area
  registered_area_sqft?: number;
  /** carpet, builtup, or super_builtup */
  area_type?: string;
  price_per_sqft_registered?: number;
  
  // Buyer (anonymized)
  /** individual, company, huf, nri */
  buyer_type?: string;
  
  created_at?: string;
  verified_at?: string;
  verification_status?: string;
}

export interface TransactionSummary {
  registry_date?: string;
  declared_amount?: number;
  registered_area_sqft?: number;
  price_per_sqft_registered?: number;
}

export interface TransactionCreate {
  project_id: number;
  building_id?: number;
  unit_id?: number;
  registry_date?: string;
  registry_number?: string;
  declared_amount?: number;
  registered_area_sqft?: number;
  area_type?: string;
  buyer_type?: string;
}

export interface TransactionStats {
  total_transactions: number;
  avg_price_per_sqft?: number;
  median_price_per_sqft?: number;
  min_price_per_sqft?: number;
  max_price_per_sqft?: number;
  /** Trend: positive = appreciating, negative = depreciating */
  price_trend_percent?: number;
  last_transaction_date?: string;
}

// =============================================================================
// Enhancement #10: Granular Ratings
// =============================================================================

export interface StructuredRatings {
  // Existing scores (normalized to 0-10)
  connectivity?: number;
  daily_needs?: number;
  social_infra?: number;
  
  // Enhancement #7: Lifestyle from amenity taxonomy
  lifestyle?: number;
  
  // Enhancement #10: New ratings
  /** Gated, CCTV, guards, etc. */
  safety?: number;
  /** Green cover, air quality, noise */
  environment?: number;
  /** Price trends, appreciation */
  investment_potential?: number;
  
  // Value for money (existing)
  value?: number;
}

export interface EnhancedScores {
  // Existing scores (0-100 scale)
  overall_score?: number;
  amenity_score?: number;
  location_score?: number;
  value_score?: number;
  
  // Sub-scores
  connectivity_score?: number;
  daily_needs_score?: number;
  social_infra_score?: number;
  
  // Enhancement #7 & #10 (0-10 scale)
  lifestyle_score?: number;
  safety_score?: number;
  environment_score?: number;
  investment_potential_score?: number;
  
  // Full structured breakdown
  structured_ratings?: StructuredRatings;
  
  // Metadata
  score_status?: 'ok' | 'partial' | 'insufficient_data';
  score_status_reason?: string | string[] | Record<string, unknown>;
  score_version?: string;
  last_computed_at?: string;
}

// =============================================================================
// Composite Types
// =============================================================================

export interface EnhancedProjectDetail {
  // Core info
  project_id: number;
  name: string;
  rera_number?: string;
  status?: string;
  
  // Enhancement #1: Developer
  developer?: DeveloperSummary;
  
  // Enhancement #5: Possession
  possession_timeline?: PossessionTimeline;
  
  // Location
  location?: {
    lat?: number;
    lon?: number;
    geo_source?: string;
    geo_confidence?: string;
    address?: string;
    district?: string;
    tehsil?: string;
  };
  
  // Enhancement #10: Scores
  scores?: EnhancedScores;
  
  // Enhancement #4: Pricing
  pricing?: PricingByAreaType;
  
  // Enhancement #8: Unit types
  unit_types?: EnhancedUnitType[];
  
  // Enhancement #7: Amenities with taxonomy
  amenities?: ProjectAmenity[];
  amenities_flat?: AmenityTaxonomyFlat[];
  
  // Enhancement #2: Units summary
  units_summary?: {
    total_units?: number;
    available?: number;
    sold?: number;
    by_status?: Record<UnitStatus, number>;
    by_floor?: Record<number, number>;
  };
  
  // Enhancement #9: Transaction stats
  transaction_stats?: TransactionStats;
}

// =============================================================================
// API Request/Response Types
// =============================================================================

export interface DeveloperSearchParams {
  name?: string;
  state_code?: string;
  min_trust_score?: number;
  min_projects_completed?: number;
  sort_by?: 'name' | 'trust_score' | 'total_projects_completed';
  sort_dir?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}

export interface UnitSearchParams {
  project_id?: number;
  building_id?: number;
  status?: UnitStatus;
  min_carpet_area?: number;
  max_carpet_area?: number;
  min_price?: number;
  max_price?: number;
  floor_min?: number;
  floor_max?: number;
  sort_by?: 'unit_number' | 'floor_number' | 'carpet_area_sqft' | 'base_price';
  sort_dir?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}

export interface TransactionSearchParams {
  project_id?: number;
  building_id?: number;
  min_date?: string;
  max_date?: string;
  min_amount?: number;
  max_amount?: number;
  buyer_type?: string;
  sort_by?: 'registry_date' | 'declared_amount' | 'price_per_sqft_registered';
  sort_dir?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse<T> {
  page: number;
  page_size: number;
  total: number;
  items: T[];
}

// Type aliases for paginated responses
export type DeveloperSearchResponse = PaginatedResponse<Developer>;
export type UnitSearchResponse = PaginatedResponse<Unit>;
export type TransactionSearchResponse = PaginatedResponse<Transaction>;
