from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, BOOLEAN
from datetime import datetime
import uuid


class Base(AsyncAttrs, DeclarativeBase):

    __abstract__ = True
    __timestamps__ = True
    __is_updatable__ = True
    __allow_nullable__ = set()

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"
    
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        if not cls.__timestamps__:
            return None
        return mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        if not cls.__timestamps__:
            return None
        if not cls.__is_updatable__:
            return None
        return mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), server_onupdate=func.now())

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if getattr(cls, "__abstract__", False):
            return

        table = getattr(cls, "__table__", None)
        if not table:
            return

        for column in table.columns:

            if column.primary_key:
                continue

            if column.name in cls.__allow_nullable__:
                continue

            column.nullable = False

    

class BaseWithUUId(Base):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
