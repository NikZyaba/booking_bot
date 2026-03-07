"""upgrade 'Order' table

Revision ID: 76c8201586c1
Revises: b111b713147f
Create Date: 2026-03-07 10:00:43.933564

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76c8201586c1'
down_revision: Union[str, Sequence[str], None] = 'b111b713147f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
