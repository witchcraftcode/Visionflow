from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _engine_kwargs(database_url: str):
    url = make_url(database_url)
    if url.drivername.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


engine = create_engine(
    settings.database_url,
    future=True,
    pool_recycle=1800,
    pool_size=10,
    max_overflow=20,
    **_engine_kwargs(settings.database_url),
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def is_sqlite() -> bool:
    return engine.url.drivername.startswith("sqlite")

from contextlib import contextmanager


@contextmanager
def session_scope():
    session = SessionLocal()

    try:
        yield session
        session.commit()

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()