"""new field

Revision ID: d214d97fefc9
Revises: 64f29bcf0622
Create Date: 2024-11-23 22:10:21.153825

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd214d97fefc9'
down_revision: Union[str, None] = '64f29bcf0622'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('games', sa.Column('current_question_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'games', 'questions', ['current_question_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'games', type_='foreignkey')
    op.drop_column('games', 'current_question_id')
    # ### end Alembic commands ###
