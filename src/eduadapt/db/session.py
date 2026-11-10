"""Database connection and session lifecycle management for EduAdapt."""

from contextlib import asynccontextmanager, contextmanager
import logging
import socket
import sys
import asyncio
from typing import Any, AsyncGenerator, Generator, Optional
from urllib.parse import urlparse

# On Windows, psycopg async requires the Selector event loop policy rather than ProactorEventLoop
if sys.platform == "win32" and hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    try:
        if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsSelectorEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from eduadapt.config import Settings, get_settings

logger = logging.getLogger("eduadapt.db.session")

_async_engine: Optional[AsyncEngine] = None
_sync_engine = None
_AsyncSessionFactory: Optional[async_sessionmaker[AsyncSession]] = None
_SyncSessionFactory: Optional[sessionmaker[Session]] = None


def is_local_port_open(host: str, port: int, timeout: float = 0.3) -> bool:
    """Test whether a local host/port is accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def resolve_effective_database_url(raw_url: str, is_async: bool = True) -> str:
    """Resolve database URL, applying intelligent development fallback if local PostgreSQL is offline.

    Args:
        raw_url: The configured database URL.
        is_async: Whether async driver is requested.

    Returns:
        Effective, connectable database URL.
    """
    clean_url = raw_url.strip()
    parsed = urlparse(clean_url.replace("+psycopg", ""))

    # If configured for local PostgreSQL (localhost or 127.0.0.1 on port 5432), probe port availability
    if "postgres" in parsed.scheme and parsed.hostname in ("localhost", "127.0.0.1", "::1"):
        port = parsed.port or 5432
        if not is_local_port_open(parsed.hostname, port):
            logger.warning(
                "PostgreSQL service is not running on %s:%d. External PostgreSQL setup is required for production. "
                "Activating local SQLite fallback at ./data/eduadapt.db for development and verification.",
                parsed.hostname,
                port,
            )
            fallback_sqlite = "sqlite+aiosqlite:///./data/eduadapt.db" if is_async else "sqlite:///./data/eduadapt.db"
            return fallback_sqlite

    return normalize_database_url(clean_url, is_async=is_async)


def normalize_database_url(url: str, is_async: bool = True) -> str:
    """Normalize database connection string for psycopg driver.

    Args:
        url: Raw database URL (e.g. postgresql://user:pass@host/db).
        is_async: Whether an async driver scheme is required.

    Returns:
        Normalized URL string compatible with SQLAlchemy 2.0.
    """
    clean_url = url.strip()

    if clean_url.startswith("postgres://"):
        clean_url = "postgresql://" + clean_url[len("postgres://") :]

    if clean_url.startswith("postgresql://"):
        if is_async:
            return "postgresql+psycopg://" + clean_url[len("postgresql://") :]
        return "postgresql+psycopg://" + clean_url[len("postgresql://") :]

    if is_async and clean_url.startswith("sqlite://") and not clean_url.startswith("sqlite+aiosqlite://"):
        return "sqlite+aiosqlite://" + clean_url[len("sqlite://") :]

    return clean_url


def get_async_engine(settings: Optional[Settings] = None, url_override: Optional[str] = None) -> AsyncEngine:
    """Retrieve or create the global async SQLAlchemy engine."""
    global _async_engine, _AsyncSessionFactory
    if _async_engine is not None and url_override is None:
        return _async_engine

    cfg = settings or get_settings()
    raw_url = url_override or cfg.database_url
    if url_override is not None:
        async_url = normalize_database_url(url_override, is_async=True)
    else:
        async_url = resolve_effective_database_url(raw_url, is_async=True)

    engine_kwargs = {
        "echo": getattr(cfg, "database_echo", False),
        "future": True,
    }

    if not async_url.startswith("sqlite"):
        engine_kwargs.update(
            {
                "pool_size": getattr(cfg, "database_pool_size", 10),
                "max_overflow": getattr(cfg, "database_max_overflow", 20),
                "pool_timeout": getattr(cfg, "database_pool_timeout", 30.0),
                "pool_pre_ping": True,
            }
        )

    engine = create_async_engine(async_url, **engine_kwargs)
    if url_override is None:
        _async_engine = engine
        _AsyncSessionFactory = async_sessionmaker(
            bind=_async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return engine


def get_sync_engine(settings: Optional[Settings] = None, url_override: Optional[str] = None):
    """Retrieve or create the synchronous SQLAlchemy engine."""
    global _sync_engine, _SyncSessionFactory
    if _sync_engine is not None and url_override is None:
        return _sync_engine

    cfg = settings or get_settings()
    raw_url = url_override or cfg.database_url
    if url_override is not None:
        sync_url = normalize_database_url(url_override, is_async=False)
    else:
        sync_url = resolve_effective_database_url(raw_url, is_async=False)

    engine_kwargs = {
        "echo": getattr(cfg, "database_echo", False),
        "future": True,
    }

    if not sync_url.startswith("sqlite"):
        engine_kwargs.update(
            {
                "pool_size": getattr(cfg, "database_pool_size", 10),
                "max_overflow": getattr(cfg, "database_max_overflow", 20),
                "pool_timeout": getattr(cfg, "database_pool_timeout", 30.0),
                "pool_pre_ping": True,
            }
        )

    engine = create_engine(sync_url, **engine_kwargs)
    if url_override is None:
        _sync_engine = engine
        _SyncSessionFactory = sessionmaker(
            bind=_sync_engine,
            class_=Session,
            expire_on_commit=False,
            autoflush=False,
        )
    return engine


def get_async_session_factory(settings: Optional[Settings] = None) -> async_sessionmaker[AsyncSession]:
    """Retrieve or create the async session factory."""
    global _AsyncSessionFactory
    if _AsyncSessionFactory is None:
        get_async_engine(settings)
    assert _AsyncSessionFactory is not None
    return _AsyncSessionFactory


def get_sync_session_factory(settings: Optional[Settings] = None) -> sessionmaker[Session]:
    """Retrieve or create the synchronous session factory."""
    global _SyncSessionFactory
    if _SyncSessionFactory is None:
        get_sync_engine(settings)
    assert _SyncSessionFactory is not None
    return _SyncSessionFactory


async def get_db_session(session_factory: Any = None) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI async dependency yielding an isolated database session."""
    factory = session_factory or get_async_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_sync_db_session(session_factory: Any = None) -> Generator[Session, None, None]:
    """FastAPI synchronous dependency yielding an isolated database session."""
    factory = session_factory or get_sync_session_factory()
    with factory() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


async def check_database_connection(engine: Optional[AsyncEngine] = None) -> dict:
    """Execute a lightweight probe to verify database connectivity.

    Returns:
        Dict indicating status and latency or descriptive error details.
    """
    eng = engine or get_async_engine()
    try:
        async with eng.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.scalar()
            return {
                "status": "healthy" if row == 1 else "unhealthy",
                "database": eng.url.database,
                "driver": eng.url.drivername,
                "host": eng.url.host,
            }
    except Exception as exc:
        logger.warning("Database connectivity check failed: %s", exc)
        return {
            "status": "unreachable",
            "error": str(exc),
            "driver": eng.url.drivername,
            "host": eng.url.host,
            "database": eng.url.database,
        }


def check_database_connection_sync(engine=None) -> dict:
    """Synchronous connectivity probe."""
    eng = engine or get_sync_engine()
    try:
        with eng.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.scalar()
            return {
                "status": "healthy" if row == 1 else "unhealthy",
                "database": eng.url.database,
                "driver": eng.url.drivername,
                "host": eng.url.host,
            }
    except Exception as exc:
        logger.warning("Sync database connectivity check failed: %s", exc)
        return {
            "status": "unreachable",
            "error": str(exc),
            "driver": eng.url.drivername,
            "host": eng.url.host,
            "database": eng.url.database,
        }


async def close_database_connections() -> None:
    """Dispose and cleanly close database engine connections."""
    global _async_engine, _sync_engine, _AsyncSessionFactory, _SyncSessionFactory
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
        _AsyncSessionFactory = None
    if _sync_engine is not None:
        _sync_engine.dispose()
        _sync_engine = None
        _SyncSessionFactory = None


def init_db(engine=None) -> None:
    """Ensure database schema tables are created in the target database."""
    from eduadapt.db.base import Base
    import eduadapt.db.models  # noqa: F401
    eng = engine or get_sync_engine()
    Base.metadata.create_all(eng)
