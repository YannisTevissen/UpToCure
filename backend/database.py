from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from datetime import date

SQLALCHEMY_DATABASE_URL = "sqlite:///./uptocure.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TileBase(BaseModel):
    title: str
    content: str
    tile_date: date  # Renamed from 'date' to 'tile_date'

class Tile(Base):
    __tablename__ = "tiles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    date = Column(Date)

Base.metadata.create_all(bind=engine) 