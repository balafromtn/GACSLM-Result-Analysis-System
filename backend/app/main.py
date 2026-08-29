from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine
from app.models import academic
from app.api import routes_upload
from app.api import routes_analytics # <-- ADD THIS IMPORT

academic.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_upload.router, prefix=settings.API_V1_STR, tags=["Upload"])
# <-- ADD THIS ROUTER REGISTRATION -->
app.include_router(routes_analytics.router, prefix=settings.API_V1_STR, tags=["Analytics"])

@app.get("/")
def health_check():
    return {"status": "online"}