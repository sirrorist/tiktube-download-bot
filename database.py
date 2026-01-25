"""Database models and initialization."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, BigInteger, Text
from datetime import datetime
from typing import AsyncGenerator

from config import settings

Base = declarative_base()


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_premium = Column(Boolean, default=False)
    downloads_today = Column(Integer, default=0)
    total_downloads = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    downloads = relationship("Download", back_populates="user")


class Download(Base):
    """Download history model."""
    __tablename__ = "downloads"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    platform = Column(String(50), nullable=False)
    url = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False)  # video, photo, text
    file_size = Column(Integer, nullable=True)
    status = Column(String(20), default="completed")  # completed, failed, processing
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="downloads")


# Database engine and session
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized successfully")
