"""Service layer for project API endpoints."""

from .detail import fetch_project_detail
from .map import fetch_map_projects
from .search import search_projects
from .analytics import fetch_price_trends
from .access import process_brochure_access, SignedUrlGenerator
from .jsonld import generate_project_jsonld, generate_project_jsonld_from_db

__all__ = [
    "search_projects",
    "fetch_project_detail",
    "fetch_map_projects",
    "fetch_price_trends",
    "process_brochure_access",
    "SignedUrlGenerator",
    "generate_project_jsonld",
    "generate_project_jsonld_from_db",
]
