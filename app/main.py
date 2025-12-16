from fastapi import FastAPI
from app.config import settings
from app.routes import analysis

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="1.0.0"
)

# Include routers
app.include_router(analysis.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Daylytics Backend"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
