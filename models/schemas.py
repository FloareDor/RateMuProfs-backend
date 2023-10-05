from pydantic import BaseModel, Field, validator, ValidationError
from typing import Optional, List
from datetime import datetime

class ratingSchema(BaseModel):
    _id: Optional[str] = None
    professorID: str
    userID: str
    overallRating: Optional[float] = None
    courseQuality: float
    responsiveness: float
    teachingQuality: float
    helpfulness: float
    course: str
    date: Optional[str] = None 
    feedback: Optional[str] = None
    def __init__(self, **data):
        super().__init__(**data)
        # Additional validation logic can be placed here
        if self.courseQuality <= 0 or self.responsiveness <= 0 or self.teachingQuality <= 0 or self.helpfulness <= 0:
            raise ValueError('Rating values must be greater than 0')

class professorSchema(BaseModel):
    _id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    rating: Optional[float] = 5
    teachingQuality: Optional[float] = 2.5
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
    