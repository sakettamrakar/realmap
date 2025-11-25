"""Service layer for project API endpoints."""

from .detail import fetch_project_detail
from .map import fetch_map_projects
from .search import search_projects

__all__ = ["search_projects", "fetch_project_detail", "fetch_map_projects"]
