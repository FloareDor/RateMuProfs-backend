from fastapi import FastAPI, HTTPException, Request
from typing import Dict, Any, List
from pymongo import MongoClient
from bson import ObjectId
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from pymongo import ReturnDocument
import time

with open("prof_data.json", "r") as json_file:
	data = json.load(json_file)

# MongoDB connection
client = MongoClient("mongodb://localhost:27017")
db = client["rate_my_professor"]
collection = db["professors"]
collection.delete_many({})

for prof in data:
	# Insert the document into the collection
	# if "userRatings" in prof:
	# 	for i in range(len(prof["userRatings"])):
	# 		prof["userRatings"][i]["_id"] = ObjectId(prof["userRatings"][i]["_id"])
			
	prof["_id"] = ObjectId(prof["_id"])
	insert_result = collection.insert_one(prof)
	# Check if the insertion was successful
	if insert_result.acknowledged:
		# print("Document inserted successfully!")
		for doc in collection.find():
			# Convert the ObjectId to string representation before printing
			doc["_id"] = str(doc["_id"])
			print(doc)
	else:
		print("Failed to insert the document.")

print("Document inserted successfully!")
app = FastAPI()

origins = ["*"]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.get("/")
async def main():
	time.sleep(1)
	return {"message": "Hello World"}

########################### PROFESSOR CRUD ####################################

# get all profs
@app.get("/professors", response_model=List[Dict[str, Any]])
def get_all_professors():
	professors = []
	for professor in collection.find().sort("name"):
		# Convert the ObjectId to string representation before returning
		professor["_id"] = str(professor["_id"])
		professors.append(professor)
	if professors:
		# time.sleep(10)
		return professors
	else:
		raise HTTPException(status_code=404, detail="No professors found")
	
	
@app.get("/professors/by_school/{school}", response_model=List[Dict[str, Any]])
def get_professors_by_school(school: str):
	professors = []
	for professor in collection.find({"school": re.compile(school, re.IGNORECASE)}).sort("name"):
		# Convert the ObjectId to string representation before returning
		professor["_id"] = str(professor["_id"])
		professors.append(professor)
	if professors:
		return professors
	else:
		raise HTTPException(status_code=404, detail=f"No professors found for school: {school}")

# Read Professor
@app.post("/professors/get_professor", response_model=Dict[str, Any])
def get_professor(request: Request):
	data = request.json()
	professor_id = data["_id"]
	print(professor_id)
	if professor_id:
		try:
			professor = collection.find_one({"_id": ObjectId(professor_id)})
			if professor:
				professor["_id"] = str(professor["_id"])
				return professor
		except Exception as e:
			print(e)
			raise HTTPException(status_code=404, detail="Professor not found")
	raise HTTPException(status_code=404, detail="Professor not found")


# Update Professor
@app.post("/professors/update_professor", response_model=Dict[str, Any])
def update_professor(request: Request):
	data =  request.json()
	# print(data)
	professor_id = ObjectId(data["_id"])
	updated_professor = data
	updated_professor.pop("_id", None)
	if professor_id and updated_professor:
		professor = collection.find_one({"_id": professor_id})
		print(professor)
		for key in updated_professor:
			if updated_professor[key] != professor[key]:
				professor[key] = updated_professor[key]
		print(professor)
		result = collection.update_one(
			{"_id": professor_id},
			{"$set": professor}
		)
		if result.modified_count == 1:
			# updated_professor["_id"] = professor_id
			professor = collection.find_one({"_id": ObjectId(professor_id)})
			if professor:
				professor["_id"] = str(professor["_id"])
				return professor
	raise HTTPException(status_code=404, detail="Professor not found")


# Delete Professor
@app.delete("/professors/delete_professor", response_model=Dict[str, str])
def delete_professor(request: Request):
	data =  request.json()
	professor_id = data.get("professor_id")
	
	if professor_id:
		result =  collection.delete_one({"_id": professor_id})
		if result.deleted_count == 1:
			return {"message": "Professor deleted successfully"}
	raise HTTPException(status_code=404, detail="Professor not found")



########################### RATING CRUD ####################################


# Add Professor Rating
@app.post("/professors/add_rating", response_model=Dict[str, Any])
def create_professor_rating(request: Request):
	data =  request.json()
	professor_id = data["_id"]
	rating = data["rating"]
	
	if professor_id and rating:
		professor_object_id = ObjectId(professor_id)
		rating["_id"] = ObjectId()
		try:
			result = collection.update_one(
				{"_id": professor_object_id},
				{"$push": {"userRatings": rating}}
			)
		except Exception as e:
			raise HTTPException(status_code=500, detail="Failed to update professor ratings")

		if result.modified_count == 1:
			updated_professor = collection.find_one({"_id": professor_object_id})
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
def get_professor_ratings(request: Request):
	data =  request.json()
	professor_id = data["_id"]
	print(collection.find_one({"_id": ObjectId(professor_id)}))
	if professor_id:
		professor = collection.find_one({"_id": ObjectId(professor_id)})
		if professor and "userRatings" in professor:
			for i in range(len(professor["userRatings"])):
				professor["userRatings"][i]["_id"] = str(professor["userRatings"][i]["_id"])
			return professor["userRatings"]
		
	raise HTTPException(status_code=404, detail="Professor not found or no ratings available")

# Update Professor Rating
@app.post("/professors/update_rating", response_model=List[Dict[str, Any]])
def update_professor_rating(request: Request):
	data =  request.json()
	professor_id = ObjectId(data["_id"])
	rating_id = ObjectId(data["rating"]["_id"])
	updated_rating = data["rating"]
	
	if professor_id and rating_id and updated_rating:
		professor = collection.find_one({"_id": professor_id})
		if professor and "userRatings" in professor:
			updated_ratings = professor["userRatings"]
			count = 0
			l = len(updated_ratings)
			for i in range(l):
				if ObjectId(updated_ratings[i]["_id"]) == rating_id:
					for key, value in updated_rating.items():
						if key in updated_ratings[i] and key != "_id":
							updated_ratings[i][key] = value
					break
				count+=1
				if count >= l:
					raise HTTPException(status_code=404, detail="Professor rating not found")
							
			result = collection.find_one_and_update(
				{"_id": professor_id},
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
def delete_professor_rating(request: Request):
	data =  request.json()
	professor_id = ObjectId(data["_id"])
	rating_id = ObjectId(data["rating"]["_id"])
	if professor_id and rating_id:
		result = collection.update_one(
			{"_id": ObjectId(professor_id)},
			{"$pull": {"userRatings": {"_id": str(rating_id)}}}
		)
		if result.modified_count == 1:
			return {"message": "Professor rating deleted successfully"}
	raise HTTPException(status_code=404, detail="Professor rating not found")