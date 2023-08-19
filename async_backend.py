from fastapi import FastAPI, HTTPException, Request
from typing import List
from beanie import init_beanie
from pydantic import BaseModel
from bson import ObjectId
import json
import re
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

from beanie import Document, Indexed, init_beanie

app = FastAPI()

class UserRating(BaseModel):
    courseQuality: int
    responsiveness: int
    lod: int
    course: str
    date: str
    helpfulness: int
    feedback: str

class Professor(Document):
    name: str
    rating: float
    lod: float
    courses: List[str]
    dept: str
    school: str
    totRatings: int
    courseQuality: Optional[float]
    helpfulness: Optional[float]
    responsiveness: Optional[float]
    userRatings: Optional[List[UserRating]]

client = AsyncIOMotorClient("mongodb://localhost:27017")
# Initialize Beanie


with open("prof_data.json", "r") as json_file:
    data = json.load(json_file)

@app.on_event("startup")
async def insert_professors():
    await init_beanie(database=client.rate_my_professor, document_models=[Professor])
    for prof in data:
        prof["_id"] = ObjectId()
        prof.setdefault("userRatings", [])
        prof.setdefault("courseQuality", None)
        prof.setdefault("helpfulness", None)
        prof.setdefault("responsiveness", None)
        professor = Professor(**prof)
        # print(professor)
        try:
            await professor.insert()
        except Exception as e:
            print(e,professor)

@app.get("/professors", response_model=List[Professor])
async def get_all_professors():
    professors = await Professor.find().sort(Professor.name).to_list()
    if professors:
        return professors
    else:
        raise HTTPException(status_code=404, detail="No professors found")
    
@app.get("/professors/by_school/{school}", response_model=List[Professor])
async def get_professors_by_school(school: str):
    professors = await Professor.find(
        Professor.school == re.compile(school, re.IGNORECASE)
    ).sort(Professor.name).to_list()

    if professors:
        return professors
    else:
        raise HTTPException(status_code=404, detail=f"No professors found for school: {school}")
    
@app.post("/professors/get_professor", response_model=Professor)
async def get_professor(request: Request):
    data = await request.json()
    professor_id = data["_id"]
    
    if professor_id:
        try:
            professor = await Professor.get(professor_id)
            return professor
        except Exception as e:
            print(e)
            raise HTTPException(status_code=404, detail="Professor not found")
    
    raise HTTPException(status_code=404, detail="Professor not found")

# @app.post("/professors/add_rating", response_model=Professor)
# async def create_professor_rating(request: Request):
#     data = await request.json()
#     professor_id = data["_id"]
#     rating = data["rating"]
#     try:
#         if professor_id and rating:
#             professor = await Professor.get(ObjectId(professor_id))
#             print(professor)
#             if professor:
#                 rating["_id"] = ObjectId()
#                 print(professor.userRatings)
#                 professor.userRatings.append(rating)
#                 await professor.save()
#                 return professor
#             else:
#                 raise HTTPException(status_code=404, detail="Professor not found")
#     except Exception as e:
#         print(e)
    
#     raise HTTPException(status_code=400, detail="Invalid input data")
    


