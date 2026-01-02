"""Add Phase 0 foundational fields v2

Revision ID: d2ecdf969be7
Revises: g4a5b6c7d8e9
Create Date: 2026-01-02 14:28:14.701783

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd2ecdf969be7'
down_revision: Union[str, Sequence[str], None] = 'g4a5b6c7d8e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 0 Additions."""
    # Additions to projects table
    op.add_column('projects', sa.Column('listing_type', sa.String(length=30), nullable=True))
    op.add_column('projects', sa.Column('property_type', sa.String(length=50), nullable=True))
    op.add_column('projects', sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('projects', sa.Column('featured_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('projects', sa.Column('meta_description', sa.Text(), nullable=True))
    op.add_column('projects', sa.Column('slug', sa.String(length=200), nullable=True))
    op.add_column('projects', sa.Column('stamp_duty_rate', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('projects', sa.Column('registration_rate', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('projects', sa.Column('gst_applicable', sa.Boolean(), nullable=True))
    op.add_column('projects', sa.Column('gst_rate', sa.Numeric(precision=5, scale=2), nullable=True))
    op.create_index(op.f('ix_projects_slug'), 'projects', ['slug'], unique=True)

    # Additions to project_unit_types table
    op.add_column('project_unit_types', sa.Column('base_price_inr', sa.Numeric(precision=14, scale=2), nullable=True))
    op.add_column('project_unit_types', sa.Column('price_per_sqft_carpet', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('project_unit_types', sa.Column('price_per_sqft_super', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('project_unit_types', sa.Column('floor_plan_image_url', sa.String(length=1024), nullable=True))
    op.add_column('project_unit_types', sa.Column('has_3d_view', sa.Boolean(), nullable=True, server_default='false'))


def downgrade() -> None:
    """Downgrade schema - Remove Phase 0 Additions."""
    op.drop_column('project_unit_types', 'has_3d_view')
    op.drop_column('project_unit_types', 'floor_plan_image_url')
    op.drop_column('project_unit_types', 'price_per_sqft_super')
    op.drop_column('project_unit_types', 'price_per_sqft_carpet')
    op.drop_column('project_unit_types', 'base_price_inr')

    op.drop_index(op.f('ix_projects_slug'), table_name='projects')
    op.drop_column('projects', 'gst_rate')
    op.drop_column('projects', 'gst_applicable')
    op.drop_column('projects', 'registration_rate')
    op.drop_column('projects', 'stamp_duty_rate')
    op.drop_column('projects', 'slug')
    op.drop_column('projects', 'meta_description')
    op.drop_column('projects', 'featured_at')
    op.drop_column('projects', 'view_count')
    op.drop_column('projects', 'property_type')
    op.drop_column('projects', 'listing_type')
