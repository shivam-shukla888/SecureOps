import logging
import urllib.parse
from typing import AsyncGenerator, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)


def get_db_connection_params(raw_url: str = "") -> Tuple[str, Dict[str, Any]]:
    """
    Parses and normalizes DATABASE_URL for SQLAlchemy asyncpg driver.
    - Strips prefixes, whitespace, quotes.
    - Normalizes postgres:// / postgresql:// to postgresql+asyncpg://.
    - Strips unsupported query parameters (e.g. sslmode) that crash asyncpg.
    - Configures SSL mode cleanly for cloud/hosted PostgreSQL (e.g. Supabase, AWS RDS, Render).
    """
    url_str = (raw_url or settings.DATABASE_URL or "").strip("\"' \t\r\n")
    if url_str.startswith("DATABASE_URL="):
        url_str = url_str[len("DATABASE_URL="):].strip("\"' \t\r\n")

    if not url_str:
        return "postgresql+asyncpg://postgres:postgres@localhost:5432/secureops", {"timeout": 5.0}

    parsed = urllib.parse.urlparse(url_str)
    scheme = parsed.scheme
    if scheme in ("postgresql", "postgres"):
        scheme = "postgresql+asyncpg"
    elif not scheme.startswith("postgresql+asyncpg"):
        scheme = "postgresql+asyncpg"

    query_params = urllib.parse.parse_qs(parsed.query)
    connect_args: Dict[str, Any] = {
        "timeout": 5.0,
        "command_timeout": 5.0,
    }

    # Extract and strip sslmode and ssl query params so asyncpg does not error
    sslmode = query_params.pop("sslmode", [None])[0]
    ssl_val = query_params.pop("ssl", [None])[0]

    is_remote = parsed.hostname not in ("localhost", "127.0.0.1", "postgres", None)

    # Enable SSL for remote providers or when requested
    if (
        sslmode in ("require", "prefer", "verify-ca", "verify-full")
        or ssl_val in ("require", "true", "1")
        or (is_remote and sslmode != "disable" and ssl_val != "disable")
    ):
        connect_args["ssl"] = "require"

    new_query = urllib.parse.urlencode(
        {k: v[0] if len(v) == 1 else v for k, v in query_params.items()},
        doseq=True,
    )
    clean_url = urllib.parse.urlunparse(
        (scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
    )
    return clean_url, connect_args


def get_async_db_url() -> str:
    clean_url, _ = get_db_connection_params()
    return clean_url


_clean_url, _connect_args = get_db_connection_params()
engine = create_async_engine(
    _clean_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=10,
    connect_args=_connect_args,
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


get_db = get_db_session


async def check_db_connectivity() -> bool:
    """Executes a lightweight ping query (SELECT 1) against PostgreSQL."""
    try:
        from sqlalchemy import text
        async with async_session_factory() as session:
            res = await session.execute(text("SELECT 1"))
            return res.scalar() == 1
    except Exception as exc:
        logger.warning(f"Database connectivity check failed ({type(exc).__name__})")
        return False
