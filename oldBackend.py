from fastapi import FastAPI, HTTPException, Request, Depends, status, Response
from typing import Dict, Any, List
from pymongo import MongoClient
from bson import ObjectId
import re
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
import json
from pymongo import ReturnDocument
import httpx
from os import environ as env
from fastapi import HTTPException
from models.schemas import ratingSchema, professorSchema, userSchema
from pydantic import BaseModel, ValidationError
from dotenv import find_dotenv, load_dotenv
import jwt
from starlette.requests import Request

from profanity_check import predict_prob
from fuzzywuzzy import fuzz

import datetime
from datetime import timezone
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded



ENV_FILE = find_dotenv()
if ENV_FILE:
	load_dotenv(ENV_FILE)
JWT_SECRET = env.get("JWT_SECRET")

d = 		{
			"professorID": "x",
			"userID": "xx",
			"overallRating": 5,
			"responsiveness": 5,
			"teachingQuality": 4,
			"helpfulness": 3,
			"course": "Computer Organization",
			"date": "2023-05-28T09:59:53.346Z",
			"feedback": "good prof",
			"_id": "647325b57231c23c45077152",
		}

# try:
# 	b = ratingSchema(**d)
# except:
# 	exit()

ATLAS_URL = env.get("ATLAS_URL")
localDb = 'mongodb://localhost:27017/?maxPoolSize=100'
# MongoDB professor connection
client = MongoClient(localDb)
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
		prof["rating"] = 5
		prof["teachingQuality"] = 5
		prof["userRatings"] = []
		prof["totRatings"] = 0
		prof["helpfulness"] = 5
		prof["courseQuality"] = 5
		prof["responsiveness"] = 5
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

limiter = Limiter(key_func=get_remote_address, config_filename=".rate")
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

print(111111111111111111)
origins = ["*"]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
	expose_headers=["Authorization"],
)

async def encode_jwt(userD, expire_time):
	userD["exp"] = datetime.datetime.now(tz=timezone.utc) + datetime.timedelta(seconds=expire_time)
	return jwt.encode(userD, JWT_SECRET, algorithm="HS256")

async def decode_jwt(encoded_jwt):
	return jwt.decode(encoded_jwt, JWT_SECRET, algorithms=["HS256"])

offensive_hindi_words = [
		"bahenchod", "behenchod", "bhenchod", "bhenchodd", "b.c.", "bc", "bakchod", "bakchodd", 
		"bakchodi", "bevda", "bewda", "bevdey", "bewday", "bevakoof", "bevkoof", "bevkuf", "bewakoof", 
		"bewkoof", "bewkuf", "bhadua", "bhaduaa", "bhadva", "bhadvaa", "bhadwa", "bhadwaa", "bhosada", 
		"bhosda", "bhosdaa", "bhosdike", "bhonsdike", "bhosdiki", "bhosdiwala", "bhosdiwale", 
		"bhosadchodal", "bhosadchod", "bhosadchodal", "bhosadchod", "babbe", "babbey", "bube", "bubey", 
		"bur", "burr", "buurr", "buur", "charsi", "chooche", "choochi", "chuchi", "chhod", "chod", "chodd", 
		"chudne", "chudney", "chudwa", "chudwaa", "chudwane", "chudwaane", "chaat", "choot", "chut", 
		"chute", "chutia", "chutiya", "chutiye", "dalaal", "dalal", "dalle", "dalley", "fattu", "gadha", 
		"gadhe", "gadhalund", "gaand", "gand", "gandu", "gandfat", "gandfut", "gandiya", "gandiye", 
		"gote", "gotey", "gotte", "hag", "haggu", "hagne", "hagney", "harami", "haramjada", 
		"haraamjaada", "haramzyada", "haraamzyaada", "haraamjaade", "haraamzaade", "haraamkhor", "haramkhor", 
		"jhat", "jhaat", "jhaatu", "jhatu", "kutta", "kutte", "kuttey", "kutia", "kutiya", "kuttiya", 
		"kutti", "landi", "landy", "laude", "laudey", "laura", "lora", "lauda", "ling", "loda", "lode", 
		"lund", "launda", "lounde", "laundey", "laundi", "loundi", "laundiya", "loundiya", "lulli", 
		"maar", "maro", "marunga", "madarchod", "madarchodd", "madarchood", "madarchoot", "madarchut", "mamme", "mammey", "moot", "mut", "mootne", "mutne", "mooth", "muth", "nunni", 
		"nunnu", "paaji", "paji", "pesaab", "pesab", "peshaab", "peshab", "pilla", "pillay", "pille", 
		"pilley", "pisaab", "pisab", "pkmkb", "porkistan", "raand", "rand", "randi", "randy", "suar", 
		"tatte", "tatti", "tatty", "ullu", "chewtiya"
	]

async def contains_hindi_offensive_word(text):

	for offensiveWord in offensive_hindi_words:
		for word in text.lower().split():
			if fuzz.ratio(offensiveWord, word) > 65:  # Adjust the similarity threshold as needed
				print(fuzz.ratio(offensiveWord, word), word, offensiveWord)
				return True
	return False

async def authorize(authorization):
	if authorization is None:
		raise HTTPException(status_code=401, detail="No Authorization Token Received")
	match = re.match(r"Bearer (.+)", authorization)
	userData = {}
	if match:
		jwt_token = match.group(1)
		print(jwt_token)
		try:
			userData = await decode_jwt(jwt_token)
			existing_user_id = None
			try:
				existing_user_id = user_collection.find_one(
					{"sub": userData["sub"]},  # Query condition
					{"_id": 1}  # Projection: Include only the "_id" field
				)
			except Exception as e:
				print("USER NOT FOUND")
				print(e)
				pass
			if existing_user_id is not None:
				userData["_id"] = str(existing_user_id["_id"])
				print("YOOOOOOOOOOOOOO")
				print(userData["_id"])
				print("YOPOOOOOOOOOOOOOOO")
			print(userData)
			return userData
		except jwt.ExpiredSignatureError:
			raise HTTPException(status_code=401, detail="Authorization Token Expired")
		except Exception as e: 
			raise HTTPException(status_code=401, detail="Invalid Authorization Token Received", headers={"detail": str(e)})
		
	else:
		raise HTTPException(status_code=401, detail="No Authorization Token Received")

# print(verify_google_oauth_token(str("ya29.a0AfB_byBLRN6R-1eVjKyHiEqxFUcXPJNEWyR-5ogRThC61u0eWLOz2kMIiZ8uyUbXPo1kfHOlypw_IC0pc7EmCF7CF_AxkP68d5DvRBxKQedMf-W5_2Ed2y7KcJUJUr05dZc_qPFAgxZUSwxK5P_5RYaN8BQ4b_Gh99pGRSUaCgYKAbsSARISFQHsvYls3fcdIqOBWTudbOi-C-jAYw0174")))
@app.get("/home")
@limiter.limit("5/minute")
async def main(request: Request):
	return {"message": "Hello World"}

@app.post("/verify_user")
@limiter.limit("12/minute")
async def verify_user(request: Request):
	data = await request.json()
	token = data['accessToken']
	print(f"'accessToken': {token}")
	headers = {'Authorization': f'Bearer {token}'}
	async with httpx.AsyncClient() as client:
		response = await client.get('https://www.googleapis.com/oauth2/v3/userinfo', headers=headers)
		user_info = response.json()
	if "error" in user_info:
		return JSONResponse(user_info, status_code=400)
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
		if "sub" in existing_user:
			existing_user.pop("sub")
		encoded_jwt = await encode_jwt(userData, expire_time=3600)
		if "exp" in existing_user:
			existing_user.pop("exp")
		print("User already exists:", existing_user)
		response_data = {
			"message": "User already exists",
			"userData": existing_user
		}
		response = JSONResponse(content=response_data, status_code=200)
		response.headers["Authorization"] = f"Bearer {encoded_jwt}"
		return response
	else:
		userData["_id"] = ObjectId()
		result = user_collection.insert_one(userData)
		if "sub" in userData:
			userData.pop("sub")
		userData["_id"] = str(userData["_id"])
		encoded_jwt = await encode_jwt(userData, expire_time=3600)
		# print(1111111111111111111)
		if "exp" in userData:
			userData.pop("exp")
		# print(userData)
		# print(1111111111111111111)
		if result.acknowledged:
			response = JSONResponse({"message": "User added successfully", "userData": userData }, status_code=200)
			response.headers["Authorization"] = f"Bearer {encoded_jwt}"
			return response
		else:
			print(f"Failed to add user: {userData}")
			raise HTTPException(status_code=500, detail={"response": "Failed to add user", "userData": userData})

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
@limiter.limit("30/minute")
async def get_all_professors(request: Request):
	professors = []
	for professor in professor_collection.find().sort("name"):
		# Convert the ObjectId to string representation before returning
		professor["_id"] = str(professor["_id"])
		professors.append(professor)
	if professors:
		response = JSONResponse(professors, status_code=200)
		# time.sleep(10)
		return response
	else:
		raise HTTPException(status_code=404, detail="No professors found")
	
	
@app.get("/professors/by_school/{school}")
# @limiter.limit("30/minute")
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

# Read Professor
@app.post("/professors/get_professor")
@limiter.limit("30/minute")
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
			response = JSONResponse({"message": "Professor deleted successfully"}, status_code=200)
			return response
	raise HTTPException(status_code=404, detail="Professor not found")

@app.post("/professors/get_courses")
@limiter.limit("30/minute")
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


########################### RATING CRUD ####################################

# Add Professor Rating
@app.post("/professors/add_rating")
@limiter.limit("12/minute")
async def create_professor_rating(request: Request, authorization: str = Header(None)):
	userData = {}
	try:
		# Authorize the request
		userData = await authorize(authorization=authorization)
	except HTTPException as http_exception:
		# Handle authorization errors
		return JSONResponse({"detail": http_exception.detail}, status_code=http_exception.status_code)

	# Parse request data
	data = await request.json()
	professorID = data["professorID"]
	userID = userData["_id"]
	rating = data["rating"]
	rating["professorID"] = professorID
	rating["userID"] = userID
	rating["_id"] = str(ObjectId())
	rating["overallRating"] = 0.0
	

	try:
		# Validate and create a RatingSchema instance
		x = ratingSchema(**rating)
	except ValidationError as e:
		# Handle invalid rating data
		raise HTTPException(status_code=400, detail="Invalid rating data", headers={"detail": str(e)})
	
	subRatings = ["courseQuality", "helpfulness", "teachingQuality", "responsiveness"]
	for key, value in rating.items():
		if value is not None and key in subRatings:
			rating["overallRating"] += value
	rating["overallRating"] = rating["overallRating"] / 4
	
	# Check for foul language
	if predict_prob([rating["feedback"]]) > 0.42 or await contains_hindi_offensive_word(rating["feedback"]):
		raise HTTPException(status_code=422, detail="Warning: Feedback contains inappropriate language.")

	try:
		# Retrieve existing user data
		existing_user = user_collection.find_one({"_id": ObjectId(userID)})
	except:
		raise HTTPException(status_code=400, detail="Wrong userID format")
	
	if not existing_user:
		raise HTTPException(status_code=404, detail="User not found")
	
	if professorID and rating:
		professor_object_id = ObjectId(professorID)

		# Check if the user has already rated this professor for this course
		existing_rating = rating_collection.find_one(
			{"professorID": professorID, "userID": userID, "course": rating["course"]}
		)
		if existing_rating:
			raise HTTPException(status_code=409, detail="You have already rated this professor for this course")
		try:
			# Update professor ratings with the new rating
			result = professor_collection.update_one(
				{"_id": professor_object_id},
				{"$push": {"userRatings": rating}}
			)
		except Exception as e:
			raise HTTPException(status_code=500, detail=f"Failed to update professor ratings. Error: {e}")

		if result.modified_count == 1:
			updated_professor = professor_collection.find_one({"_id": professor_object_id})
			if updated_professor:
				# Update professor values
				updated_professor["helpfulness"] = ((updated_professor["helpfulness"] * updated_professor["totRatings"]) + rating["helpfulness"]) / (updated_professor["totRatings"] + 1)
				updated_professor["rating"] = ((updated_professor["rating"] * updated_professor["totRatings"]) + rating["overallRating"]) / (updated_professor["totRatings"] + 1)
				updated_professor["courseQuality"] = ((updated_professor["courseQuality"] * updated_professor["totRatings"]) + rating["courseQuality"]) / (updated_professor["totRatings"] + 1)
				updated_professor["teachingQuality"] = ((updated_professor["teachingQuality"] * updated_professor["totRatings"]) + rating["teachingQuality"]) / (updated_professor["totRatings"] + 1)
				updated_professor["responsiveness"] = ((updated_professor["responsiveness"] * updated_professor["totRatings"]) + rating["responsiveness"]) / (updated_professor["totRatings"] + 1)

				# Round off values to one decimal
				updated_professor["helpfulness"] = round(updated_professor["helpfulness"], 1)
				updated_professor["rating"] = round(updated_professor["rating"], 1)
				updated_professor["courseQuality"] = round(updated_professor["courseQuality"], 1)
				updated_professor["teachingQuality"] = round(updated_professor["teachingQuality"], 1)
				updated_professor["responsiveness"] = round(updated_professor["responsiveness"], 1)

				updated_professor["totRatings"] += 1

				# Update professor data
				result = professor_collection.update_one(
					{"_id": professor_object_id},
					{"$set": updated_professor},
				)
				# Update rating collection
				inserted_rating = rating_collection.insert_one(rating)
				if inserted_rating.acknowledged and result is not None:
					response = JSONResponse({"response": "Rating created successfully"}, status_code=201)
					return response
				else:
					raise HTTPException(status_code=500, detail="Failed to add rating")
			else:
				raise HTTPException(status_code=404, detail="Professor not found")
	
	raise HTTPException(status_code=400, detail="Invalid input data")

# Get Professor Ratings
@app.get("/professors/get_ratings", response_model=List[Dict[str, Any]])
@limiter.limit("30/minute")
async def get_professor_ratings(request: Request):

	
	data = await request.json()
	professorID = data["professorID"]
	print(professor_collection.find_one({"_id": ObjectId(professorID)}))
	if professorID:
		professor = professor_collection.find_one({"_id": ObjectId(professorID)})
		if professor and "userRatings" in professor:
			for i in range(len(professor["userRatings"])):
				professor["userRatings"][i]["_id"] = str(professor["userRatings"][i]["_id"])
			response = JSONResponse(professor["userRatings"], status_code=200)
			return response
		
	raise HTTPException(status_code=404, detail="Professor not found or no ratings available")

# Update Professor Rating
@app.post("/professors/update_rating", response_model=List[Dict[str, Any]])
@limiter.limit("12/minute")
async def update_professor_rating(request: Request, authorization: str = Header(None)):
	if authorization is None:
		raise HTTPException(status_code=500, detail="No Authorization Token Received")
	match = re.match(r"Bearer (.+)", authorization)
	userData = {}
	if match:
		jwt_token = match.group(1)
		print(jwt_token)
		try:
			userData = await decode_jwt(jwt_token)
			print(userData)
		except jwt.ExpiredSignatureError:
			raise HTTPException(status_code=401, detail="Authorization Token Expired")
		except Exception as e:
			raise HTTPException(status_code=401, detail="Invalid Authorization Token Received", headers={"detail": str(e)})
	else:
		raise HTTPException(status_code=401, detail="No Authorization Token Received")
	
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
				response = JSONResponse(professor["userRatings"], status_code=200)
				return response
	
	raise HTTPException(status_code=404, detail="Professor rating not found")


# Delete Professor Rating
@app.post("/professors/delete_rating", response_model=Dict[str, str])
@limiter.limit("12/minute")
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
		validation = ratingSchema(**rating)  # Validate and create RatingSchema instance
	except ValidationError as e:
		raise HTTPException(status_code=400, detail="Invalid rating data", headers={"detail": str(e)})
	rating_id = ObjectId(rating["_id"])
	if professorID and rating_id:
		result = professor_collection.update_one(
			{"_id": ObjectId(professorID)},
			{"$pull": {"userRatings": {"$and": [{"_id": str(rating_id)}, {"userID": userID}] }}}
		)
		if result.modified_count == 1:
			response = JSONResponse({"message": "Professor rating deleted successfully"}, status_code=200)
			return response
	raise HTTPException(status_code=404, detail="Professor rating not found")

if __name__ == "__main__":
	import uvicorn

	# ssl_cert_path = '/etc/letsencrypt/live/ratemuprofs.live/fullchain.pem'
	# ssl_key_path = '/etc/letsencrypt/live/ratemuprofs.live/privkey.pem'
	# uvicorn.run(app, host="0.0.0.0", port=8000, ssl_certfile=ssl_cert_path, ssl_keyfile=ssl_key_path)

	uvicorn.run(app, host="localhost", port=8000)