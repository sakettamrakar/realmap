export interface Filters {
  district: string;
  minOverallScore: number;
  minPrice?: number;
  maxPrice?: number;
  nameQuery: string;
  sortBy: "overall_score" | "location_score" | "registration_date" | "name" | "price";
  sortDir: "asc" | "desc";
}
