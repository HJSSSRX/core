from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from forhacker.data.models import Base

_engine = None
_session_factory = None


async def init_db(database_url: str = "postgresql+asyncpg://localhost/forhacker"):
    global _engine, _session_factory
    _engine = create_async_engine(database_url, echo=False)
    _session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _session_factory()


async def close_db():
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
