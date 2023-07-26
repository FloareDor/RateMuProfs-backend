from pymongo import MongoClient
from bson import ObjectId

# Create a connection to MongoDB
client = MongoClient("mongodb://localhost:27017")

# Access the database and collection
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
			"courseQuality": 4,
			"responsiveness": 5,
			"lod": 4,
			"course": "Computer Organization",
			"date": {"$date": 1685267893303},
			"helpfulness": 3,
			"feedback": "good prof",
			"_id": ObjectId("647325b57231c23c45077152"),
		},
	],
}

# Insert the document into the collection
insert_result = collection.insert_one(document)

# Check if the insertion was successful
if insert_result.acknowledged:
	print("Document inserted successfully!")
	for doc in collection.find():
		print(doc)

else:
	print("Failed to insert the document.")
