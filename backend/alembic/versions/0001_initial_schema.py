"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-07 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

from app.models.base import Base
import app.models  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
