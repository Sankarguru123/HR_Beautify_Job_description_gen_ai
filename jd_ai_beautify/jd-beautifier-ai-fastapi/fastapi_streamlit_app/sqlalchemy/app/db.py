import asyncio
import uuid
from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Text, ForeignKey,Boolean,DateTime, func,event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, DeclarativeBase

import os
from dotenv import load_dotenv



# DATABASE_URL = "sqlite+aiosqlite:///./test.db"
load_dotenv()
class Base(DeclarativeBase):
    pass
class JobDescription(Base):
    __tablename__ = 'job_descriptions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_description = Column(String, nullable=False)
    role = Column(String, nullable=False)
    experience = Column(String, nullable=False)
    location = Column(String, nullable=False)
    beautified_description_1 = Column(Text, nullable=True)
    beautified_description_2 = Column(Text, nullable=True)
    beautified_description_3 = Column(Text, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    archived = Column(Boolean, default=False)
    user = relationship("User", back_populates="job_descriptions")
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = 'user'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    job_descriptions = relationship("JobDescription", back_populates="user")
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


engine = create_async_engine(os.environ.get("DATABASE_URL"),echo=True)
print(engine,'value')
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


# async def connect_to_db():
#     connected = False
#     while not connected:
#         try:
#             async with engine.begin() as conn:
#                 connected = True
#                 print("Connected to the database!")
#         except OperationalError:
#             print("Database is not ready, retrying in 5 seconds...")
#             await asyncio.sleep(5)

# @event.listens_for(engine.sync_engine, "connect")
# async def do_startup(target, connection, **kw):
#     await connect_to_db()



async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


@event.listens_for(JobDescription, 'before_update')
def receive_before_update(mapper, connection, target):
    target.updated_at = func.now()



@event.listens_for(User, 'before_update')
def receive_before_update(mapper, connection, target):
    target.updated_at = func.now()

