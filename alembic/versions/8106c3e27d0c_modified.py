"""modified

Revision ID: 8106c3e27d0c
Revises: d214d97fefc9
Create Date: 2024-11-25 22:26:17.845400

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8106c3e27d0c'
down_revision: Union[str, None] = 'd214d97fefc9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('updates',
    sa.Column('offset', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('offset')
    )
    op.drop_table('chat_updates')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chat_updates',
    sa.Column('chat_id', sa.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('offset', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], name='chat_updates_chat_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('chat_id', name='chat_updates_pkey')
    )
    op.drop_table('updates')
    # ### end Alembic commands ###
