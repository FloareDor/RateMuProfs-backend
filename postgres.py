from fastapi import FastAPI, HTTPException, Request
from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from typing import List
from pydantic import BaseModel
from datetime import datetime
import json
import time

app = FastAPI()

DATABASE_URL = "postgresql://username:password@localhost/dbname"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class UserRating(BaseModel):
    courseQuality: int
    responsiveness: int
    lod: int
    course: str
    date: str
    helpfulness: int
    feedback: str

class Professor(Base):
    __tablename__ = "professors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    rating = Column(Float)
    lod = Column(Float)
    courses = Column(JSON)
    dept = Column(String)
    school = Column(String)
    totRatings = Column(Integer)
    courseQuality = Column(Float)
    helpfulness = Column(Float)
    responsiveness = Column(Float)
    userRatings = relationship("UserRatingModel", back_populates="professor")

class UserRatingModel(Base):
    __tablename__ = "user_ratings"

    id = Column(Integer, primary_key=True, index=True)
    courseQuality = Column(Integer)
    responsiveness = Column(Integer)
    lod = Column(Integer)
    course = Column(String)
    date = Column(String)
    helpfulness = Column(Integer)
    feedback = Column(String)
    professor_id = Column(Integer, ForeignKey("professors.id"))
    professor = relationship("Professor", back_populates="userRatings")

Base.metadata.create_all(bind=engine)

class ProfessorResponse(Professor, BaseModel):
    pass

@app.on_event("startup")
async def insert_professors():
    with open("prof_data.json", "r") as json_file:
        data = json.load(json_file)

    db = SessionLocal()
    for prof in data:
        user_ratings = prof.pop("userRatings", [])
        professor = Professor(**prof)
        db.add(professor)
        db.commit()

        for rating in user_ratings:
            db_rating = UserRatingModel(**rating, professor_id=professor.id)
            db.add(db_rating)
            db.commit()

@app.get("/professors", response_model=List[ProfessorResponse])
async def get_all_professors():
    db = SessionLocal()
    professors = db.query(Professor).all()
    time.sleep(10)
    return professors

@app.get("/professors/by_school/{school}", response_model=List[ProfessorResponse])
async def get_professors_by_school(school: str):
    db = SessionLocal()
    professors = db.query(Professor).filter(Professor.school.ilike(f"%{school}%")).all()
    return professors

@app.post("/professors/get_professor", response_model=ProfessorResponse)
async def get_professor(request: Request):
    data = await request.json()
    professor_id = data["_id"]

    db = SessionLocal()
    professor = db.query(Professor).filter(Professor.id == professor_id).first()

    if professor:
        return professor
    else:
        raise HTTPException(status_code=404, detail="Professor not found")
