from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import SessionLocal, Tile, TileBase
from datetime import date
from typing import List

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Seed data function
def seed_data(db: Session):
    # Check if data already exists
    if db.query(Tile).first() is None:
        sample_tiles = [
            Tile(
                title="Welcome to UpToCure",
                content="Revolutionizing healthcare through innovative AI solutions.",
                date=date(2024, 3, 1)
            ),
            Tile(
                title="AI in Healthcare",
                content="Exploring the future of medical diagnostics with artificial intelligence.",
                date=date(2024, 3, 2)
            ),
            Tile(
                title="Patient Care",
                content="Improving patient outcomes through data-driven decisions.",
                date=date(2024, 3, 3)
            ),
        ]
        for tile in sample_tiles:
            db.add(tile)
        db.commit()

@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    seed_data(db)
    db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to UpToCure API"}

@app.get("/api/tiles", response_model=List[TileBase])
def get_tiles(db: Session = Depends(get_db)):
    tiles = db.query(Tile).all()
    return [{"title": tile.title, "content": tile.content, "tile_date": tile.date} for tile in tiles] 