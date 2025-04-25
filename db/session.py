from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from tomato.core.settings import SETTINGS


engine = create_async_engine(
    SETTINGS.DB_URI,
    echo=False,
    connect_args={
        "server_settings": {
            "timezone": "Europe/Moscow"  # Указываем нужную временную зону
        }
    }
    )

async_session = async_sessionmaker(
    bind=engine, expire_on_commit=False
)


@asynccontextmanager
async def get_session() -> AsyncSession:
    """Асинхронный контекст сессии."""
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
