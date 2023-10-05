from fastapi import HTTPException, Request
from bson import ObjectId
import re
from fastapi.responses import JSONResponse
import httpx
from fastapi import HTTPException
import jwt
from starlette.requests import Request
from datetime import timezone, datetime, timedelta
from os import environ as env
from pymongo import ReturnDocument
from dotenv import find_dotenv, load_dotenv

ENV_FILE = find_dotenv()
if ENV_FILE:
	load_dotenv(ENV_FILE)

class Authenticator:
	def __init__(self, db):
		self.db = db
		self.user_collection = db["users"]
		self.JWT_SECRET = env.get("JWT_SECRET")
		self.banTimeout = int(env.get("BAN_TIMEOUT"))
		self.jwtExpiryTime = int(env.get("JWT_EXPIRE_TIME"))

	async def encode_jwt(self, userD, expire_time):
		userD["exp"] = datetime.now(tz=timezone.utc) + timedelta(seconds=expire_time)
		return jwt.encode(userD, self.JWT_SECRET, algorithm="HS256")

	async def decode_jwt(self, encoded_jwt):
		return jwt.decode(encoded_jwt, self.JWT_SECRET, algorithms=["HS256"])

	async def Authorize(self, authorization):
		if authorization is None:
			raise HTTPException(status_code=401, detail="No Authorization Token Received")
		match = re.match(r"Bearer (.+)", authorization)
		userData = {}
		if match:
			jwt_token = match.group(1)
			# print(jwt_token)
			try:
				userData = await self.decode_jwt(jwt_token)
				existingUser = None
				try:
					existingUser = self.user_collection.find_one(
						{"sub": userData["sub"]},  # Query condition
					)
				except Exception as e:
					print(f"USER NOT FOUND: {e}")
					pass
				if existingUser is not None:
					userData["_id"] = str(existingUser["_id"])
					print(f"USER FOUND: {userData}")
					if existingUser["banned"]:
						timeDifference = datetime.now() - existingUser["banStartTime"]
						if timeDifference.total_seconds() > self.banTimeout:
							result = self.user_collection.find_one_and_update(
								{"_id": existingUser},
								{
									"$set": {
										"banned": False,
										"banStartTime": 0,
										"warnings": 0
									}
								},
								return_document=ReturnDocument.AFTER
							)
							
							# print(f"You have been temporarily banned from adding ratings. Please try again after {(self.banTimeout - timeDifference.total_seconds()) / 60} minutes.")
							# raise HTTPException(status_code=403, detail=f"You have been temporarily banned from adding ratings. Please try again after {(self.banTimeout - timeDifference.total_seconds()) / 60} minutes.")
				# print(userData)
				return userData
			except jwt.ExpiredSignatureError:
				raise HTTPException(status_code=401, detail="Authorization Token Expired")
			except Exception as e: 
				raise HTTPException(status_code=401, detail=f"Invalid Authorization Token Received: {str(e)}")
			
		else:
			raise HTTPException(status_code=401, detail="No Authorization Token Received")

	async def Verify_user(self, request: Request):
		data = await request.json()
		token = data['accessToken']
		# print(f"'accessToken': {token}")
		headers = {'Authorization': f'Bearer {token}'}
		async with httpx.AsyncClient() as client:
			response = await client.get('https://www.googleapis.com/oauth2/v3/userinfo', headers=headers)
			user_info = response.json()
		if "error" in user_info:
			return JSONResponse(user_info, status_code=400)
		existingUser = self.user_collection.find_one({"$or": [{"email": user_info["email"]}, {"sub": user_info["sub"]}]})
		# print(f"userInfo: {user_info}")
		userData = {
			"sub": user_info.get("sub"),
			"name": user_info.get("name"),
			"email": user_info.get("email"),
			"picture": user_info.get("picture"),
			"ratings": [],
			"banned": False,
			"banStartTime": 0,
			"warnings": 0
		}
		print(f"real: {userData}")
		encoded_jwt = ""
		if existingUser:
			existingUser = dict(existingUser)
			existingUser["_id"] = str(existingUser["_id"])
			if "sub" in existingUser:
				existingUser.pop("sub")
			encoded_jwt = await self.encode_jwt(userData, expire_time=self.jwtExpiryTime)
			if "exp" in existingUser:
				existingUser.pop("exp")
			# print("User already exists:", existingUser)
			existingUser["banStartTime"] = str(existingUser["banStartTime"])
			response_data = {
				"message": "User already exists",
				"userData": existingUser
			}
			response = JSONResponse(content=response_data, status_code=200)
			response.headers["Authorization"] = f"Bearer {encoded_jwt}"
			return response
		else:
			userData["_id"] = ObjectId()
			result = self.user_collection.insert_one(userData)
			# if "sub" in userData:
			# 	userData.pop("sub")
			userData["_id"] = str(userData["_id"])
			encoded_jwt = await self.encode_jwt(userData, expire_time=self.jwtExpiryTime)
			# print(1111111111111111111)
			if "exp" in userData:
				userData.pop("exp")

			userData["banStartTime"] = str(userData["banStartTime"])
			# print(userData)
			# print(1111111111111111111)
			# print(result)
			if result.acknowledged:
				response = JSONResponse({"message": "User added successfully", "userData": userData }, status_code=200)
				response.headers["Authorization"] = f"Bearer {encoded_jwt}"
				print({"message": "User added successfully", "userData": userData })
				return response
			else:
				print(f"Failed to add user: {userData}")
				raise HTTPException(status_code=500, detail={"response": "Failed to add user", "userData": userData})