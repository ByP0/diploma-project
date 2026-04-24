"""add user profile fields and avatar

Revision ID: b7c2d1e4f903
Revises: f2a4c8d9e501
Create Date: 2026-04-24 16:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b7c2d1e4f903"
down_revision: Union[str, Sequence[str], None] = "f2a4c8d9e501"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.VARCHAR(length=255), nullable=True))
    op.add_column("users", sa.Column("avatar_image_id", sa.VARCHAR(length=24), nullable=True))
    op.create_check_constraint(
        "ck_users_avatar_image_id_length",
        "users",
        "avatar_image_id IS NULL OR char_length(avatar_image_id) = 24",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_avatar_image_id_length", "users", type_="check")
    op.drop_column("users", "avatar_image_id")
    op.drop_column("users", "name")
