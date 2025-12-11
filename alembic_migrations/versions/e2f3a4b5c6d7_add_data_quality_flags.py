"""Add data_quality_flags table

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2025-12-11 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e2f3a4b5c6d7'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create data_quality_flags table
    op.create_table(
        'data_quality_flags',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('column_name', sa.String(length=64), nullable=False),
        sa.Column('outlier_value', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('anomaly_score', sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column('is_reviewed', sa.Boolean(), nullable=False, default=False),
        sa.Column('review_comment', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_data_quality_flags_project_id', 'data_quality_flags', ['project_id'], unique=False)
    op.create_index('ix_data_quality_flags_column_name', 'data_quality_flags', ['column_name'], unique=False)
    op.create_index('ix_data_quality_flags_is_reviewed', 'data_quality_flags', ['is_reviewed'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_data_quality_flags_is_reviewed', table_name='data_quality_flags')
    op.drop_index('ix_data_quality_flags_column_name', table_name='data_quality_flags')
    op.drop_index('ix_data_quality_flags_project_id', table_name='data_quality_flags')
    op.drop_table('data_quality_flags')
