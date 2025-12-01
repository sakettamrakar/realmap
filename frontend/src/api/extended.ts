/**
 * Extended API Client Functions (Points 11-17 APIs)
 * 
 * API functions for the new endpoints created in Phase 2:
 * - Analytics (price trends)
 * - Access (brochure downloads)
 * - Discovery (API metadata)
 * - Media (rich media assets)
 */

import { apiClient } from "./client";
import type {
  PriceTrendResponse,
  BrochureAccessRequest,
  BrochureAccessResponse,
  ProjectMediaResponse,
  ApiMetaResponse,
} from "../types/api";

// ====================
// Analytics API
// ====================

/**
 * Get price trends for a project
 */
export async function getPriceTrends(
  projectId: number,
  options?: {
    period?: "3m" | "6m" | "1y" | "2y";
    granularity?: "day" | "week" | "month";
  }
): Promise<PriceTrendResponse> {
  const params = new URLSearchParams();
  params.append("project_id", String(projectId));
  if (options?.period) params.append("period", options.period);
  if (options?.granularity) params.append("granularity", options.granularity);

  const response = await apiClient.get<PriceTrendResponse>(
    `/api/v1/analytics/price-trends?${params.toString()}`
  );
  return response.data;
}

/**
 * Compare price trends across multiple projects
 */
export async function comparePriceTrends(
  projectIds: number[],
  options?: {
    period?: "3m" | "6m" | "1y" | "2y";
    granularity?: "day" | "week" | "month";
  }
): Promise<Record<number, PriceTrendResponse>> {
  const params = new URLSearchParams();
  projectIds.forEach(id => params.append("project_ids", String(id)));
  if (options?.period) params.append("period", options.period);
  if (options?.granularity) params.append("granularity", options.granularity);

  const response = await apiClient.get<Record<number, PriceTrendResponse>>(
    `/api/v1/analytics/price-trends/compare?${params.toString()}`
  );
  return response.data;
}

// ====================
// Access API (Brochure Downloads)
// ====================

/**
 * Request access to a brochure (lead-gated)
 */
export async function requestBrochureAccess(
  request: BrochureAccessRequest
): Promise<BrochureAccessResponse> {
  const response = await apiClient.post<BrochureAccessResponse>(
    "/api/v1/access/brochure",
    request
  );
  return response.data;
}

/**
 * Check if brochure is available for download
 */
export async function checkBrochureAvailability(
  brochureId: string
): Promise<{ available: boolean; requires_lead: boolean; page_count?: number }> {
  const response = await apiClient.get<{ available: boolean; requires_lead: boolean; page_count?: number }>(
    `/api/v1/access/brochure/${brochureId}/available`
  );
  return response.data;
}

// ====================
// Media API
// ====================

/**
 * Get rich media assets for a project
 */
export async function getProjectMedia(
  projectId: number,
  options?: {
    type?: "image" | "video" | "brochure" | "floorplan";
    limit?: number;
  }
): Promise<ProjectMediaResponse> {
  const params = new URLSearchParams();
  if (options?.type) params.append("type", options.type);
  if (options?.limit) params.append("limit", String(options.limit));

  const queryString = params.toString();
  const url = queryString
    ? `/api/v1/projects/${projectId}/media?${queryString}`
    : `/api/v1/projects/${projectId}/media`;

  const response = await apiClient.get<ProjectMediaResponse>(url);
  return response.data;
}

// ====================
// Discovery API
// ====================

/**
 * Get API metadata and capabilities
 */
export async function getAPIMeta(): Promise<ApiMetaResponse> {
  const response = await apiClient.get<ApiMetaResponse>("/api/v1/api/meta");
  return response.data;
}

// ====================
// Unified Project Lookup
// ====================

/**
 * Lookup project by ID or RERA number
 * Implements Point 11 - Unified ID/RERA lookup
 */
export async function lookupProject(
  identifier: string | number,
  options?: {
    include_jsonld?: boolean;
  }
): Promise<unknown> {
  const params = new URLSearchParams();
  if (options?.include_jsonld) params.append("include_jsonld", "true");

  const queryString = params.toString();
  const url = queryString
    ? `/api/v1/projects/lookup/${identifier}?${queryString}`
    : `/api/v1/projects/lookup/${identifier}`;

  const response = await apiClient.get(url);
  return response.data;
}

// ====================
// Neighborhood Stats (for PriceComparisonWidget)
// ====================

/**
 * Get neighborhood price statistics
 * Used by PriceComparisonWidget for comparison data
 */
export async function getNeighborhoodStats(
  projectId: number
): Promise<{
  average: number;
  min: number;
  max: number;
  sample_size: number;
  area_name: string;
}> {
  // This would call a real endpoint - for now returns mock structure
  // In production, this would be: /api/v1/analytics/neighborhood/{projectId}
  const response = await apiClient.get<{
    average: number;
    min: number;
    max: number;
    sample_size: number;
    area_name: string;
  }>(`/api/v1/analytics/neighborhood/${projectId}`);
  return response.data;
}
