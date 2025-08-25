# app/db.py
import os
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime
from datetime import datetime
from typing import Optional
from .config import settings

# Ensure directory exists for SQLite file paths
try:
    url = make_url(settings.DATABASE_URL)
    if url.get_backend_name().startswith("sqlite") and url.database:
        dirpath = os.path.dirname(url.database) or "."
        os.makedirs(dirpath, exist_ok=True)
except Exception:
    # Non-sqlite URLs or parsing errors can be ignored here
    pass

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class EmailRecord(Base):
    __tablename__ = "email_records"
    key: Mapped[str] = mapped_column(String(512), primary_key=True)
    email: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
