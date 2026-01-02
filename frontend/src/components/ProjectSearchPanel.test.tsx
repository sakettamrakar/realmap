import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ProjectSearchPanel from "./ProjectSearchPanel";
import type { Filters } from "../types/filters";
import type { ProjectSummary } from "../types/projects";

const sampleFilters: Filters = {
  district: "",
  minOverallScore: 0,
  nameQuery: "",
  projectTypes: [],
  statuses: [],
  sortBy: "overall_score",
  sortDir: "desc",
  tags: [],
  tagsMatchAll: false,
  reraVerifiedOnly: false,
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

  describe("Filter Chips", () => {
    it("displays district filter chip when district is selected", () => {
      const filtersWithDistrict = { ...sampleFilters, district: "Raipur" };
      const onFiltersChange = vi.fn();

      render(
        <ProjectSearchPanel
          filters={filtersWithDistrict}
          onFiltersChange={onFiltersChange}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          selectedProjectId={null}
          total={1}
          page={1}
          pageSize={10}
          onPageChange={vi.fn()}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      expect(screen.getByText("District: Raipur")).toBeInTheDocument();
    });

    it("displays min score filter chip when min score is set", () => {
      const filtersWithScore = { ...sampleFilters, minOverallScore: 0.5 };
      const onFiltersChange = vi.fn();

      render(
        <ProjectSearchPanel
          filters={filtersWithScore}
          onFiltersChange={onFiltersChange}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          selectedProjectId={null}
          total={1}
          page={1}
          pageSize={10}
          onPageChange={vi.fn()}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      expect(screen.getByText("Min score: 0.50")).toBeInTheDocument();
    });

    it("displays search filter chip when search query is set", () => {
      const filtersWithSearch = { ...sampleFilters, nameQuery: "test" };
      const onFiltersChange = vi.fn();

      render(
        <ProjectSearchPanel
          filters={filtersWithSearch}
          onFiltersChange={onFiltersChange}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          selectedProjectId={null}
          total={1}
          page={1}
          pageSize={10}
          onPageChange={vi.fn()}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      expect(screen.getByText('Search: "test"')).toBeInTheDocument();
    });

    it("displays sort filter chip when sort differs from default", () => {
      const filtersWithSort = { ...sampleFilters, sortBy: "name" as const, sortDir: "asc" as const };
      const onFiltersChange = vi.fn();

      render(
        <ProjectSearchPanel
          filters={filtersWithSort}
          onFiltersChange={onFiltersChange}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          selectedProjectId={null}
          total={1}
          page={1}
          pageSize={10}
          onPageChange={vi.fn()}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      expect(screen.getByText("Sort: Name A–Z (asc)")).toBeInTheDocument();
    });

    it("removes district filter when chip is clicked", () => {
      const filtersWithDistrict = { ...sampleFilters, district: "Raipur" };
      const onFiltersChange = vi.fn();

      render(
        <ProjectSearchPanel
          filters={filtersWithDistrict}
          onFiltersChange={onFiltersChange}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          selectedProjectId={null}
          total={1}
          page={1}
          pageSize={10}
          onPageChange={vi.fn()}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      const chip = screen.getByRole("button", { name: /Remove District: Raipur filter/i });
      fireEvent.click(chip);
      expect(onFiltersChange).toHaveBeenCalledWith({ district: "" });
    });

    it("removes min score filter when chip is clicked", () => {
      const filtersWithScore = { ...sampleFilters, minOverallScore: 0.5 };
      const onFiltersChange = vi.fn();

      render(
        <ProjectSearchPanel
          filters={filtersWithScore}
          onFiltersChange={onFiltersChange}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          selectedProjectId={null}
          total={1}
          page={1}
          pageSize={10}
          onPageChange={vi.fn()}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      const chip = screen.getByRole("button", { name: /Remove Min score: 0.50 filter/i });
      fireEvent.click(chip);
      expect(onFiltersChange).toHaveBeenCalledWith({ minOverallScore: 0 });
    });

    it("removes search filter when chip is clicked", () => {
      const filtersWithSearch = { ...sampleFilters, nameQuery: "test" };
      const onFiltersChange = vi.fn();

      render(
        <ProjectSearchPanel
          filters={filtersWithSearch}
          onFiltersChange={onFiltersChange}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          selectedProjectId={null}
          total={1}
          page={1}
          pageSize={10}
          onPageChange={vi.fn()}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      const chip = screen.getByRole("button", { name: /Remove Search: "test" filter/i });
      fireEvent.click(chip);
      expect(onFiltersChange).toHaveBeenCalledWith({ nameQuery: "" });
    });

    it("removes sort filter when chip is clicked", () => {
      const filtersWithSort = { ...sampleFilters, sortBy: "name" as const, sortDir: "asc" as const };
      const onFiltersChange = vi.fn();

      render(
        <ProjectSearchPanel
          filters={filtersWithSort}
          onFiltersChange={onFiltersChange}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          selectedProjectId={null}
          total={1}
          page={1}
          pageSize={10}
          onPageChange={vi.fn()}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      const chip = screen.getByRole("button", { name: /Remove Sort: Name A–Z \(asc\) filter/i });
      fireEvent.click(chip);
      expect(onFiltersChange).toHaveBeenCalledWith({
        sortBy: "overall_score",
        sortDir: "desc",
      });
    });
  });

  describe("Pagination Controls", () => {
    it("disables previous button on first page", () => {
      render(
        <ProjectSearchPanel
          filters={sampleFilters}
          onFiltersChange={vi.fn()}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          selectedProjectId={null}
          total={50}
          page={1}
          pageSize={10}
          onPageChange={vi.fn()}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      const prevButton = screen.getByRole("button", { name: /Previous/i });
      expect(prevButton).toBeDisabled();
    });

    it("disables next button on last page", () => {
      render(
        <ProjectSearchPanel
          filters={sampleFilters}
          onFiltersChange={vi.fn()}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          selectedProjectId={null}
          total={10}
          page={1}
          pageSize={10}
          onPageChange={vi.fn()}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      const nextButton = screen.getByRole("button", { name: /Next/i });
      expect(nextButton).toBeDisabled();
    });

    it("calls onPageChange with correct value when clicking next", () => {
      const onPageChange = vi.fn();

      render(
        <ProjectSearchPanel
          filters={sampleFilters}
          onFiltersChange={vi.fn()}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          selectedProjectId={null}
          total={50}
          page={1}
          pageSize={10}
          onPageChange={onPageChange}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      const nextButton = screen.getByRole("button", { name: /Next/i });
      fireEvent.click(nextButton);
      expect(onPageChange).toHaveBeenCalledWith(2);
    });

    it("calls onPageChange with correct value when clicking previous", () => {
      const onPageChange = vi.fn();

      render(
        <ProjectSearchPanel
          filters={sampleFilters}
          onFiltersChange={vi.fn()}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          selectedProjectId={null}
          total={50}
          page={3}
          pageSize={10}
          onPageChange={onPageChange}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      const prevButton = screen.getByRole("button", { name: /Previous/i });
      fireEvent.click(prevButton);
      expect(onPageChange).toHaveBeenCalledWith(2);
    });

    it("disables pagination buttons during loading", () => {
      render(
        <ProjectSearchPanel
          filters={sampleFilters}
          onFiltersChange={vi.fn()}
          projects={sampleProjects}
          loading={true}
          onSelectProject={vi.fn()}
          selectedProjectId={null}
          total={50}
          page={2}
          pageSize={10}
          onPageChange={vi.fn()}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      const prevButton = screen.getByRole("button", { name: /Previous/i });
      const nextButton = screen.getByRole("button", { name: /Next/i });
      expect(prevButton).toBeDisabled();
      expect(nextButton).toBeDisabled();
    });
  });

  describe("Sort Controls", () => {
    it("changes sortBy and sets default direction when sort option is changed", () => {
      const onFiltersChange = vi.fn();

      render(
        <ProjectSearchPanel
          filters={sampleFilters}
          onFiltersChange={onFiltersChange}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          selectedProjectId={null}
          total={1}
          page={1}
          pageSize={10}
          onPageChange={vi.fn()}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      // Find the sort select by its label
      const sortSelect = screen.getByRole("combobox", { name: /Sort by/i });
      fireEvent.change(sortSelect, { target: { value: "name" } });

      expect(onFiltersChange).toHaveBeenCalledWith({
        sortBy: "name",
        sortDir: "asc",
      });
    });

    it("toggles sort direction when direction button is clicked", () => {
      const onFiltersChange = vi.fn();

      render(
        <ProjectSearchPanel
          filters={sampleFilters}
          onFiltersChange={onFiltersChange}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          selectedProjectId={null}
          total={1}
          page={1}
          pageSize={10}
          onPageChange={vi.fn()}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      const toggleButton = screen.getByRole("button", { name: /Toggle sort direction/i });
      fireEvent.click(toggleButton);

      expect(onFiltersChange).toHaveBeenCalledWith({ sortDir: "asc" });
    });
  });

  describe("Hover Behavior", () => {
    beforeEach(() => {
      Element.prototype.scrollIntoView = vi.fn();
    });

    it("triggers onHoverProject when hovering a project card", () => {
      const onHoverProject = vi.fn();

      render(
        <ProjectSearchPanel
          filters={sampleFilters}
          onFiltersChange={vi.fn()}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          onHoverProject={onHoverProject}
          selectedProjectId={null}
          hoveredProjectId={null}
          total={1}
          page={1}
          pageSize={10}
          onPageChange={vi.fn()}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      const projectCard = screen.getByText("Skyline Heights").closest("button");
      expect(projectCard).toBeInTheDocument();

      fireEvent.mouseEnter(projectCard!);
      expect(onHoverProject).toHaveBeenCalledWith(1);

      fireEvent.mouseLeave(projectCard!);
      expect(onHoverProject).toHaveBeenCalledWith(null);
    });

    it("applies hovered class when hoveredProjectId matches project", () => {
      render(
        <ProjectSearchPanel
          filters={sampleFilters}
          onFiltersChange={vi.fn()}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          onHoverProject={vi.fn()}
          selectedProjectId={null}
          hoveredProjectId={1}
          total={1}
          page={1}
          pageSize={10}
          onPageChange={vi.fn()}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      const projectCard = screen.getByText("Skyline Heights").closest("button");
      expect(projectCard).toHaveClass("hovered");
    });

    it("scrolls project into view when hoveredProjectId changes", () => {
      const scrollIntoViewMock = vi.fn();
      Element.prototype.scrollIntoView = scrollIntoViewMock;

      const { rerender } = render(
        <ProjectSearchPanel
          filters={sampleFilters}
          onFiltersChange={vi.fn()}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          onHoverProject={vi.fn()}
          selectedProjectId={null}
          hoveredProjectId={null}
          total={1}
          page={1}
          pageSize={10}
          onPageChange={vi.fn()}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      // Initially no scroll
      expect(scrollIntoViewMock).not.toHaveBeenCalled();

      // Trigger hover by changing hoveredProjectId
      rerender(
        <ProjectSearchPanel
          filters={sampleFilters}
          onFiltersChange={vi.fn()}
          projects={sampleProjects}
          loading={false}
          onSelectProject={vi.fn()}
          onHoverProject={vi.fn()}
          selectedProjectId={null}
          hoveredProjectId={1}
          total={1}
          page={1}
          pageSize={10}
          onPageChange={vi.fn()}
          onResetFilters={vi.fn()}
          defaultFilters={sampleFilters}
        />,
      );

      expect(scrollIntoViewMock).toHaveBeenCalledWith({ behavior: "smooth", block: "nearest" });
    });
  });
});
