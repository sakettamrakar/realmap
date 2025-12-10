"""Database layer for CG RERA projects."""

from .base import Base, get_engine, get_session_local
from .migrations import MIGRATIONS, apply_migrations

# Core models
from .models import (
    BankAccount,
    Building,
    LandParcel,
    Project,
    ProjectAmenityStats,
    ProjectArtifact,
    ProjectDocument,
    ProjectScores,
    ProjectLocation,
    ProjectPricingSnapshot,
    ProjectUnitType,
    Promoter,
    QuarterlyUpdate,
    UnitType,
    # Point 28 & 29: Ops Standard
    DataProvenance,
    IngestionAudit,
)

# Enhanced models (10-Point Enhancement Standard)
from .models_enhanced import (
    Developer,
    DeveloperProject,
    Unit,
    ProjectPossessionTimeline,
    AmenityCategory,
    Amenity,
    AmenityType,
    ProjectAmenity,
    TransactionHistory,
)

# Discovery & Trust models (Points 24-26)
from .models_discovery import (
    Tag,
    ProjectTag,
    ReraVerification,
    Landmark,
    ProjectLandmark,
)

# Enums
from .enums import (
    AreaUnit,
    ProjectPhase,
    AmenityCategoryType,
    UnitStatus,
    TagCategory,
    ReraVerificationStatus,
)

from .loader import load_all_runs, load_run_into_db

__all__ = [
    # Base
    "Base",
    "get_engine",
    "get_session_local",
    
    # Core models
    "AmenityPOI",
    "BankAccount",
    "Building",
    "LandParcel",
    "Project", 
    "ProjectArtifact",
    "ProjectAmenityStats",
    "ProjectDocument",
    "ProjectPricingSnapshot",
    "ProjectScores",
    "ProjectLocation",
    "ProjectUnitType",
    "Promoter",
    "QuarterlyUpdate",
    "UnitType",
    # Point 28 & 29: Ops Standard
    "DataProvenance",
    "IngestionAudit",
    
    # Enhanced models (10-Point Enhancement Standard)
    "Developer",
    "DeveloperProject",
    "Unit",
    "ProjectPossessionTimeline",
    "AmenityCategory",
    "Amenity",
    "AmenityType",
    "ProjectAmenity",
    "TransactionHistory",
    
    # Discovery & Trust models (Points 24-26)
    "Tag",
    "ProjectTag",
    "ReraVerification",
    "Landmark",
    "ProjectLandmark",
    
    # Enums
    "AreaUnit",
    "ProjectPhase",
    "AmenityCategoryType",
    "UnitStatus",
    "TagCategory",
    "ReraVerificationStatus",
    
    # Utilities
    "MIGRATIONS",
    "apply_migrations",
    "load_all_runs",
    "load_run_into_db",
]
