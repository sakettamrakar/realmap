"""Add project_embeddings table for semantic search

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2025-12-11 16:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f3a4b5c6d7e8'
down_revision: Union[str, None] = 'e2f3a4b5c6d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create project_embeddings table without pgvector dependency
    # The embedding_data JSON column stores embeddings as arrays
    # If pgvector is available, a native vector column can be added later
    op.create_table(
        'project_embeddings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('embedding_data', sa.JSON(), nullable=True, comment="Vector embedding as JSON array"),
        sa.Column('text_content', sa.Text(), nullable=True, comment="Source text used for embedding"),
        sa.Column('model_name', sa.String(length=100), nullable=True, comment="Embedding model used"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id')
    )
    op.create_index('ix_project_embeddings_project_id', 'project_embeddings', ['project_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_project_embeddings_project_id', table_name='project_embeddings')
    op.drop_table('project_embeddings')
