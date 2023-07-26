from fastapi import FastAPI, HTTPException
from typing import Dict, Any, List
from pymongo import MongoClient
from bson import ObjectId

# MongoDB connection
client = MongoClient("mongodb://localhost:27017")
db = client["rate_my_professor"]
collection = db["professors"]
collection.delete_many({})

# Document to be inserted
document = {
	"name": "Bhanukiran Perabathini",
	"rating": 4,
	"lod": 4,
	"courses": ["Discrete Mathematics", "Optimization techniques of AI", "Introduction to C"],
	"dept": "Department of Computer Science and Engineering",
	"school": "ECSoE",
	"totRatings": 1,
	"courseQuality": 3,
	"helpfulness": 4,
	"responsiveness": 5,
	"userRatings": [
		{
			"_id": str(ObjectId()),
			"courseQuality": 4,
			"responsiveness": 5,
			"lod": 4,
			"course": "Computer Organization",
			"date": {"$date": 1685267893303},
			"helpfulness": 3,
			"feedback": "good prof",
		},
	],
}

# Insert the document into the collection
insert_result = collection.insert_one(document)

# Check if the insertion was successful
if insert_result.acknowledged:
	print("Document inserted successfully!")
	for doc in collection.find():
		# Convert the ObjectId to string representation before printing
		doc["_id"] = str(doc["_id"])
		print(doc)
else:
	print("Failed to insert the document.")


app = FastAPI()

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


# Read Professor
@app.get("/professors/{professor_id}", response_model=Dict[str, Any])
async def get_professor(professor_id: str):
	professor = await collection.find_one({"_id": professor_id})
	if professor:
		return professor
	else:
		raise HTTPException(status_code=404, detail="Professor not found")

# Update Professor
@app.put("/professors/{professor_id}", response_model=Dict[str, Any])
async def update_professor(professor_id: str, updated_professor: Dict[str, Any]):
	result = await collection.update_one(
		{"_id": professor_id},
		{"$set": updated_professor}
	)
	
	if result.modified_count == 1:
		updated_professor["_id"] = professor_id
		return updated_professor
	else:
		raise HTTPException(status_code=404, detail="Professor not found")

# Delete Professor
@app.delete("/professors/{professor_id}", response_model=Dict[str, str])
async def delete_professor(professor_id: str):
	result = await collection.delete_one({"_id": professor_id})
	if result.deleted_count == 1:
		return {"message": "Professor deleted successfully"}
	else:
		raise HTTPException(status_code=404, detail="Professor not found")



########################### RATING CRUD ####################################

from bson import ObjectId

# Create Professor Rating
@app.post("/professors/{professor_id}/ratings/", response_model=Dict[str, Any])
async def create_professor_rating(professor_id: str, rating: Dict[str, Any]):
    professor_object_id = ObjectId(professor_id)
    rating["_id"] = str(ObjectId())
    try:
        result = collection.update_one(
            {"_id": professor_object_id},
            {"$push": {"userRatings": rating}}
        )
        print(result)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to update professor ratings")

    if result.modified_count == 1:
        # Since we did not provide an _id for the rating, MongoDB will create it automatically.
        # We can return the updated professor document to see the assigned _id.
        updated_professor = collection.find_one({"_id": professor_object_id})
        if updated_professor:
            # Convert ObjectId to string before returning the response
            updated_professor["_id"] = str(updated_professor["_id"])
            return updated_professor
        else:
            raise HTTPException(status_code=404, detail="Professor not found")
    else:
        raise HTTPException(status_code=404, detail="Professor not found")




# Read Professor Ratings
@app.get("/professors/{professor_id}/ratings/", response_model=List[Dict[str, Any]])
async def get_professor_ratings(professor_id: str):
	professor = collection.find_one({"_id": ObjectId(professor_id)}, {"userRatings": 1})
	if professor and "userRatings" in professor:
		return professor["userRatings"]
	else:
		raise HTTPException(status_code=404, detail="Professor not found or no ratings available")

# Update Professor Rating
@app.put("/professors/{professor_id}/ratings/{rating_id}/", response_model=Dict[str, Any])
async def update_professor_rating(professor_id: str, rating_id: str, updated_rating: Dict[str, Any]):
	result = collection.update_one(
		{"_id": ObjectId(professor_id), "userRatings._id": rating_id},
		{"$set": {"userRatings.$": updated_rating}}
	)
	if result.modified_count == 1:
		return updated_rating
	else:
		raise HTTPException(status_code=404, detail="Professor rating not found")

# Delete Professor Rating
@app.delete("/professors/{professor_id}/ratings/{rating_id}/", response_model=Dict[str, str])
async def delete_professor_rating(professor_id: str, rating_id: str):
	result = await collection.update_one(
		{"_id": ObjectId(professor_id)},
		{"$pull": {"userRatings": {"_id": rating_id}}}
	)
	if result.modified_count == 1:
		return {"message": "Professor rating deleted successfully"}
	else:
		raise HTTPException(status_code=404, detail="Professor rating not found")
