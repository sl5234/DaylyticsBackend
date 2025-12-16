from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="1.0.0"
)


@app.get("/")
def read_root():
    return {"message": "Welcome to Daylytics Backend"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}

