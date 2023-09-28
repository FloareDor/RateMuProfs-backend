
from pymongo import MongoClient
import json
from bson import ObjectId

client = MongoClient('mongodb://localhost:27017/?maxPoolSize=100')
db = client["rate_my_professor"]
professor_collection = db["professors"]
professor_collection.delete_many({})

def insertSampleData(filename):
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

def dropDB():
	professor_collection = db["professors"]
	professor_collection.delete_many({})

	# User collection
	user_collection = db["users"]
	user_collection.delete_many({})

	# Ratings collection
	rating_collection = db["ratings"]
	rating_collection.delete_many({})

	return "success"

