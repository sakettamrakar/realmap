"""Add floor_plan_data column to project_artifacts

Revision ID: c0a1b2c3d4e5
Revises: b98723aa80d3
Create Date: 2025-12-11 13:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c0a1b2c3d4e5'
down_revision: Union[str, None] = 'b98723aa80d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('project_artifacts', sa.Column('floor_plan_data', sa.JSON(), nullable=True, comment='Structured room dimensions and layout data'))


def downgrade() -> None:
    op.drop_column('project_artifacts', 'floor_plan_data')
