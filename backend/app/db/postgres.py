from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import setting


class DataBase:
    def __init__(self, url: str, echo: bool):
        self._engine = create_async_engine(
            url=url,
            echo=echo
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False
        )

    async def get_session(self):
        async with self._session_factory() as session:
            try:
                yield session
            finally:
                await session.close()


db_postgres = DataBase(
    url=setting.postgres_url,
    echo=setting.postgres_echo
)
