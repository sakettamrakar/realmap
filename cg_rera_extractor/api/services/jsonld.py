"""
JSON-LD Generator Service (Point 15).

Generates Schema.org structured data for SEO.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from cg_rera_extractor.db import Project, ProjectScores, Promoter
from cg_rera_extractor.api.schemas_api import (
    SchemaOrgProduct,
    SchemaOrgOffer,
    SchemaOrgAggregateRating,
    SchemaOrgGeoCoordinates,
    SchemaOrgAddress,
    SchemaOrgOrganization,
)


def _format_price_range(min_price: float | None, max_price: float | None) -> str | None:
    """Format price range as readable string."""
    if not min_price and not max_price:
        return None
    
    def format_amount(amt: float) -> str:
        if amt >= 10_000_000:  # 1 Crore
            return f"₹{amt / 10_000_000:.2f}Cr"
        elif amt >= 100_000:  # 1 Lakh
            return f"₹{amt / 100_000:.2f}L"
        else:
            return f"₹{amt:,.0f}"
    
    if min_price and max_price:
        return f"{format_amount(min_price)} - {format_amount(max_price)}"
    elif min_price:
        return f"From {format_amount(min_price)}"
    elif max_price:
        return f"Up to {format_amount(max_price)}"
    
    return None


def _score_to_rating(score: float | None, max_score: float = 100) -> float | None:
    """Convert internal score (0-100) to Schema.org rating (0-5)."""
    if score is None:
        return None
    # Normalize to 0-5 scale
    return round((float(score) / max_score) * 5, 1)


def _get_availability_status(status: str | None) -> str:
    """Map project status to Schema.org availability."""
    if not status:
        return "https://schema.org/PreOrder"
    
    status_lower = status.lower()
    if "completed" in status_lower or "ready" in status_lower:
        return "https://schema.org/InStock"
    elif "sold" in status_lower:
        return "https://schema.org/SoldOut"
    elif "construction" in status_lower or "ongoing" in status_lower:
        return "https://schema.org/PreOrder"
    else:
        return "https://schema.org/PreOrder"


def generate_project_jsonld(
    project: Project,
    scores: ProjectScores | None = None,
    pricing: dict[str, Any] | None = None,
    base_url: str = "https://example.com",
) -> SchemaOrgProduct:
    """
    Generate Schema.org Product/Residence structured data for a project.
    
    This data can be embedded in HTML pages for SEO benefits.
    """
    # Build geo coordinates
    geo = None
    if project.latitude and project.longitude:
        geo = SchemaOrgGeoCoordinates(
            latitude=float(project.latitude),
            longitude=float(project.longitude),
        )
    
    # Build address
    address = SchemaOrgAddress(
        streetAddress=project.full_address or project.normalized_address,
        addressLocality=project.tehsil or project.village_or_locality,
        addressRegion=project.district,
        postalCode=project.pincode,
        addressCountry="IN",
    )
    
    # Build developer/brand (from promoters)
    brand = None
    if project.promoters:
        primary_promoter = project.promoters[0]
        brand = SchemaOrgOrganization(
            name=primary_promoter.promoter_name,
            url=primary_promoter.website,
        )
    
    # Build pricing offer
    offers = None
    if pricing:
        min_price = pricing.get("min_price_total")
        max_price = pricing.get("max_price_total")
        
        offers = SchemaOrgOffer(
            priceCurrency="INR",
            price=min_price,
            priceRange=_format_price_range(min_price, max_price),
            availability=_get_availability_status(project.status),
            validFrom=project.approved_date.isoformat() if project.approved_date else None,
        )
    
    # Build aggregate rating from scores
    aggregate_rating = None
    if scores and scores.overall_score is not None:
        rating_value = _score_to_rating(float(scores.overall_score))
        if rating_value:
            aggregate_rating = SchemaOrgAggregateRating(
                ratingValue=rating_value,
                bestRating=5,
                worstRating=1,
                ratingCount=1,  # Based on algorithmic score, not user reviews
            )
    
    # Build description
    description_parts = []
    if project.status:
        description_parts.append(f"Status: {project.status}")
    if project.district:
        description_parts.append(f"Located in {project.district}")
    if project.tehsil:
        description_parts.append(project.tehsil)
    
    description = ". ".join(description_parts) if description_parts else None
    
    # Collect images (from artifacts if available)
    images = []
    if hasattr(project, "artifacts"):
        for artifact in project.artifacts:
            if artifact.source_url and artifact.file_format in ("jpg", "jpeg", "png", "webp"):
                images.append(artifact.source_url)
    
    # Build additional properties for real estate specific data
    additional_properties = []
    
    if project.approved_date:
        additional_properties.append({
            "@type": "PropertyValue",
            "name": "RERA Registration Date",
            "value": project.approved_date.isoformat(),
        })
    
    if project.proposed_end_date:
        additional_properties.append({
            "@type": "PropertyValue",
            "name": "Expected Completion",
            "value": project.proposed_end_date.isoformat(),
        })
    
    if project.rera_registration_number:
        additional_properties.append({
            "@type": "PropertyValue",
            "name": "RERA Registration Number",
            "value": project.rera_registration_number,
        })
    
    return SchemaOrgProduct(
        name=project.project_name,
        description=description,
        sku=project.rera_registration_number,
        productID=str(project.id),
        url=f"{base_url}/projects/{project.id}",
        image=images if images else None,
        geo=geo,
        address=address,
        brand=brand,
        manufacturer=brand,  # Same as brand for real estate
        offers=offers,
        aggregateRating=aggregate_rating,
        additionalProperty=additional_properties if additional_properties else None,
    )


def generate_project_jsonld_from_db(
    db: Session,
    project_id: int,
    base_url: str = "https://example.com",
) -> SchemaOrgProduct | None:
    """
    Fetch a project and generate its JSON-LD.
    
    Convenience function that handles database queries.
    """
    from sqlalchemy.orm import selectinload
    
    project = (
        db.query(Project)
        .options(
            selectinload(Project.promoters),
            selectinload(Project.score),
            selectinload(Project.pricing_snapshots),
            selectinload(Project.artifacts),
        )
        .filter(Project.id == project_id)
        .first()
    )
    
    if not project:
        return None
    
    # Get pricing info
    pricing = None
    if project.pricing_snapshots:
        active = [s for s in project.pricing_snapshots if s.is_active]
        if active:
            min_prices = [float(s.min_price_total) for s in active if s.min_price_total]
            max_prices = [float(s.max_price_total) for s in active if s.max_price_total]
            pricing = {
                "min_price_total": min(min_prices) if min_prices else None,
                "max_price_total": max(max_prices) if max_prices else None,
            }
    
    return generate_project_jsonld(
        project=project,
        scores=project.score,
        pricing=pricing,
        base_url=base_url,
    )


__all__ = [
    "generate_project_jsonld",
    "generate_project_jsonld_from_db",
]
