import { describe, expect, it, vi, beforeEach } from "vitest";
import { apiClient } from "./client";
import {
  getProject,
  getProjectsForMap,
  searchProjects,
} from "./projectsApi";
import type { ProjectSearchResponse } from "../types/projects";

describe("projectsApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls search with filters and returns data", async () => {
    const mockData: ProjectSearchResponse = {
      page: 1,
      page_size: 20,
      total: 1,
      items: [
        {
          project_id: 123,
          name: "Test Project",
          district: "Raipur",
          overall_score: 0.8,
        },
      ],
    };

    const spy = vi
      .spyOn(apiClient, "get")
      .mockResolvedValue({ data: mockData } as any);

    const result = await searchProjects({
      district: "Raipur",
      min_overall_score: 0.5,
      name_contains: "Test",
    });

    expect(spy).toHaveBeenCalledWith("/projects/search", {
      params: {
        district: "Raipur",
        min_overall_score: 0.5,
        name_contains: "Test",
      },
    });
    expect(result.items[0].name).toBe("Test Project");
  });

  it("formats bbox for map pins", async () => {
    const spy = vi
      .spyOn(apiClient, "get")
      .mockResolvedValue({ data: { items: [] } } as any);

    await getProjectsForMap({
      bbox: { minLat: 1, minLon: 2, maxLat: 3, maxLon: 4 },
      min_overall_score: 0.6,
    });

    expect(spy).toHaveBeenCalledWith("/projects/map", {
      params: {
        bbox: "1,2,3,4",
        min_overall_score: 0.6,
      },
    });
  });

  it("requests project details by id", async () => {
    const spy = vi
      .spyOn(apiClient, "get")
      .mockResolvedValue({ data: { project: { name: "P" } } } as any);

    await getProject(123);

    expect(spy).toHaveBeenCalledWith("/projects/123");
  });
});
