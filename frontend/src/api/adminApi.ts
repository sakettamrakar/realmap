/**
 * Admin/debug API functions.
 */
import type { ProjectFullDebug, ReraSearchResult } from "../types/admin";
import { apiClient } from "./client";

/**
 * Get full debug information for a project by ID.
 */
export async function getProjectFullDebug(
  projectId: number,
): Promise<ProjectFullDebug> {
  try {
    const { data } = await apiClient.get<ProjectFullDebug>(
      `/admin/projects/${projectId}/full_debug`,
    );
    return data;
  } catch (error) {
    console.error(`Failed to fetch full debug for project ${projectId}`, error);
    throw new Error("Unable to load project debug information.");
  }
}

/**
 * Search for a project by RERA registration number.
 */
export async function searchProjectByRera(
  reraNumber: string,
): Promise<ReraSearchResult> {
  try {
    const { data } = await apiClient.get<ReraSearchResult>(
      `/admin/projects/search_by_rera/${encodeURIComponent(reraNumber)}`,
    );
    return data;
  } catch (error) {
    console.error(`Failed to search for RERA ${reraNumber}`, error);
    throw new Error("Project not found with that RERA number.");
  }
}
