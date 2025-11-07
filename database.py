from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import settings

Base = declarative_base()

# Add SQLite-specific connection arguments for better compatibility
connect_args = {"check_same_thread": False}
if "sqlite" in settings.database_url:
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
        connect_args=connect_args
    )
else:
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True
    )

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def init_db():
    """Initialize database tables - ensure all models are imported first"""
    async with engine.begin() as conn:
        # Create all tables defined in models that inherit from Base
        await conn.run_sync(Base.metadata.create_all)
        
        # Log all tables that were created
        await conn.run_sync(lambda sync_conn: print(f"Created tables: {list(Base.metadata.tables.keys())}"))


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
