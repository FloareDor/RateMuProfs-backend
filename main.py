from fastapi import FastAPI, HTTPException, Request, Depends, status
from typing import Dict, Any, List
from pymongo import MongoClient
from bson import ObjectId
import re
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
import json
from pymongo import ReturnDocument
import requests
import httpx
from os import environ as env
from fastapi import HTTPException
from models.schemas import ratingSchema, professorSchema, userSchema
from pydantic import BaseModel, ValidationError
from dotenv import find_dotenv, load_dotenv
import jwt
from starlette.requests import Request
import datetime
from datetime import timezone

ENV_FILE = find_dotenv()
if ENV_FILE:
	load_dotenv(ENV_FILE)
JWT_SECRET = env.get("JWT_SECRET")
print(JWT_SECRET)

d = 		{
			"courseQuality": 4,
			"responsiveness": 5,
			"lod": 4,
			"course": "Computer Organization",
			"date": "2023-05-28T09:59:53.346Z",
			"helpfulness": 3,
			"feedback": "good prof",
			"_id": "647325b57231c23c45077152",
		}

d = ratingSchema(**d)
print(d)


# MongoDB professor connection
client = MongoClient(env.get("ATLAS_URL"))
db = client["rate_my_professor"]
professor_collection = db["professors"]
professor_collection.delete_many({})

# User collection
user_collection = db["users"]
user_collection.delete_many({})

# Ratings collection
rating_collection = db["ratings"]
rating_collection.delete_many({})

def insertSample_data(filename):
	with open(filename, "r") as json_file:
		data = json.load(json_file)
	for prof in data:
		# Insert the document into the professor_collection
		prof["_id"] = ObjectId(prof["_id"])
		insert_result = professor_collection.insert_one(prof)
		# Check if the insertion was successful
		if insert_result.acknowledged:
			# print("Document inserted successfully!")
			for doc in professor_collection.find():
				# Convert the ObjectId to string representation before printing
				doc["_id"] = str(doc["_id"])
				# print(doc)
		else:
			print("Failed to insert the document.")

	print("Document inserted successfully!")

sampleFilename = "prof_data.json"
insertSample_data(sampleFilename)

app = FastAPI()

origins = ["*"]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"]
)

# def verify_google_oauth_token(token: str):
# 	try:
# 		id_info = id_token.verify_oauth2_token(token, requests.Request())
# 		return id_info
# 	except GoogleAuthError:
# 		raise HTTPException(status_code=401, detail="Invalid Google OAuth token")

async def encode_jwt(userData, expire_time):
	userData["exp"] = datetime.datetime.now(tz=timezone.utc) + datetime.timedelta(seconds=expire_time)
	return jwt.encode(userData, JWT_SECRET, algorithm="HS256")

async def decode_jwt(encoded_jwt):
	jwt.decode(encoded_jwt, JWT_SECRET, algorithms=["HS256"])


# print(verify_google_oauth_token(str("ya29.a0AfB_byBLRN6R-1eVjKyHiEqxFUcXPJNEWyR-5ogRThC61u0eWLOz2kMIiZ8uyUbXPo1kfHOlypw_IC0pc7EmCF7CF_AxkP68d5DvRBxKQedMf-W5_2Ed2y7KcJUJUr05dZc_qPFAgxZUSwxK5P_5RYaN8BQ4b_Gh99pGRSUaCgYKAbsSARISFQHsvYls3fcdIqOBWTudbOi-C-jAYw0174")))
@app.get("/")
async def main():
	return {"message": "Hello World"}

@app.post("/verify_user")
async def verify_user(request: Request):
	data = await request.json()
	token = data['accessToken']
	print(f"'accessToken': {token}")
	headers = {'Authorization': f'Bearer {token}'}
	async with httpx.AsyncClient() as client:
		response = await client.get('https://www.googleapis.com/oauth2/v3/userinfo', headers=headers)
		user_info = response.json()
	if "error" in user_info:
		return JSONResponse(user_info)
	existing_user = user_collection.find_one({"$or": [{"email": user_info["email"]}, {"sub": user_info["sub"]}]})
	userData = {
		"sub": user_info.get("sub"),
		"name": user_info.get("name"),
		"email": user_info.get("email"),
		"picture": user_info.get("picture"),
		"ratings": []
	}
	encoded_jwt = ""
	if existing_user:
		existing_user = dict(existing_user)
		existing_user["_id"] = str(existing_user["_id"])
		existing_user.pop("sub")
		encoded_jwt = encode_jwt(userData, expire_time=3600)
		print("User already exists:", existing_user)
		return JSONResponse({"response": "User already exists", "userData": existing_user, "token": encoded_jwt})
	else:
		result = user_collection.insert_one(userData)
		userData.pop("sub")
		userData["_id"] = str(userData["_id"])
		encoded_jwt = encode_jwt(userData, expire_time=3600)
		if result.acknowledged:
			print(f"User added successfully: {userData}")
			return JSONResponse({"response": "User added successfully", "userData": userData, "token": encoded_jwt})
		else:
			print(f"Failed to add user: {userData}")
			raise HTTPException(status_code=400, detail={"response": "Failed to add user", "user": userData})

userData = {
    "sub": "user123",
    "name": "John Doe",
    "email": "john@example.com",
    "picture": "https://example.com/profile.jpg",
    "ratings": [],
    "exp": datetime.datetime.now(tz=timezone.utc) + datetime.timedelta(seconds=1)
}

print(jwt.encode(userData, JWT_SECRET, algorithm="HS256"))
########################### PROFESSOR CRUD ####################################

# get all profs
@app.get("/professors", response_model=List[Dict[str, Any]])
async def get_all_professors():
	professors = []
	for professor in professor_collection.find().sort("name"):
		# Convert the ObjectId to string representation before returning
		professor["_id"] = str(professor["_id"])
		professors.append(professor)
	if professors:
		# time.sleep(10)
		return professors
	else:
		raise HTTPException(status_code=404, detail="No professors found")
	
	
@app.get("/professors/by_school/{school}")
async def get_professors_by_school(school: str):
	professors = []
	for professor in professor_collection.find({"school": re.compile(school, re.IGNORECASE)}).sort("name"):
		# Convert the ObjectId to string representation before returning
		professor["_id"] = str(professor["_id"])
		professors.append(professor)
	if professors:
		return professors
	else:
		raise HTTPException(status_code=404, detail=f"No professors found for school: {school}")

# Read Professor
@app.post("/professors/get_professor", response_model=Dict[str, Any])
async def get_professor(request: Request):
	data = await request.json()
	professorID = data["_id"]
	print(professorID)
	if professorID:
		try:
			professor = professor_collection.find_one({"_id": ObjectId(professorID)})
			if professor:
				professor["_id"] = str(professor["_id"])
				return professor
		except Exception as e:
			print(e)
			raise HTTPException(status_code=404, detail="Professor not found")
	raise HTTPException(status_code=404, detail="Professor not found")


# Update Professor
@app.post("/professors/update_professor", response_model=Dict[str, Any])
async def update_professor(request: Request):
	data = await request.json()
	# print(data)
	professorID = ObjectId(data["_id"])
	updated_professor = data
	updated_professor.pop("_id", None)
	if professorID and updated_professor:
		professor = professor_collection.find_one({"_id": professorID})
		print(professor)
		for key in updated_professor:
			if updated_professor[key] != professor[key]:
				professor[key] = updated_professor[key]
		print(professor)
		result = professor_collection.update_one(
			{"_id": professorID},
			{"$set": professor}
		)
		if result.modified_count == 1:
			# updated_professor["_id"] = professorID
			professor = professor_collection.find_one({"_id": ObjectId(professorID)})
			if professor:
				professor["_id"] = str(professor["_id"])
				return professor
	raise HTTPException(status_code=404, detail="Professor not found")


# Delete Professor
@app.delete("/professors/delete_professor", response_model=Dict[str, str])
async def delete_professor(request: Request):
	data = await request.json()
	professorID = data.get("professorID")
	
	if professorID:
		result = await professor_collection.delete_one({"_id": professorID})
		if result.deleted_count == 1:
			return {"message": "Professor deleted successfully"}
	raise HTTPException(status_code=404, detail="Professor not found")



########################### RATING CRUD ####################################


# Add Professor Rating
@app.post("/professors/add_rating", response_model=Dict[str, Any])
async def create_professor_rating(request: Request, authorization: str = Header(None)):
	if authorization is None:
		raise HTTPException(status_code=500, detail="No Authorization Token Received")
	match = re.match(r"Bearer (.+)", authorization)
	userData = {}
	if match:
		jwt_token = match.group(1)
		print(jwt_token)
		try:
			userData = decode_jwt(jwt_token)
			print(userData)
		except jwt.ExpiredSignatureError:
			raise HTTPException(status_code=500, detail="Authorization Token Expired")
		except Exception as e:
			raise HTTPException(status_code=400, detail="Invalid Authorization Token Received", headers={"detail": str(e)})
	else:
		raise HTTPException(status_code=500, detail="No Authorization Token Received")
	
	data = await request.json()
	professorID = data["professorID"]
	userID = userData["_id"]
	rating = data["rating"]
	rating["userID"] = userID
	rating["_id"] = ObjectId()

	try:
		rating = ratingSchema(**rating)  # Validate and create RatingSchema instance
	except ValidationError as e:
		raise HTTPException(status_code=400, detail="Invalid rating data", headers={"detail": str(e)})
	try:
		existing_user = user_collection.find_one({"_id": ObjectId(userID)})
	except:
		raise HTTPException(status_code=500, detail="Wrong userID format")
	if not existing_user:
		raise HTTPException(status_code=500, detail="User not found")
	if professorID and rating:
		professor_object_id = ObjectId(professorID)
		
		try:
			result = professor_collection.update_one(
				{"_id": professor_object_id},
				{"$push": {"userRatings": rating}}
			)
		except Exception as e:
			raise HTTPException(status_code=500, detail="Failed to update professor ratings")

		if result.modified_count == 1:
			updated_professor = professor_collection.find_one({"_id": professor_object_id})
			if updated_professor:
				updated_professor["_id"] = str(updated_professor["_id"])
				for i in range(len(updated_professor["userRatings"])):
					updated_professor["userRatings"][i]["_id"] = str(updated_professor["userRatings"][i]["_id"])
				return updated_professor
			else:
				raise HTTPException(status_code=404, detail="Professor not found")
	raise HTTPException(status_code=400, detail="Invalid input data")

# Get Professor Ratings
@app.get("/professors/get_ratings", response_model=List[Dict[str, Any]])
async def get_professor_ratings(request: Request):

	
	data = await request.json()
	professorID = data["professorID"]
	print(professor_collection.find_one({"_id": ObjectId(professorID)}))
	if professorID:
		professor = professor_collection.find_one({"_id": ObjectId(professorID)})
		if professor and "userRatings" in professor:
			for i in range(len(professor["userRatings"])):
				professor["userRatings"][i]["_id"] = str(professor["userRatings"][i]["_id"])
			return professor["userRatings"]
		
	raise HTTPException(status_code=404, detail="Professor not found or no ratings available")

# Update Professor Rating
@app.post("/professors/update_rating", response_model=List[Dict[str, Any]])
async def update_professor_rating(request: Request, authorization: str = Header(None)):
	if authorization is None:
		raise HTTPException(status_code=500, detail="No Authorization Token Received")
	match = re.match(r"Bearer (.+)", authorization)
	userData = {}
	if match:
		jwt_token = match.group(1)
		print(jwt_token)
		try:
			userData = decode_jwt(jwt_token)
			print(userData)
		except jwt.ExpiredSignatureError:
			raise HTTPException(status_code=500, detail="Authorization Token Expired")
		except Exception as e:
			raise HTTPException(status_code=400, detail="Invalid Authorization Token Received", headers={"detail": str(e)})
	else:
		raise HTTPException(status_code=500, detail="No Authorization Token Received")
	
	userID = userData["_id"]
	data = await request.json()
	professorID = ObjectId(data["professorID"])
	rating_id = ObjectId(data["rating"]["_id"])
	updated_rating = data["rating"]
	try:
		update_rating = ratingSchema(**update_rating)  # Validate and create RatingSchema instance
	except ValidationError as e:
		raise HTTPException(status_code=400, detail="Invalid rating data", headers={"detail": str(e)})
	
	if professorID and rating_id and updated_rating:
		professor = professor_collection.find_one({"_id": professorID})
		if professor and "userRatings" in professor:
			updated_ratings = professor["userRatings"]
			count = 0
			l = len(updated_ratings)
			for i in range(l):
				if ObjectId(updated_ratings[i]["_id"]) == rating_id and updated_ratings[i]["userID"] == userID:
					for key, value in updated_rating.items():
						if key in updated_ratings[i] and key != "_id":
							updated_ratings[i][key] = value
					break
				count+=1
				if count >= l:
					raise HTTPException(status_code=404, detail="Professor rating not found")
							
			result = professor_collection.find_one_and_update(
				{"_id": professorID},
				{"$set": {"userRatings": updated_ratings}},
				return_document=ReturnDocument.AFTER
			)
			
			if result and "userRatings" in result:
				for i in range(len(result["userRatings"])):
					result["userRatings"][i]["_id"] = str(result["userRatings"][i]["_id"])
				return result["userRatings"]
	
	raise HTTPException(status_code=404, detail="Professor rating not found")


# Delete Professor Rating
@app.post("/professors/delete_rating", response_model=Dict[str, str])
async def delete_professor_rating(request: Request, authorization: str = Header(None)):
	if authorization is None:
		raise HTTPException(status_code=500, detail="No Authorization Token Received")
	match = re.match(r"Bearer (.+)", authorization)
	userData = {}
	if match:
		jwt_token = match.group(1)
		print(jwt_token)
		try:
			userData = decode_jwt(jwt_token)
			print(userData)
		except jwt.ExpiredSignatureError:
			raise HTTPException(status_code=500, detail="Authorization Token Expired")
		except Exception as e:
			raise HTTPException(status_code=400, detail="Invalid Authorization Token Received", headers={"detail": str(e)})
	else:
		raise HTTPException(status_code=500, detail="No Authorization Token Received")
	
	userID = userData["_id"]
	data = await request.json()
	professorID = ObjectId(data["professorID"])
	rating = ObjectId(data["rating"])
	try:
		rating = ratingSchema(**rating)  # Validate and create RatingSchema instance
	except ValidationError as e:
		raise HTTPException(status_code=400, detail="Invalid rating data", headers={"detail": str(e)})
	rating_id = ObjectId(rating["_id"])
	if professorID and rating_id:
		result = professor_collection.update_one(
			{"_id": ObjectId(professorID)},
			{"$pull": {"userRatings": {"$and": [{"_id": str(rating_id)}, {"userID": userID}] }}}
		)
		if result.modified_count == 1:
			return {"message": "Professor rating deleted successfully"}
	raise HTTPException(status_code=404, detail="Professor rating not found")
