import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    AsyncSession,
    async_scoped_session
)
from sqlalchemy.orm import sessionmaker
from app.config import get_db_uri
from app import create_app



@pytest.fixture(scope="session", autouse=True)
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def aio_engine():
    engine: AsyncEngine = create_async_engine(get_db_uri(), future=True)

    # Write initial set up and teardown code.

    yield engine


@pytest_asyncio.fixture(scope="function")
async def session_factory(aio_engine: AsyncEngine):
    async with aio_engine.connect() as conn:
        sf: sessionmaker = sessionmaker(
            conn,
            expire_on_commit=False,
            autoflush=False,
            class_=AsyncSession,
        )
        scoped_session = async_scoped_session(
            session_factory=sf, scopefunc=asyncio.current_task
        )
        yield scoped_session


@pytest_asyncio.fixture(scope="function")
async def session(session_factory: async_scoped_session):
    s: AsyncSession = session_factory()
    yield s
    await s.commit()
    await s.close()
