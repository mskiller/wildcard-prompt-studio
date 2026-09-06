"""Update knowledge documents for 384-dim vector and add gallery metadata to images

Revision ID: 20260906_rag_gallery_upgrade
Revises: 7b9e11fc3421
Create Date: 2026-09-06 03:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector


# revision identifiers, used by Alembic.
revision: str = '20260906_rag_gallery_upgrade'
down_revision: Union[str, Sequence[str], None] = '7b9e11fc3421'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update knowledge_documents table
    # Clear existing embeddings before altering dimension to prevent casting errors on populated tables
    op.execute("UPDATE knowledge_documents SET embedding = NULL")
    op.alter_column(
        'knowledge_documents',
        'embedding',
        existing_type=pgvector.sqlalchemy.Vector(1536),
        type_=pgvector.sqlalchemy.Vector(384),
        existing_nullable=True
    )
    op.add_column('knowledge_documents', sa.Column('category', sa.String(), server_default='general', nullable=True))
    op.create_index(op.f('ix_knowledge_documents_category'), 'knowledge_documents', ['category'], unique=False)
    op.create_index(op.f('ix_knowledge_documents_title'), 'knowledge_documents', ['title'], unique=False)
    op.add_column('knowledge_documents', sa.Column('tags', sa.Text(), server_default='[]', nullable=True))
    op.add_column('knowledge_documents', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('knowledge_documents', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))

    # 2. Update images table
    op.add_column('images', sa.Column('is_favorite', sa.Boolean(), server_default=sa.text('false'), nullable=True))
    op.create_index(op.f('ix_images_is_favorite'), 'images', ['is_favorite'], unique=False)
    op.add_column('images', sa.Column('rating', sa.Integer(), server_default=sa.text('0'), nullable=True))
    op.create_index(op.f('ix_images_rating'), 'images', ['rating'], unique=False)
    op.add_column('images', sa.Column('aesthetic_score', sa.Float(), nullable=True))
    op.create_index(op.f('ix_images_aesthetic_score'), 'images', ['aesthetic_score'], unique=False)
    op.create_index(op.f('ix_images_created_at'), 'images', ['created_at'], unique=False)


def downgrade() -> None:
    # 1. Revert images table
    op.drop_index(op.f('ix_images_created_at'), table_name='images')
    op.drop_index(op.f('ix_images_aesthetic_score'), table_name='images')
    op.drop_column('images', 'aesthetic_score')
    op.drop_index(op.f('ix_images_rating'), table_name='images')
    op.drop_column('images', 'rating')
    op.drop_index(op.f('ix_images_is_favorite'), table_name='images')
    op.drop_column('images', 'is_favorite')

    # 2. Revert knowledge_documents table
    op.drop_column('knowledge_documents', 'updated_at')
    op.drop_column('knowledge_documents', 'created_at')
    op.drop_column('knowledge_documents', 'tags')
    op.drop_index(op.f('ix_knowledge_documents_title'), table_name='knowledge_documents')
    op.drop_index(op.f('ix_knowledge_documents_category'), table_name='knowledge_documents')
    op.drop_column('knowledge_documents', 'category')
    op.execute("UPDATE knowledge_documents SET embedding = NULL")
    op.alter_column(
        'knowledge_documents',
        'embedding',
        existing_type=pgvector.sqlalchemy.Vector(384),
        type_=pgvector.sqlalchemy.Vector(1536),
        existing_nullable=True
    )
