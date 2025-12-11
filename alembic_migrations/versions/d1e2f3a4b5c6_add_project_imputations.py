"""Add project_imputations table

Revision ID: d1e2f3a4b5c6
Revises: c0a1b2c3d4e5
Create Date: 2025-12-11 14:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c0a1b2c3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create project_imputations table
    op.create_table(
        'project_imputations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('imputed_data', sa.JSON(), nullable=True, comment="Key-value pairs of imputed fields"),
        sa.Column('confidence_score', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=True, comment="Algorithm used"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_project_imputations_model_name', 'project_imputations', ['model_name'], unique=False)
    op.create_index('ix_project_imputations_project_id', 'project_imputations', ['project_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_project_imputations_project_id', table_name='project_imputations')
    op.drop_index('ix_project_imputations_model_name', table_name='project_imputations')
    op.drop_table('project_imputations')
