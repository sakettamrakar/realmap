"""Phase 1 Final Additions

Revision ID: 7cc76b883018
Revises: 866ddc69ce62
Create Date: 2026-01-02 14:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7cc76b883018'
down_revision: Union[str, Sequence[str], None] = '866ddc69ce62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add Phase 1 Enhanced Tables."""
    
    # --- Amenity Taxonomy ---
    op.create_table('amenity_categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('lifestyle_weight', sa.Numeric(precision=4, scale=2), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_amenity_category_code')
    )

    op.create_table('amenities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('lifestyle_points', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['amenity_categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_amenity_code')
    )
    op.create_index('ix_amenities_category_id', 'amenities', ['category_id'], unique=False)

    op.create_table('amenity_types',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('amenity_id', sa.Integer(), nullable=False),
        sa.Column('variant_code', sa.String(length=50), nullable=False),
        sa.Column('variant_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('premium_multiplier', sa.Numeric(precision=3, scale=2), nullable=True, server_default='1.0'),
        sa.ForeignKeyConstraint(['amenity_id'], ['amenities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('amenity_id', 'variant_code', name='uq_amenity_variant')
    )

    op.create_table('project_amenities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('amenity_type_id', sa.Integer(), nullable=False),
        sa.Column('onsite_details', sa.JSON(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['amenity_type_id'], ['amenity_types.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'amenity_type_id', name='uq_project_amenity_type')
    )
    op.create_index('ix_project_amenities_project_id', 'project_amenities', ['project_id'], unique=False)

    # --- Developers & Timelines ---
    op.create_table('developers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.String(length=1024), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('total_projects', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('experience_years', sa.Integer(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_developers_slug')
    )

    op.create_table('developer_projects',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('developer_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['developer_id'], ['developers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('developer_id', 'project_id', name='uq_developer_project')
    )

    op.create_table('project_possession_timelines',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('event_name', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=True),
        sa.Column('original_date', sa.Date(), nullable=True),
        sa.Column('revised_date', sa.Date(), nullable=True),
        sa.Column('actual_date', sa.Date(), nullable=True),
        sa.Column('delay_months', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # --- Tags --
    op.create_table('tags',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.Enum('PROXIMITY', 'INFRASTRUCTURE', 'INVESTMENT', 'LIFESTYLE', 'CERTIFICATION', name='tagcategory'), nullable=False),
        sa.Column('is_auto_generated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('auto_rule_json', sa.JSON(), nullable=True),
        sa.Column('icon_emoji', sa.String(length=10), nullable=True),
        sa.Column('color_hex', sa.String(length=7), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_tags_slug')
    )
    op.create_index('ix_tags_category', 'tags', ['category'], unique=False)

    op.create_table('project_tags',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('is_auto_applied', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('confidence_score', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('applied_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'tag_id', name='uq_project_tag')
    )

    # --- Landmarks ---
    op.create_table('landmarks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('alternate_names', sa.JSON(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('subcategory', sa.String(length=50), nullable=True),
        sa.Column('lat', sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column('lon', sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column('city', sa.String(length=128), nullable=True),
        sa.Column('importance_score', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_landmarks_slug')
    )
    op.create_index('ix_landmarks_lat_lon', 'landmarks', ['lat', 'lon'], unique=False)

    op.create_table('project_landmarks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('landmark_id', sa.Integer(), nullable=False),
        sa.Column('distance_km', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('driving_time_mins', sa.Integer(), nullable=True),
        sa.Column('is_highlighted', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['landmark_id'], ['landmarks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'landmark_id', name='uq_project_landmark')
    )


def downgrade() -> None:
    """Downgrade schema - Remove all Phase 1 Enhanced Tables."""
    op.drop_table('project_landmarks')
    op.drop_table('landmarks')
    op.drop_table('project_tags')
    op.drop_table('tags')
    op.drop_table('project_possession_timelines')
    op.drop_table('developer_projects')
    op.drop_table('developers')
    op.drop_table('project_amenities')
    op.drop_table('amenity_types')
    op.drop_table('amenities')
    op.drop_table('amenity_categories')
