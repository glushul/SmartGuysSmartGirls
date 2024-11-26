"""modified

Revision ID: b413cd0952ac
Revises: 244c5b790c0d
Create Date: 2024-11-22 22:25:36.329547

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b413cd0952ac'
down_revision: Union[str, None] = '244c5b790c0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chat_updates',
    sa.Column('chat_id', sa.BigInteger(), nullable=False),
    sa.Column('offset', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['offset'], ['chats.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('chat_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('chat_updates')
    # ### end Alembic commands ###