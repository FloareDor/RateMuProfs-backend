from fastapi import HTTPException, Request
from bson import ObjectId
import re
from fastapi.responses import JSONResponse
import httpx
from os import environ as env
from fastapi import HTTPException
from dotenv import find_dotenv, load_dotenv
import jwt
from starlette.requests import Request
import datetime
from datetime import timezone
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/?maxPoolSize=100')
db = client["rate_my_professor"]

# User collection
user_collection = db["users"]
user_collection.delete_many({})

ENV_FILE = find_dotenv()
if ENV_FILE:
	load_dotenv(ENV_FILE)
JWT_SECRET = env.get("JWT_SECRET")

async def encode_jwt(userD, expire_time):
	userD["exp"] = datetime.datetime.now(tz=timezone.utc) + datetime.timedelta(seconds=expire_time)
	return jwt.encode(userD, JWT_SECRET, algorithm="HS256")

async def decode_jwt(encoded_jwt):
	return jwt.decode(encoded_jwt, JWT_SECRET, algorithms=["HS256"])

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