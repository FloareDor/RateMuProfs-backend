from fastapi import APIRouter, Request, Header
from typing import Dict, Any, List
from starlette.requests import Request
from fastapi.responses import JSONResponse

# rate limit imports
from slowapi import Limiter
from slowapi.util import get_remote_address


# from handlers.professors import get_all_professors, get_professor, get_professors_by_school, get_courses
# from handlers.ratings import add_rating, get_professor_ratings, update_professor_rating, delete_professor_rating
from handlers.professors import ProfessorHandler
from handlers.ratings import RatingHandler
from utils.authenticator import Authenticator

from utils.scripts import insertSampleData, initDB

db = initDB()
insertSampleData("prof_data.json", db)

professorHandler = ProfessorHandler(db)
ratingHandler = RatingHandler(db)
authenticator = Authenticator(db)

limiter = Limiter(key_func=get_remote_address, config_filename=".rate")
router = APIRouter()

# Health check
@router.get("/", response_model=List[Dict[str, Any]])
@limiter.limit("30/minute")
async def health(request: Request):
    return JSONResponse({"status": "ok"}, status_code=200)

# Auth
@router.post("/verify_user")
@limiter.limit("12/minute")
async def verifyUser(request: Request):
    return await authenticator.Verify_user(request)

# Professors

@router.get("/professors", response_model=List[Dict[str, Any]])
@limiter.limit("30/minute")
async def getProfessors(request: Request):
    return await professorHandler.get_all_professors(request)

@router.get("/professors/by_school/{school}")
@limiter.limit("30/minute")
async def getProfessorBySchool(request: Request, school: str):
    return await professorHandler.get_professors_by_school(request, school)

@router.post("/professors/get_professor")
@limiter.limit("30/minute")
async def getProfessor(request: Request):
    return await professorHandler.get_professor(request)

@router.post("/professors/get_courses")
@limiter.limit("30/minute")
async def getCourses(request: Request, authorization: str = Header(None)):
    return await professorHandler.get_courses(request, authorization=authorization)

# Ratings

@router.post("/professors/add_rating")
@limiter.limit("12/minute")
async def addRating(request: Request, authorization: str = Header(None)):
    return await ratingHandler.add_rating(request, authorization=authorization)

@router.get("/professors/get_ratings", response_model=List[Dict[str, Any]])
@limiter.limit("30/minute")
async def getProfessorRatings(request: Request):
    return await ratingHandler.get_professor_ratings(request)

@router.post("/professors/update_rating", response_model=List[Dict[str, Any]])
@limiter.limit("12/minute")
async def updateProfessorRating(request: Request, authorization: str = Header(None)):
    return await ratingHandler.update_professor_rating(request, authorization=authorization)

@router.post("/professors/delete_rating", response_model=Dict[str, str])
@limiter.limit("12/minute")
async def deleteProfessorRating(request: Request, authorization: str = Header(None)):
    return await ratingHandler.delete_professor_rating(request, authorization=authorization)





