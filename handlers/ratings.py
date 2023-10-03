from fastapi import HTTPException, Header
from fastapi.responses import JSONResponse
from pymongo import ReturnDocument
from starlette.requests import Request
from bson import ObjectId
from models.schemas import ratingSchema
from pydantic import ValidationError
from utils.profanityFilter import containsHindiOffensiveWord
from profanity_check import predict_prob

from utils.authenticator import Authenticator


class RatingHandler:
	def __init__(self, db):
		self.db = db
		self.user_collection = db["users"]
		self.rating_collection = db["ratings"]
		self.professor_collection = db["professors"]
		self.authenticator = Authenticator(db)
	
	async def add_rating(self, request: Request, authorization: str = Header(None)):
		userData = {}
		try:
			# Authorize the request
			userData = await self.authenticator.Authorize(authorization=authorization)
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
		if predict_prob([rating["feedback"]]) > 0.42 or await containsHindiOffensiveWord(rating["feedback"]):
			raise HTTPException(status_code=422, detail="Warning: Feedback contains inappropriate language.")

		try:
			# Retrieve existing user data
			existing_user = self.user_collection.find_one({"_id": ObjectId(userID)})
		except:
			raise HTTPException(status_code=400, detail="Wrong userID format")
		
		if not existing_user:
			raise HTTPException(status_code=404, detail="User not found")
		
		if professorID and rating:
			professor_object_id = ObjectId(professorID)

			# Check if the user has already rated this professor for this course
			existing_rating = self.rating_collection.find_one(
				{"professorID": professorID, "userID": userID, "course": rating["course"]}
			)
			if existing_rating:
				raise HTTPException(status_code=409, detail="You have already rated this professor for this course")
			try:
				# Update professor ratings with the new rating
				result = self.professor_collection.update_one(
					{"_id": professor_object_id},
					{"$push": {"userRatings": rating}}
				)
			except Exception as e:
				raise HTTPException(status_code=500, detail=f"Failed to update professor ratings. Error: {e}")

			if result.modified_count == 1:
				updated_professor = self.professor_collection.find_one({"_id": professor_object_id})
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
					result = self.professor_collection.update_one(
						{"_id": professor_object_id},
						{"$set": updated_professor},
					)
					# Update rating collection
					inserted_rating = self.rating_collection.insert_one(rating)
					if inserted_rating.acknowledged and result is not None:
						response = JSONResponse({"response": "Rating created successfully"}, status_code=201)
						return response
					else:
						raise HTTPException(status_code=500, detail="Failed to add rating")
				else:
					raise HTTPException(status_code=404, detail="Professor not found")
		
		raise HTTPException(status_code=400, detail="Invalid input data")

	# Get Professor Ratings
	async def get_professor_ratings(self, request: Request, professor_collection):
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
	async def update_professor_rating(self, request: Request, professor_collection, authorization: str = Header(None)):
		if authorization is None:
			raise HTTPException(status_code=500, detail="No Authorization Token Received")
		try:
			# Authorize the request
			userData = await self.authenticator.Authorize(authorization=authorization)
		except HTTPException as http_exception:
			# Handle authorization errors
			return JSONResponse({"detail": http_exception.detail}, status_code=http_exception.status_code)
		userData = {}
		# if match:
		# 	jwt_token = match.group(1)
		# 	print(jwt_token)
		# 	try:
		# 		userData = await decode_jwt(jwt_token)
		# 		print(userData)
		# 	except jwt.ExpiredSignatureError:
		# 		raise HTTPException(status_code=401, detail="Authorization Token Expired")
		# 	except Exception as e:
		# 		raise HTTPException(status_code=401, detail="Invalid Authorization Token Received", headers={"detail": str(e)})
		# else:
		# 	raise HTTPException(status_code=401, detail="No Authorization Token Received")
		
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
	async def delete_professor_rating(self, request: Request, professor_collection, authorization: str = Header(None)):
		if authorization is None:
			raise HTTPException(status_code=500, detail="No Authorization Token Received")
		# match = re.match(r"Bearer (.+)", authorization)
		# userData = {}
		# if match:
		# 	jwt_token = match.group(1)
		# 	print(jwt_token)
		# 	try:
		# 		userData = decode_jwt(jwt_token)
		# 		print(userData)
		# 	except jwt.ExpiredSignatureError:
		# 		raise HTTPException(status_code=500, detail="Authorization Token Expired")
		# 	except Exception as e:
		# 		raise HTTPException(status_code=400, detail="Invalid Authorization Token Received", headers={"detail": str(e)})
		# else:
		# 	raise HTTPException(status_code=500, detail="No Authorization Token Received")
		try:
			# Authorize the request
			userData = await self.authenticator.Authorize(authorization=authorization)
		except HTTPException as http_exception:
			# Handle authorization errors
			return JSONResponse({"detail": http_exception.detail}, status_code=http_exception.status_code)
		
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