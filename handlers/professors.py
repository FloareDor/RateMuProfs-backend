from fastapi import HTTPException, Header, Request
from fastapi.responses import JSONResponse
from bson import ObjectId
import re

from utils.authenticator import Authenticator


class ProfessorHandler:
	def __init__(self, db):
		self.db = db
		self.professor_collection = db["professors"]
		self.authenticator = Authenticator(db)

	async def get_all_professors(self, request: Request):
		professors = []
		for professor in self.professor_collection.find().sort("name"):
			professor["_id"] = str(professor["_id"])
			professors.append(professor)
		if professors:
			return JSONResponse(professors, status_code=200)
		else:
			raise HTTPException(status_code=404, detail="No professors found")
	
	async def get_professors_by_school(self, request: Request, school: str):
		professors = []
		for professor in self.professor_collection.find({"school": re.compile(school, re.IGNORECASE)}).sort("name"):
			professor["_id"] = str(professor["_id"])
			professors.append(professor)
		if professors:
			return JSONResponse(professors, status_code=200)
		else:
			raise HTTPException(status_code=404, detail=f"No professors found for school: {school}")
	
	async def get_professor(self, request: Request):
		data = await request.json()
		professorID = data["_id"]
		print(professorID)
		if professorID:
			try:
				professor = self.professor_collection.find_one({"_id": ObjectId(professorID)})
				if professor:
					professor["_id"] = str(professor["_id"])
					response = JSONResponse(professor, status_code=200)
					return response
			except Exception as e:
				print(e)
				raise HTTPException(status_code=404, detail="Professor not found")
		raise HTTPException(status_code=404, detail="Professor not found")
	
	async def get_courses(self, request: Request, authorization: str = Header(None)):
		try:
			await self.authenticator.Authorize(authorization=authorization)
		except HTTPException as http_exception:
			return JSONResponse({"detail": http_exception.detail}, status_code=http_exception.status_code)
		
		data = await request.json()
		professorID = data["professorID"]
		print(professorID)
		if professorID:
			try:
				professor = self.professor_collection.find_one({"_id": ObjectId(professorID)})
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
