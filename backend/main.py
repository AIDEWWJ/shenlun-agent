from app.api import api_router
from app.core.config import settings
from app.db.init_db import init_database
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="申论 Agent API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")


@app.on_event("startup")
def startup_event():
    init_database()


@app.get("/")
def root():
    return {"message": "申论 Agent API is running"}
