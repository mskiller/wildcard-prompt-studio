"""Fix prompt and image foreign keys to allow cascading and nullification

Revision ID: 7b9e11fc3421
Revises: 88d06ead4851
Create Date: 2026-09-06 03:02:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7b9e11fc3421'
down_revision: Union[str, Sequence[str], None] = '88d06ead4851'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Allow images to exist independently without a prompt
    op.alter_column('images', 'prompt_id', nullable=True)

    # 2. Update images -> prompts foreign key to ON DELETE SET NULL
    op.drop_constraint('images_prompt_id_fkey', 'images', type_='foreignkey')
    op.create_foreign_key(
        'images_prompt_id_fkey',
        'images',
        'prompts',
        ['prompt_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # 3. Update prompt_tags foreign keys to ON DELETE CASCADE
    op.drop_constraint('prompt_tags_prompt_id_fkey', 'prompt_tags', type_='foreignkey')
    op.create_foreign_key(
        'prompt_tags_prompt_id_fkey',
        'prompt_tags',
        'prompts',
        ['prompt_id'],
        ['id'],
        ondelete='CASCADE'
    )

    op.drop_constraint('prompt_tags_tag_id_fkey', 'prompt_tags', type_='foreignkey')
    op.create_foreign_key(
        'prompt_tags_tag_id_fkey',
        'prompt_tags',
        'tags',
        ['tag_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    op.drop_constraint('prompt_tags_tag_id_fkey', 'prompt_tags', type_='foreignkey')
    op.create_foreign_key(
        'prompt_tags_tag_id_fkey',
        'prompt_tags',
        'tags',
        ['tag_id'],
        ['id']
    )

    op.drop_constraint('prompt_tags_prompt_id_fkey', 'prompt_tags', type_='foreignkey')
    op.create_foreign_key(
        'prompt_tags_prompt_id_fkey',
        'prompt_tags',
        'prompts',
        ['prompt_id'],
        ['id']
    )

    op.drop_constraint('images_prompt_id_fkey', 'images', type_='foreignkey')
    op.create_foreign_key(
        'images_prompt_id_fkey',
        'images',
        'prompts',
        ['prompt_id'],
        ['id']
    )
    op.alter_column('images', 'prompt_id', nullable=False)
