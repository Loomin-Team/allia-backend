import json
from wsgiref import validate
from pydantic import parse_obj_as
from sqlalchemy import JSON, Enum, Column, ForeignKey, Integer, Nullable, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from app.config.db import Base

class Corpus(Base):
    __tablename__ = 'corpus'
    id = Column(Integer, primary_key=True, index=True)