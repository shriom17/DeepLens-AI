from fastapi import FastAPI

from backend.routes.auth import router as auth_router


app = FastAPI(
    title="NoticeSense AI API",
    description="Backend API for NoticeSense AI",
    version="1.0.0"
)


app.include_router(auth_router)


@app.get("/")
def home():

    return {
        "message": "NoticeSense AI Backend is running!"
    }