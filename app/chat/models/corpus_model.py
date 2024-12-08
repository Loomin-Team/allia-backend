import json
from wsgiref import validate
from pydantic import parse_obj_as
from sqlalchemy import Column, Integer

from app.config.db import Base

class Corpus(Base):
    __tablename__ = 'corpus'
    id = Column(Integer, primary_key=True, index=True)