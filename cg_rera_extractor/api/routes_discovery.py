"""
API Discovery Routes (Point 16).

Provides API metadata and resource discovery for developers.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from cg_rera_extractor.api.schemas_api import (
    ApiMetaResponse,
    ResourceEndpoint,
)

router = APIRouter(tags=["discovery"])

# Track server start time for uptime calculation
_SERVER_START_TIME = time.time()

# API version - should match app.py
API_VERSION = "1.0.0"


def _get_resource_endpoints() -> list[ResourceEndpoint]:
    """Return list of all available API resources."""
    return [
        # Projects
        ResourceEndpoint(
            name="Project Search",
            path="/projects/search",
            methods=["GET"],
            description="Search projects with filters (location, scores, price, amenities)",
            requires_auth=False,
        ),
        ResourceEndpoint(
            name="Project Detail",
            path="/projects/{identifier}",
            methods=["GET"],
            description="Get project details by ID or RERA number. Accepts project_id or rera_id.",
            requires_auth=False,
        ),
        ResourceEndpoint(
            name="Project Map Pins",
            path="/projects/map",
            methods=["GET"],
            description="Get lightweight project pins for map rendering",
            requires_auth=False,
        ),
        ResourceEndpoint(
            name="Project Media",
            path="/projects/{id}/media",
            methods=["GET"],
            description="Get all media assets (gallery, floorplans, videos) for a project",
            requires_auth=False,
        ),
        
        # Analytics
        ResourceEndpoint(
            name="Price Trends",
            path="/analytics/price-trends",
            methods=["GET"],
            description="Get historical price trend data for a project or locality",
            requires_auth=False,
        ),
        ResourceEndpoint(
            name="Price Trends Compare",
            path="/analytics/price-trends/compare",
            methods=["GET"],
            description="Compare price trends across multiple entities",
            requires_auth=False,
        ),
        
        # Access Control
        ResourceEndpoint(
            name="Brochure Access",
            path="/access/brochure",
            methods=["POST"],
            description="Request brochure download (requires lead capture)",
            requires_auth=False,
        ),
        ResourceEndpoint(
            name="Brochure Availability",
            path="/access/brochure/{project_id}/available",
            methods=["GET"],
            description="Check if brochure is available for a project",
            requires_auth=False,
        ),
        
        # Legacy/Compatibility
        ResourceEndpoint(
            name="List Projects (Legacy)",
            path="/projects",
            methods=["GET"],
            description="List projects with basic filters. Use /projects/search for advanced search.",
            requires_auth=False,
            deprecated=True,
        ),
        ResourceEndpoint(
            name="Project by RERA (Legacy)",
            path="/projects/{state_code}/{rera_registration_number}",
            methods=["GET"],
            description="Get project by state code and RERA number. Use /projects/{identifier} instead.",
            requires_auth=False,
            deprecated=True,
        ),
        
        # Discovery & Trust Layer (Points 24-26)
        ResourceEndpoint(
            name="Faceted Tags",
            path="/discovery/tags/faceted",
            methods=["GET"],
            description="Get tags organized by category with project counts for faceted search UI",
            requires_auth=False,
        ),
        ResourceEndpoint(
            name="Project Tags",
            path="/discovery/projects/{project_id}/tags",
            methods=["GET"],
            description="Get all tags assigned to a specific project",
            requires_auth=False,
        ),
        ResourceEndpoint(
            name="Trust Badge",
            path="/discovery/projects/{project_id}/trust-badge",
            methods=["GET"],
            description="Get RERA verification trust badge for a project",
            requires_auth=False,
        ),
        ResourceEndpoint(
            name="Project Verification",
            path="/discovery/projects/{project_id}/verification",
            methods=["GET"],
            description="Get detailed RERA verification status and history",
            requires_auth=False,
        ),
        ResourceEndpoint(
            name="Nearby Landmarks",
            path="/discovery/projects/{project_id}/landmarks",
            methods=["GET"],
            description="Get landmarks near a project with distances",
            requires_auth=False,
        ),
        ResourceEndpoint(
            name="Projects Near Landmark",
            path="/discovery/landmarks/{slug}/projects",
            methods=["GET"],
            description="Get projects near a specific landmark",
            requires_auth=False,
        ),
        ResourceEndpoint(
            name="Full Discovery Data",
            path="/discovery/projects/{project_id}/full",
            methods=["GET"],
            description="Get all discovery data (trust badge, tags, landmarks) in one call",
            requires_auth=False,
        ),
        
        # Admin
        ResourceEndpoint(
            name="Project Inspector",
            path="/admin/project/{project_id}/inspect",
            methods=["GET"],
            description="Internal: Get detailed project inspection data with artifacts",
            requires_auth=True,
        ),
        
        # System
        ResourceEndpoint(
            name="Health Check",
            path="/health",
            methods=["GET"],
            description="API health/readiness probe",
            requires_auth=False,
        ),
        ResourceEndpoint(
            name="API Metadata",
            path="/api/meta",
            methods=["GET"],
            description="API discovery endpoint listing all available resources",
            requires_auth=False,
        ),
    ]


@router.get("/api/meta", response_model=ApiMetaResponse)
def get_api_metadata(request: Request):
    """
    API Discovery Endpoint.
    
    Returns metadata about the API including all available endpoints.
    Useful for:
    - API documentation generation
    - Client SDK generation
    - Crawler/bot discovery
    - Health monitoring systems
    
    ## Response
    ```json
    {
        "api_name": "CG RERA Projects API",
        "api_version": "1.0.0",
        "base_url": "https://api.example.com",
        "documentation_url": "https://docs.example.com",
        "resources": [
            {
                "name": "Project Search",
                "path": "/projects/search",
                "methods": ["GET"],
                "description": "Search projects...",
                "requires_auth": false,
                "deprecated": false,
                "version": "1.0"
            }
        ],
        "rate_limit": 100,
        "status": "healthy",
        "uptime_seconds": 86400
    }
    ```
    """
    # Determine base URL from request
    base_url = str(request.base_url).rstrip("/")
    
    # Calculate uptime
    uptime_seconds = int(time.time() - _SERVER_START_TIME)
    
    return ApiMetaResponse(
        api_name="CG RERA Projects API",
        api_version=API_VERSION,
        base_url=base_url,
        documentation_url=f"{base_url}/docs",  # FastAPI's built-in docs
        resources=_get_resource_endpoints(),
        rate_limit=100,  # Requests per minute
        status="healthy",
        uptime_seconds=uptime_seconds,
    )


@router.get("/api/version")
def get_api_version():
    """
    Simple version endpoint.
    
    Returns just the API version for quick checks.
    """
    return {
        "version": API_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


__all__ = ["router"]
