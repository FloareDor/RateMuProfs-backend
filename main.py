from fastapi import FastAPI
from routes.routes import professor_router, limiter
from fastapi.middleware.cors import CORSMiddleware
from os import environ as env
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from utils.scripts import insertSampleData, dropDB


app = FastAPI()

# Include the professor router
app.include_router(professor_router, prefix="")

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

if __name__ == "__main__":

    dropDB()
    insertSampleData("prof_data.json")
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)