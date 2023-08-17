from fastapi import FastAPI, HTTPException, Request
from typing import Dict, Any, List
from pymongo import MongoClient
from bson import ObjectId
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json

with open("prof_data.json", "r") as json_file:
    data = json.load(json_file)

# MongoDB connection
client = MongoClient("mongodb://localhost:27017")
db = client["rate_my_professor"]
collection = db["professors"]
collection.delete_many({})

# # Document to be inserted
# document = {
# 	"name": "Bhanukiran Perabathini",
# 	"rating": 4,
# 	"lod": 4,
# 	"courses": ["Discrete Mathematics", "Optimization techniques of AI", "Introduction to C"],
# 	"dept": "Department of Computer Science and Engineering",
# 	"school": "ECSoE",
# 	"totRatings": 1,
# 	"courseQuality": 3,
# 	"helpfulness": 4,
# 	"responsiveness": 5,
# 	"userRatings": [
# 		{
# 			"_id": str(ObjectId()),
# 			"courseQuality": 4,
# 			"responsiveness": 5,
# 			"lod": 4,
# 			"course": "Computer Organization",
# 			"date": {"$date": 1685267893303},
# 			"helpfulness": 3,
# 			"feedback": "good prof",
# 		},
# 	],
# }

for prof in data:
	# Insert the document into the collection
	insert_result = collection.insert_one(prof)

	# Check if the insertion was successful
	if insert_result.acknowledged:
		print("Document inserted successfully!")
		for doc in collection.find():
			# Convert the ObjectId to string representation before printing
			doc["_id"] = str(doc["_id"])
			# print(doc)
	else:
		print("Failed to insert the document.")


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
    return {"message": "Hello World"}

########################### PROFESSOR CRUD ####################################

# get all profs
@app.get("/professors/", response_model=List[Dict[str, Any]])
async def get_all_professors():
	professors = []
	for professor in collection.find():
		# Convert the ObjectId to string representation before returning
		professor["_id"] = str(professor["_id"])
		professors.append(professor)
	if professors:
		return professors
	else:
		raise HTTPException(status_code=404, detail="No professors found")
	
	
@app.get("/professors/by_school/{school}", response_model=List[Dict[str, Any]])
async def get_professors_by_school(school: str):
    professors = []
    for professor in collection.find({"school": re.compile(school, re.IGNORECASE)}):
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
async def update_professor(request: Request):
	data = await request.json()
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
async def delete_professor(request: Request):
	data = await request.json()
	professor_id = data.get("professor_id")
	
	if professor_id:
		result = await collection.delete_one({"_id": professor_id})
		if result.deleted_count == 1:
			return {"message": "Professor deleted successfully"}
	raise HTTPException(status_code=404, detail="Professor not found")



########################### RATING CRUD ####################################


# Add Professor Rating
@app.post("/professors/add_rating", response_model=Dict[str, Any])
async def create_professor_rating(request: Request):
	data = await request.json()
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


# Read Professor Ratings
@app.post("/professors/get_ratings", response_model=List[Dict[str, Any]])
async def get_professor_ratings(request: Request):
	data = await request.json()
	professor_id = data["_id"]
	
	if professor_id:
		professor = collection.find_one({"_id": ObjectId(professor_id)})

		if professor and "userRatings" in professor:
			for i in range(len(professor["userRatings"])):
				professor["userRatings"][i]["_id"] = str(professor["userRatings"][i]["_id"])
			return professor["userRatings"]
	raise HTTPException(status_code=404, detail="Professor not found or no ratings available")

# Update Professor Rating
@app.post("/professors/update_rating", response_model=Dict[str, Any])
async def update_professor_rating(request: Request):
	data = await request.json()
	professor_id = ObjectId(data["professor_id"])
	rating_id = data["rating"]["_id"]
	updated_rating = data["rating"]
	
	if professor_id and rating_id and updated_rating:
		result = collection.update_one(
			{"_id": professor_id, "userRatings._id": rating_id},
			{"$set": {"userRatings.$": updated_rating}}
		)
		if result.modified_count == 1:
			professor = collection.find_one({"_id": professor_id})
			if professor and "userRatings" in professor:
				for i in range(len(professor["userRatings"])):
					professor["userRatings"][i]["_id"] = str(professor["userRatings"][i]["_id"])
				return professor["userRatings"]
			# return updated_rating
	raise HTTPException(status_code=404, detail="Professor rating not found")


# Delete Professor Rating
@app.post("/professors/delete_rating", response_model=Dict[str, str])
async def delete_professor_rating(request: Request):
	data = await request.json()
	professor_id = data.get("professor_id")
	rating_id = data.get("rating_id")
	
	if professor_id and rating_id:
		result = await collection.update_one(
			{"_id": ObjectId(professor_id)},
			{"$pull": {"userRatings": {"_id": rating_id}}}
		)
		if result.modified_count == 1:
			return {"message": "Professor rating deleted successfully"}
	raise HTTPException(status_code=404, detail="Professor rating not found")