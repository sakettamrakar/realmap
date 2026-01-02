"""Add project_media table for Phase 1

Revision ID: 866ddc69ce62
Revises: d2ecdf969be7
Create Date: 2026-01-02 14:30:48.685870

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '866ddc69ce62'
down_revision: Union[str, Sequence[str], None] = 'd2ecdf969be7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add project_media."""
    op.create_table('project_media',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('media_category', sa.Enum('GALLERY', 'FLOOR_PLAN', 'VIDEO', 'VIRTUAL_TOUR', 'BROCHURE', 'OTHER', name='mediacategory'), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=False),
        sa.Column('thumbnail_url', sa.String(length=1024), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_external', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('raw_source', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_project_media_category', 'project_media', ['media_category'], unique=False)
    op.create_index('ix_project_media_project_id', 'project_media', ['project_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Remove project_media."""
    op.drop_index('ix_project_media_project_id', table_name='project_media')
    op.drop_index('ix_project_media_category', table_name='project_media')
    op.drop_table('project_media')
    # Optional: explicitly drop the enum type if needed, but sa.Enum usually handles it
    # op.execute("DROP TYPE mediacategory")
