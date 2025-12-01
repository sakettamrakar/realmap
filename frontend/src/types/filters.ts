export interface Filters {
  district: string;
  tehsil?: string;
  minOverallScore: number;
  minPrice?: number;
  maxPrice?: number;
  nameQuery: string;
  projectTypes: string[];
  statuses: string[];
  sortBy: "overall_score" | "location_score" | "registration_date" | "name" | "price" | "value_score";
  sortDir: "asc" | "desc";
  // Point 24: Tag-based filtering
  tags: string[];
  tagsMatchAll: boolean;
  // Point 25: RERA verification filter
  reraVerifiedOnly: boolean;
}
