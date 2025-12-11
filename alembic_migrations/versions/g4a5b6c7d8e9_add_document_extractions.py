"""Add document_extractions and document_downloads tables

Revision ID: g4a5b6c7d8e9
Revises: f3a4b5c6d7e8
Create Date: 2025-12-11 17:00:00.000000

Tables created:
- document_extractions: Stores PDF extraction results with structured metadata
- document_downloads: Tracks PDF download status and local file paths

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'g4a5b6c7d8e9'
down_revision: Union[str, Sequence[str], None] = 'f3a4b5c6d7e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create document_extractions and document_downloads tables."""
    
    # Create document_extractions table
    op.create_table(
        'document_extractions',
        # Primary Key
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        
        # Foreign Keys
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=True),
        
        # File Information
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        
        # Document Classification
        sa.Column('document_type', sa.String(length=50), nullable=True),
        sa.Column('document_type_confidence', sa.Float(), nullable=True),
        
        # Extracted Text
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('text_length', sa.Integer(), nullable=True),
        
        # Structured Metadata (JSON)
        sa.Column('extracted_metadata', sa.JSON(), nullable=True),
        
        # Key Extracted Fields (denormalized for querying)
        sa.Column('approval_number', sa.String(length=100), nullable=True),
        sa.Column('approval_date', sa.String(length=50), nullable=True),
        sa.Column('validity_date', sa.String(length=50), nullable=True),
        sa.Column('issuing_authority', sa.String(length=255), nullable=True),
        sa.Column('total_area_sqft', sa.Float(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('floor_count', sa.Integer(), nullable=True),
        sa.Column('unit_count', sa.Integer(), nullable=True),
        sa.Column('summary', sa.String(length=1000), nullable=True),
        
        # Processing Metadata
        sa.Column('processor_name', sa.String(length=50), nullable=False),
        sa.Column('processor_version', sa.String(length=20), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        
        # Status
        sa.Column('success', sa.Boolean(), default=True, nullable=True),
        sa.Column('error', sa.String(length=500), nullable=True),
        sa.Column('warnings', sa.JSON(), nullable=True),
        
        # Timestamps
        sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        
        # Constraints
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['project_documents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for document_extractions
    op.create_index('ix_document_extractions_project_id', 'document_extractions', ['project_id'], unique=False)
    op.create_index('ix_document_extractions_document_id', 'document_extractions', ['document_id'], unique=False)
    op.create_index('ix_document_extractions_document_type', 'document_extractions', ['document_type'], unique=False)
    op.create_index('ix_document_extractions_processor_name', 'document_extractions', ['processor_name'], unique=False)
    
    # Create document_downloads table
    op.create_table(
        'document_downloads',
        # Primary Key
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        
        # Foreign Keys
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=True),
        
        # Source Information
        sa.Column('source_url', sa.String(length=1024), nullable=False),
        sa.Column('document_name', sa.String(length=255), nullable=True),
        
        # Local File Information
        sa.Column('local_path', sa.String(length=1024), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('content_type', sa.String(length=100), nullable=True),
        
        # Download Status
        sa.Column('download_status', sa.String(length=20), nullable=False, default='pending'),
        sa.Column('download_error', sa.String(length=500), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0, nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('downloaded_at', sa.DateTime(timezone=True), nullable=True),
        
        # Constraints
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['project_documents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for document_downloads
    op.create_index('ix_document_downloads_project_id', 'document_downloads', ['project_id'], unique=False)
    op.create_index('ix_document_downloads_download_status', 'document_downloads', ['download_status'], unique=False)


def downgrade() -> None:
    """Drop document_extractions and document_downloads tables."""
    
    # Drop document_downloads
    op.drop_index('ix_document_downloads_download_status', table_name='document_downloads')
    op.drop_index('ix_document_downloads_project_id', table_name='document_downloads')
    op.drop_table('document_downloads')
    
    # Drop document_extractions
    op.drop_index('ix_document_extractions_processor_name', table_name='document_extractions')
    op.drop_index('ix_document_extractions_document_type', table_name='document_extractions')
    op.drop_index('ix_document_extractions_document_id', table_name='document_extractions')
    op.drop_index('ix_document_extractions_project_id', table_name='document_extractions')
    op.drop_table('document_extractions')
