from fastapi import FastAPI
from routes.routes import router, limiter
from fastapi.middleware.cors import CORSMiddleware
from os import environ as env
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


app = FastAPI()

# Include the professor router
app.include_router(router, prefix="")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = ["*"]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
	expose_headers=["Authorization"],
)

# ATLAS_URL = env.get("ATLAS_URL")
# localDb = 'mongodb://localhost:27017/?maxPoolSize=100'
# # MongoDB professor connection
# client = MongoClient(ATLAS_URL)
# db = client["rate_my_professor"]

if __name__ == "__main__":
	import uvicorn

	# ssl_cert_path = '/etc/letsencrypt/live/ratemuprofs.live/fullchain.pem'
	# ssl_key_path = '/etc/letsencrypt/live/ratemuprofs.live/privkey.pem'
	# uvicorn.run(app, host="0.0.0.0", port=8000, ssl_certfile=ssl_cert_path, ssl_keyfile=ssl_key_path)
	uvicorn.run(app, host="localhost", port=8000)