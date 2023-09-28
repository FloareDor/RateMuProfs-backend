from fastapi import HTTPException, Header
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from starlette.requests import Request
from bson import ObjectId
import re

from utils.authenticator import authorize

client = MongoClient('mongodb://localhost:27017/?maxPoolSize=100')
db = client["rate_my_professor"]
professor_collection = db["professors"]
professor_collection.delete_many({})

async def get_all_professors(request: Request):
    professors = []
    for professor in professor_collection.find().sort("name"):
        # Convert the ObjectId to string representation before returning
        professor["_id"] = str(professor["_id"])
        professors.append(professor)
    if professors:
        return JSONResponse(professors, status_code=200)
    else:
        raise HTTPException(status_code=404, detail="No professors found")
	

async def get_professors_by_school(request: Request, school: str):
	professors = []
	for professor in professor_collection.find({"school": re.compile(school, re.IGNORECASE)}).sort("name"):
		# Convert the ObjectId to string representation before returning
		professor["_id"] = str(professor["_id"])
		professors.append(professor)
	if professors:
		response = JSONResponse(professors, status_code=200)
		return response
	else:
		raise HTTPException(status_code=404, detail=f"No professors found for school: {school}")

async def get_professor(request: Request):
	data = await request.json()
	professorID = data["_id"]
	print(professorID)
	if professorID:
		try:
			professor = professor_collection.find_one({"_id": ObjectId(professorID)})
			if professor:
				professor["_id"] = str(professor["_id"])
				# validation = professorSchema(**professor)
				response = JSONResponse(professor, status_code=200)
				return response
		except Exception as e:
			print(e)
			raise HTTPException(status_code=404, detail="Professor not found")
	raise HTTPException(status_code=404, detail="Professor not found")


async def get_courses(request: Request, authorization: str = Header(None)):
	try:
		await authorize(authorization=authorization)
	except HTTPException as http_exception:
		return JSONResponse({"detail": http_exception.detail}, status_code=http_exception.status_code)
	
	data = await request.json()
	professorID = data["professorID"]
	print(professorID)
	if professorID:
		try:
			professor = professor_collection.find_one({"_id": ObjectId(professorID)})
			if professor:
				if "courses" in professor:
					response = JSONResponse({"courses": professor["courses"]}, status_code=200)
					return response
				else:
					raise HTTPException(status_code=404, detail="No course data found for this professor")
		except Exception as e:
			print(e)
			raise HTTPException(status_code=404, detail="Professor not found")
	raise HTTPException(status_code=404, detail="Professor not found")