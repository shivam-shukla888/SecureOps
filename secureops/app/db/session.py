import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

def get_async_db_url() -> str:
    raw_url = (settings.DATABASE_URL or "").strip("\"' \t\r\n")
    if raw_url.startswith("DATABASE_URL="):
        raw_url = raw_url[len("DATABASE_URL="):].strip("\"' \t\r\n")
    if raw_url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + raw_url[len("postgresql://"):]
    elif raw_url.startswith("postgres://"):
        return "postgresql+asyncpg://" + raw_url[len("postgres://"):]
    return raw_url

engine = create_async_engine(
    get_async_db_url(),
    echo=False,
    future=True,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connectivity() -> bool:
    """Executes a lightweight ping query (SELECT 1) against PostgreSQL."""
    try:
        from sqlalchemy import text
        async with async_session_factory() as session:
            res = await session.execute(text("SELECT 1"))
            return res.scalar() == 1
    except Exception as exc:
        logger.warning(f"Database connectivity check failed: {exc}")
        return False
