from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)


class Base(MappedAsDataclass, DeclarativeBase):
    pass


async_session_maker = async_sessionmaker(engine, expire_on_commit=False, autoflush=False,
                                         class_=AsyncSession)


async def get_async_session():
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
