export interface Filters {
  district: string;
  minOverallScore: number;
  nameQuery: string;
  sortBy: "overall_score" | "location_score" | "registration_date" | "name";
  sortDir: "asc" | "desc";
}
