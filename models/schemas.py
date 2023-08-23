from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ratingSchema(BaseModel):
    _id: Optional[str]
    userID: Optional[str]
    courseQuality: Optional[float]
    responsiveness: Optional[float]
    lod: Optional[float]
    course: Optional[str]
    date: Optional[datetime]  # You can use the datetime module to work with date and time
    helpfulness: Optional[float]
    feedback: Optional[str]  # Making feedback field optional

class professorSchema(BaseModel):
    _id: Optional[str]
    name: Optional[str]
    rating: Optional[float]
    lod: Optional[float]
    courses: Optional[List[str]]
    dept: Optional[str]
    school: Optional[str]
    totRatings: Optional[int]
    courseQuality: Optional[float]
    helpfulness: Optional[float]
    responsiveness: Optional[float]
    userRatings: List[ratingSchema] = []

class userSchema(BaseModel):
    _id: Optional[str]
    sub: Optional[str]
    name: Optional[str]
    email: Optional[str]
    picture: Optional[str]
    ratings: Optional[List[ratingSchema]] = []
    