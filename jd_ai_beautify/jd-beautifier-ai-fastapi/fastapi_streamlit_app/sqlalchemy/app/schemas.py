import uuid
from typing import Optional, List
from datetime import datetime
from fastapi_users import schemas
from fastapi_users.schemas import CreateUpdateDictModel
from pydantic import BaseModel, Field, constr
from fastapi_users import schemas
from sqlalchemy.orm import sessionmaker, relationship

from db  import  Base,DeclarativeBase,Depends,engine
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


class JobDescriptionRequest(CreateUpdateDictModel):
    #job_description: str
    job_description: constr(min_length=1)
    role: constr(min_length=1)
    experience: constr(min_length=1)
    location: constr(min_length=1)
    beautified_job_description: Optional[List[str]] = None



class JobDescriptionResponse(BaseModel):
    id: int
    job_description: str
    role: str
    experience: str
    location: str
    beautified_description_1: str
    beautified_description_2: str
    beautified_description_3: str
    created_at: datetime




class BeautifiedJobDescriptionResponse(CreateUpdateDictModel):
    beautified_job_description: list[str]

