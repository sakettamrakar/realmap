import type {
  BBox,
  MapPinsParams,
  ProjectDetail,
  ProjectMapResponse,
  ProjectSearchResponse,
  SearchProjectsParams,
} from "../types/projects";
import { apiClient } from "./client";

const formatBBox = (bbox: BBox) =>
  `${bbox.minLat},${bbox.minLon},${bbox.maxLat},${bbox.maxLon}`;

export async function searchProjects(
  params: SearchProjectsParams,
): Promise<ProjectSearchResponse> {
  try {
    const { data } = await apiClient.get<ProjectSearchResponse>(
      "/projects/search",
      {
        params: {
          ...params,
          project_types: params.project_types,
          statuses: params.statuses,
          min_overall_score: params.min_overall_score ?? undefined,
          min_price: params.min_price ?? undefined,
          max_price: params.max_price ?? undefined,
          q: params.q || undefined,
          district: params.district || undefined,
          sort_by: params.sort_by || undefined,
          sort_dir: params.sort_dir || undefined,
        },
        paramsSerializer: {
          indexes: null, // No brackets for arrays: key=val&key=val
        },
      },
    );
    return data;
  } catch (error) {
    console.error("Failed to search projects", error);
    throw new Error("Unable to load projects. Please try again.");
  }

}

export async function getProject(
  projectId: number,
): Promise<ProjectDetail | null> {
  if (!projectId) return null;
  try {
    const { data } = await apiClient.get<ProjectDetail>(
      `/projects/${projectId}`,
    );
    return data;
  } catch (error) {
    console.error(`Failed to fetch project ${projectId}`, error);
    throw new Error("Unable to load project detail.");
  }
}

export async function getProjectsForMap(
  params: MapPinsParams,
): Promise<ProjectMapResponse> {
  try {
    const { data } = await apiClient.get<ProjectMapResponse>("/projects/map", {
      params: {
        ...params,
        bbox: formatBBox(params.bbox),
      },
    });
    return data;
  } catch (error) {
    console.error("Failed to fetch map pins", error);
    throw new Error("Unable to load map pins.");
  }
}
