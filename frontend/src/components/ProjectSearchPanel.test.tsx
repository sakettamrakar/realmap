import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ProjectSearchPanel from "./ProjectSearchPanel";
import type { Filters } from "../types/filters";
import type { ProjectSummary } from "../types/projects";

const sampleFilters: Filters = {
  district: "",
  minOverallScore: 0,
  nameQuery: "",
  sortBy: "overall_score",
  sortDir: "desc",
};

const sampleProjects: ProjectSummary[] = [
  {
    project_id: 1,
    name: "Skyline Heights",
    district: "Raipur",
    overall_score: 0.82,
    location_score: 0.78,
    amenity_score: 0.7,
    status: "Registered",
  },
];

describe("ProjectSearchPanel", () => {
  it("renders projects and triggers filter updates", () => {
    const onFiltersChange = vi.fn();
    const onSelectProject = vi.fn();
    const onPageChange = vi.fn();
    const onResetFilters = vi.fn();

    render(
      <ProjectSearchPanel
        filters={sampleFilters}
        onFiltersChange={onFiltersChange}
        projects={sampleProjects}
        loading={false}
        onSelectProject={onSelectProject}
        selectedProjectId={null}
        total={sampleProjects.length}
        page={1}
        pageSize={10}
        onPageChange={onPageChange}
        onResetFilters={onResetFilters}
        defaultFilters={sampleFilters}
      />,
    );

    expect(screen.getByText("Skyline Heights")).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText(/Search by project or promoter/i), {
      target: { value: "Sky" },
    });
    expect(onFiltersChange).toHaveBeenCalledWith({ nameQuery: "Sky" });

    fireEvent.click(screen.getByText("Skyline Heights"));
    expect(onSelectProject).toHaveBeenCalledWith(1);
  });
});
