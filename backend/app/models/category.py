from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import SMALLINT, VARCHAR

from app.models.base import Base


class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(SMALLINT, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(VARCHAR(100))
    slug: Mapped[str] = mapped_column(VARCHAR(100))