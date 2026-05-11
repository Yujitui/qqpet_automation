from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from app.config import settings, SQLITE_DATABASE_URL

use_sqlite = settings.is_sqlite or not settings.DATABASE_URL

if use_sqlite:
    database_url = SQLITE_DATABASE_URL
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False}
    )

    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    database_url = settings.DATABASE_URL
    engine = create_engine(
        database_url,
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models import User, PetData, PetInventory, UserSettings, Session
    Base.metadata.create_all(bind=engine)
