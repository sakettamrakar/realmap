/**
 * Widgets Barrel Export
 * 
 * Re-exports all widget components for easy importing.
 */

export { 
  PriceComparisonWidget,
  calculateDifferencePercent,
  formatIndianCurrency,
  formatPricePerSqft,
  getComparisonStatus,
  type PricePoint,
  type NeighborhoodStats,
  type PriceComparisonWidgetProps
} from './PriceComparisonWidget';

export {
  SmartBrochure,
  formatFileSize,
  type BrochureAccessState,
  type BrochureMetadata,
  type LeadFormData,
  type SmartBrochureProps
} from './SmartBrochure';

export {
  TransactionTable,
  VerificationBadge,
  VERIFICATION_CONFIG,
  type Transaction,
  type VerificationSource,
  type TransactionTableProps,
  type SortField,
  type SortDirection
} from './TransactionTable';

// Point 24: Tag Filtering
export {
  TagFilter,
  TagList,
  type TagCategory,
  type TagWithCount,
  type TagsByCategory,
  type FacetedTagsResponse,
  type TagFilterProps
} from './TagFilter';

// Point 25: Trust Badge
export {
  TrustBadge,
  VerifiedIcon,
  type ReraVerificationStatus,
  type TrustBadgeData,
  type TrustBadgeProps
} from './TrustBadge';

// Point 26: Landmark Links
export {
  LandmarkLinks,
  NearbyHighlights,
  type LandmarkWithDistance,
  type LandmarksByCategory,
  type ProjectLandmarksResponse,
  type LandmarkLinksProps
} from './LandmarkLinks';
