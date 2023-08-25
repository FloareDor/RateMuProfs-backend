from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ratingSchema(BaseModel):
    _id: Optional[str] = None
    userID: Optional[str] = None
    courseQuality: Optional[float] = None
    responsiveness: Optional[float] = None
    lod: Optional[float] = None
    course: Optional[str] = None
    date: Optional[datetime] = None 
    helpfulness: Optional[float] = None
    feedback: Optional[str] = None
    

class professorSchema(BaseModel):
    _id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    rating: Optional[float] = 5
    lod: Optional[float] = 2.5
    courses: Optional[List[str]] = []
    dept: Optional[str] = None
    school: Optional[str] = None
    totRatings: Optional[int] = 1
    courseQuality: Optional[float] = 5
    helpfulness: Optional[float] = 5
    responsiveness: Optional[float] = 5
    userRatings: List[ratingSchema] = []
    linkedin_link: Optional[str] = None
    googleScholar_link: Optional[str] = None
    muProfile_link: Optional[str] = None

class userSchema(BaseModel):
    _id: Optional[str] = None
    sub: Optional[str]
    name: Optional[str]
    email: Optional[str]
    picture: Optional[str] = None
    ratings: Optional[List[ratingSchema]] = []
    