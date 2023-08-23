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
    date: Optional[datetime] = None  # You can use the datetime module to work with date and time
    helpfulness: Optional[float] = None
    feedback: Optional[str] = None # Making feedback field optional

class professorSchema(BaseModel):
    _id: Optional[str] = None
    name: Optional[str] = None
    rating: Optional[float] = None
    lod: Optional[float] = None
    courses: Optional[List[str]] = []
    dept: Optional[str] = None
    school: Optional[str] = None
    totRatings: Optional[int] = None
    courseQuality: Optional[float] = None
    helpfulness: Optional[float] = None
    responsiveness: Optional[float] = None
    userRatings: List[ratingSchema] = []

class userSchema(BaseModel):
    _id: Optional[str] = None
    sub: Optional[str]
    name: Optional[str]
    email: Optional[str]
    picture: Optional[str] = None
    ratings: Optional[List[ratingSchema]] = []
    